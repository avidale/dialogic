import math
import textdistance

from collections import Counter, Callable, defaultdict, Iterable, Mapping
from itertools import chain

from ..nlu import basic_nlu


try:
    from pyemd import emd
    IMPORTED_EMD = True
except ImportError:
    emd = None
    IMPORTED_EMD = False

try:
    import numpy as np
    IMPORTED_NUMPY = True
except ImportError:
    np = None
    IMPORTED_NUMPY = False


class BaseMatcher:
    """ A base class for text classification with confidence """
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def fit(self, texts, labels):
        raise NotImplementedError()

    def match(self, text, use_threshold=True):
        scores, labels = self.get_scores(text)
        best_score = 0.0
        winner_label = None
        for score, label in zip(scores, labels):
            if (score >= self.threshold or not use_threshold) and score > best_score:
                best_score = score
                winner_label = label
        return winner_label, best_score

    def get_scores(self, text):
        raise NotImplementedError()


class WeightedAverageMatcher(BaseMatcher):
    def __init__(self, matchers, weights=None, **kwargs):
        super(WeightedAverageMatcher, self).__init__(**kwargs)
        assert len(matchers) > 0, 'list of matchers should be non-empty'
        self.matchers = matchers
        if weights is None:
            weights = [1.0 for m in self.matchers]
        else:
            assert len(weights) == len(matchers), 'matchers and weights should have the same size'
        total_weight = float(sum(weights))
        self.weights = [w / total_weight for w in weights]

    def fit(self, texts, labels):
        for m in self.matchers:
            m.fit(texts, labels)

    def get_scores(self, text):
        label2matchers2scores = defaultdict(lambda: defaultdict(lambda: 0))
        for i, m in enumerate(self.matchers):
            scores, labels = m.get_scores(text)
            for l, s in zip(labels, scores):
                if s > label2matchers2scores[l][i]:
                    label2matchers2scores[l][i] = s
        labels = []
        scores = []
        for l, ldict in label2matchers2scores.items():
            labels.append(l)
            scores.append(sum(w * ldict[i] for i, w in enumerate(self.weights)))
        return scores, labels


class ModelBasedMatcher(BaseMatcher):
    """ Classify text using an old good sklearn-style model """
    def __init__(self, model, **kwargs):
        super(ModelBasedMatcher, self).__init__(**kwargs)
        self.model = model

    def fit(self, texts, labels):
        self.model.fit(texts, labels)

    def get_scores(self, text):
        scores = self.model.predict_proba([text])[0]
        labels = self.model.classes_
        return scores, labels


class PairwiseMatcher(BaseMatcher):
    """
    Classify text using 1-nearest neighbor by some similarity metric.
    This is an abstract class; its descendants should implement the specific metric to compare preprocessed texts.

    Parameters
    ----------
    text_normalization: string or callable
        Describes how to preprocess the texts before matching.
        Supported string values: 'fast' to lowercase and remove unusual characters; 'fast_lemmatize' to additionally
        lemmatize words (russian only). Callable values should accept and return strings.
    stopwords: iterable or mapping
        Lists the words that should be discarded (if it is a list) or paid less attention
        (if it is a dict with values in (0, 1) during matching. It may not be supported by all descendant matchers.
    kwargs: dict
        Passed to the parent constructor (BaseMatcher)
    """
    def __init__(self, text_normalization='fast', stopwords=None, **kwargs):
        super(PairwiseMatcher, self).__init__(**kwargs)
        self.text_normalization = text_normalization
        self._texts = []
        self._labels = []

        if stopwords is None:
            stopwords = {}
        if isinstance(stopwords, Iterable) and not isinstance(stopwords, Mapping):
            stopwords = {w: 0 for w in stopwords}
        # todo: delay stopwords preprocessing until the descendant class has been initialized
        stopwords = {PairwiseMatcher.preprocess(self, k): v for k, v in stopwords.items()}
        self.stopwords = stopwords

    def preprocess(self, text):
        if self.text_normalization == 'fast':
            text = basic_nlu.fast_normalize(text, lemmatize=False)
        if self.text_normalization == 'fast_lemmatize':
            text = basic_nlu.fast_normalize(text, lemmatize=True)
        elif isinstance(self.text_normalization, Callable):
            text = self.text_normalization(text)
        return text

    def compare(self, one, another):
        raise NotImplementedError()

    def fit(self, texts, labels):
        self._texts = [self.preprocess(text) for text in texts]
        self._labels = labels
        return self

    def get_scores(self, text):
        processed = self.preprocess(text)
        return [self.compare(processed, t) for t in self._texts], self._labels


class ExactMatcher(PairwiseMatcher):
    def compare(self, one, another):
        return float(one == another)


class TextDistanceMatcher(PairwiseMatcher):
    def __init__(self, by_words=True, metric='cosine', **kwargs):
        super(TextDistanceMatcher, self).__init__(**kwargs)
        self.by_words = by_words
        self.metric = metric
        self.fun = getattr(textdistance, metric).normalized_similarity

    def preprocess(self, text):
        text = super(TextDistanceMatcher, self).preprocess(text)
        if self.by_words:
            return text.split()
        return text

    def compare(self, one, another):
        return self.fun(one, another)


class LevenshteinMatcher(TextDistanceMatcher):
    def __init__(self, **kwargs):
        kwargs['by_words'] = False
        kwargs['metric'] = 'levenshtein'
        super(LevenshteinMatcher, self).__init__(**kwargs)


class JaccardMatcher(PairwiseMatcher):
    def preprocess(self, text):
        text = super(JaccardMatcher, self).preprocess(text)
        return set(text.split())

    def compare(self, one, another):
        intersection = len(one.intersection(another))
        union = len(one.union(another))
        if intersection:
            return intersection / union
        return 0.0


class TFIDFMatcher(PairwiseMatcher):
    def __init__(self, smooth=2.0, ngram=1, **kwargs):
        super(TFIDFMatcher, self).__init__(**kwargs)
        self.smooth = smooth
        self.ngram = ngram
        self.vocab = Counter()

    def fit(self, texts, labels):
        self.vocab = Counter(w for t in texts for w in self._tokenize(t))
        return super(TFIDFMatcher, self).fit(texts, labels)

    def preprocess(self, text):
        text = super(TFIDFMatcher, self).preprocess(text)
        tf = Counter(self._tokenize(text))
        return {
            w: tf / math.log(self.smooth + self.vocab[w]) * self.stopwords.get(w, 1)
            for w, tf in tf.items()
        }

    def compare(self, one, another):
        dot = self._dot(one, another)
        if dot < 1e-6:
            return 0.0
        return dot / math.sqrt(self._norm(one) * self._norm(another))

    def _tokenize(self, text):
        words = text.split()
        if self.ngram == 1:
            return words
        words = ['BOS'] + words + ['EOS']
        return words + ['_'.join(words[i:(i + self.ngram)]) for i in range(len(words) - self.ngram + 1)]

    def _dot(self, one, another):
        return sum(v * another.get(k, 0) for k, v in one.items())

    def _norm(self, one):
        return self._dot(one, one)


class W2VMatcher(PairwiseMatcher):
    """ Compare texts by cosine similarity of their mean word vectors """
    def __init__(self, w2v, normalize_word_vec=True, **kwargs):
        super(W2VMatcher, self).__init__(**kwargs)
        self.w2v = w2v
        self.normalize_word_vec = normalize_word_vec

    def vec_from_word(self, word):
        vec = self.w2v[word]
        if self.normalize_word_vec:
            vec = vec / sum(vec**2)**0.5
        return vec

    def preprocess(self, text):
        text = super(W2VMatcher, self).preprocess(text)
        tokens = text.split()
        vecs = [self.vec_from_word(t) for t in tokens if t in self.w2v]
        if len(vecs) == 0:
            return None
        result = sum(vecs)
        result = result / sum(result**2)**0.5
        return result

    def compare(self, one, another):
        if one is None or another is None:
            return 0
        return sum(one * another)


class WMDDocument:
    def __init__(self, text, tokens, vecs, weights):
        self.text = text
        self.tokens = tokens
        self.vecs = vecs
        self.weights = weights


class WMDMatcher(PairwiseMatcher):
    """
    Compare texts by Word Mover Distance between them .

    When using this code, please consider citing the following papers:
        .. Ofir Pele and Michael Werman, "A linear time histogram metric for improved SIFT matching".
        .. Ofir Pele and Michael Werman, "Fast and robust earth mover's distances".
        .. Matt Kusner et al. "From Word Embeddings To Document Distances".
    """

    def __init__(self, w2v, normalize_word_vec=True, **kwargs):
        if not IMPORTED_NUMPY:
            raise ImportError('When using WMDMatcher, numpy should be installed')
        if not IMPORTED_EMD:
            raise ImportError('When using WMDMatcher, pyemd should be installed')
        super(WMDMatcher, self).__init__(**kwargs)
        self.w2v = w2v
        self.normalize_word_vec = normalize_word_vec

    def vec_from_word(self, word):
        vec = self.w2v[word]
        if self.normalize_word_vec:
            vec = vec / sum(vec ** 2) ** 0.5
        return vec

    def preprocess(self, text):
        preprocessed_text = super(WMDMatcher, self).preprocess(text)
        tokens = preprocessed_text.split()
        valid_tokens = [t for t in tokens if t in self.w2v]
        if len(valid_tokens) == 0:
            return None
        vecs = [self.vec_from_word(t) for t in valid_tokens]
        weights = []
        return WMDDocument(text, valid_tokens, vecs, weights)

    def text2bow(self, tokens, word2idx):
        bow = np.zeros(len(word2idx), dtype=np.double)
        n = len(tokens)
        for t in tokens:
            bow[word2idx[t]] += 1.0 / n
        return bow

    def compare(self, one, another):
        if one is None or another is None:
            return 0

        vocab = sorted(set(one.tokens).union(set(another.tokens)))
        word2idx = {word: i for i, word in enumerate(vocab)}
        word2vec = {}
        for w, v in chain(zip(one.tokens, one.vecs), zip(another.tokens, another.vecs)):
            if w not in word2vec:
                word2vec[w] = v

        distance_matrix = np.zeros((len(vocab), len(vocab)), dtype=np.double)
        for i, t1 in enumerate(vocab):
            for j, t2 in enumerate(vocab):
                if t1 not in one.tokens or t2 not in another.tokens:
                    continue
                # Compute Euclidean distance between word vectors.
                distance_matrix[i, j] = np.sqrt(np.sum((word2vec[t1] - word2vec[t2]) ** 2))

        d1 = self.text2bow(one.tokens, word2idx)
        d2 = self.text2bow(another.tokens, word2idx)

        wmd = emd(d1, d2, distance_matrix)
        # because we use unit vectors, this transformation mimics cosine distance
        similarity = 1 - wmd ** 2 / 2
        return similarity


_matchers = dict()


def register_matcher(name, matcher_maker):
    _matchers[name] = matcher_maker


def make_matcher(key, **kwargs):
    return _matchers[key](**kwargs)


register_matcher('exact', lambda **kwargs: ExactMatcher(**kwargs))
register_matcher('levenshtein', lambda **kwargs: TextDistanceMatcher(by_words=False, metric='levenshtein', **kwargs))
register_matcher('cosine', lambda **kwargs: TextDistanceMatcher(by_words=True, metric='cosine', **kwargs))
register_matcher('tf-id', lambda **kwargs: TFIDFMatcher(**kwargs))
register_matcher('simple_text', lambda weights=(0.5, 0.5), **kwargs: WeightedAverageMatcher([
    TextDistanceMatcher(by_words=False, metric='levenshtein'),
    TextDistanceMatcher(by_words=True, metric='cosine'),
], weights=weights, **kwargs))
