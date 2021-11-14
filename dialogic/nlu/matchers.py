import math
import textdistance
import re
import typing

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping
from itertools import chain
from types import ModuleType

from ..nlu import basic_nlu

from .regex_utils import regex

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


EPSILON = 1e-10


class TextNormalization:
    FAST = 'fast'
    FAST_LEMMATIZE = 'fast_lemmatize'


class BaseMatcher:
    """ A base class for text classification with confidence """
    def __init__(self, threshold: float = 0.5, thresholds=None):
        """ Create a base matcher
        parameters:
        - threshold: the minimal allowed similarity between the text and the example for a successful match
        - thresholds: an optional dict of label-wise thresholds
        """
        self.threshold: float = threshold
        self.thresholds: dict = thresholds or {}

    def fit(self, texts, labels):
        raise NotImplementedError()

    def fit_dict(self, label2texts):
        x = []
        y = []
        for label, texts in label2texts.items():
            if isinstance(texts, str):
                texts = [texts]
            for text in texts:
                x.append(text)
                y.append(label)
        return self.fit(x, y)

    def get_threshold(self, label):
        return self.thresholds.get(label, self.threshold)

    def match(self, text: str, use_threshold=True):
        """ Return the label which is most similar to the text and its score.
        If no example is similar enough, the winner label will be None.
        """
        scores, labels = self.get_scores(text)
        best_score = -math.inf
        winner_label = None
        for score, label in zip(scores, labels):
            if (score >= self.get_threshold(label) or not use_threshold) and score > best_score:
                best_score = score
                winner_label = label
        return winner_label, best_score

    def get_scores(self, text: str) -> typing.Tuple[typing.List[float], typing.List]:
        """ Return the list of matching scores and their corresponding labels """
        raise NotImplementedError()

    def aggregate_scores(self, text: str, use_threshold=True) -> Counter:
        """ Return a dict with the highest matching score for each label. """
        result = Counter()
        scores, labels = self.get_scores(text)
        for score, label in zip(scores, labels):
            if score >= self.get_threshold(label) or not use_threshold:
                result[label] = max(score, result.get(label, -math.inf))
        return result


class ExtendableMatcher(BaseMatcher):
    """ Mixin for matchers that support partial_fit """
    def fit(self, texts, labels):
        self.reset()
        self.partial_fit(texts, labels)
        return self

    def reset(self):
        raise NotImplementedError()

    def partial_fit(self, texts, labels):
        raise NotImplementedError()

    def partial_fit_dict(self, label2texts):
        x = []
        y = []
        for label, texts in label2texts.items():
            if isinstance(texts, str):
                texts = [texts]
            for text in texts:
                x.append(text)
                y.append(label)
        return self.partial_fit(x, y)


class AggregationMatcher(BaseMatcher):
    def __init__(self, matchers, **kwargs):
        super(AggregationMatcher, self).__init__(**kwargs)
        assert len(matchers) > 0, 'list of matchers should be non-empty'
        self.matchers = matchers

    def fit(self, texts, labels):
        for m in self.matchers:
            m.fit(texts, labels)

    def get_scores(self, text: str) -> typing.Tuple[typing.List[float], typing.List]:
        scores = []
        labels = []
        for m in self.matchers:
            sc, lbl = m.get_scores(text)
            scores.extend(sc)
            labels.extend(lbl)
        return scores, labels

    def _apply_matchers(self, text, use_threshold=False):
        label2matchers2scores = defaultdict(lambda: defaultdict(lambda: -math.inf))
        for i, m in enumerate(self.matchers):
            scores, labels = m.get_scores(text)
            for label, score in zip(labels, scores):
                if score > label2matchers2scores[label][i]:
                    if use_threshold and score < self.get_threshold(label):
                        continue
                    label2matchers2scores[label][i] = score
        return label2matchers2scores


class MaxMatcher(AggregationMatcher):
    def get_scores(self, text):
        label2matchers2scores = self._apply_matchers(text)
        labels = []
        scores = []
        for label, ldict in label2matchers2scores.items():
            if not ldict:
                continue
            labels.append(label)
            scores.append(max(ldict.values()))
        return scores, labels


class WeightedAverageMatcher(AggregationMatcher):
    def __init__(self, matchers, weights=None, **kwargs):
        super(WeightedAverageMatcher, self).__init__(matchers, **kwargs)
        if weights is None:
            weights = [1.0] * len(self.matchers)
        else:
            assert len(weights) == len(matchers), 'matchers and weights should have the same size'
        total_weight = float(sum(weights))
        self.weights = [w / total_weight for w in weights]

    def get_scores(self, text):
        label2matchers2scores = self._apply_matchers(text)
        labels = []
        scores = []
        for label, ldict in label2matchers2scores.items():
            score = sum(w * ldict[i] for i, w in enumerate(self.weights))
            labels.append(label)
            scores.append(score)
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


class RegexMatcher(BaseMatcher):
    """ This matcher returns matching score 1,
    if the text matches one of the provided expressions for the label, and 0 otherwise.
    The parameter `add_end` forcibly wraps each expression between `^` and `$` symbols, disabling partial prefix match.
    """
    def __init__(self, *args, add_end=True, merge=True, engine='re', **kwargs):
        super(RegexMatcher, self).__init__(*args, **kwargs)
        self.add_end = add_end
        self.merge = merge
        self.expressions = []
        self.labels = []
        self.engine = engine

    @property
    def re(self):
        if self.engine == 'regex' and regex is not None:
            return regex
        elif isinstance(self.engine, ModuleType):
            return self.engine
        return re

    def fit(self, texts, labels):
        parts = defaultdict(list)
        for text, label in zip(texts, labels):
            parts[label].append(text)
        for label, expressions in parts.items():
            if self.merge:
                self.expressions.append(
                    self.re.compile('(?:{})'.format(
                        '|'.join([self._wrap(e) for e in expressions])
                    ))
                )
                self.labels.append(label)
            else:
                for e in expressions:
                    self.expressions.append(self.re.compile('(?:{})'.format(self._wrap(e))))
                    self.labels.append(label)

    def _wrap(self, text):
        if self.add_end:
            return '^{}$'.format(text)
        return text

    def get_scores(self, text):
        scores = []
        labels = []
        for label, expression in zip(self.labels, self.expressions):
            labels.append(label)
            scores.append(float(bool(self.re.match(expression, text))))
        return scores, labels


class PairwiseMatcher(ExtendableMatcher):
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
    kwargs:
        Passed to the parent constructor (BaseMatcher)
    """
    def __init__(self, text_normalization=TextNormalization.FAST, stopwords=None, **kwargs):
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
        if self.text_normalization == TextNormalization.FAST:
            text = basic_nlu.fast_normalize(text, lemmatize=False)
        if self.text_normalization == TextNormalization.FAST_LEMMATIZE:
            text = basic_nlu.fast_normalize(text, lemmatize=True)
        elif isinstance(self.text_normalization, Callable):
            text = self.text_normalization(text)
        return text

    def compare(self, one, another):
        raise NotImplementedError()

    def partial_fit(self, texts, labels):
        self._texts.extend([self.preprocess(text) for text in texts])
        self._labels.extend(labels)
        return self

    def reset(self):
        self._texts = []
        self._labels = []
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
        self.vocab = Counter(w for t in texts for w in self._tokenize(super(TFIDFMatcher, self).preprocess(t)))
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
        if abs(dot) < 1e-6:
            return 0.0
        return dot / math.sqrt(self._norm(one) * self._norm(another))

    def _tokenize(self, text):
        words = text.split()
        if self.ngram == 1:
            return words
        words = ['BOS'] + words + ['EOS']
        return words + ['_'.join(words[i:(i + self.ngram)]) for i in range(len(words) - self.ngram + 1)]

    @staticmethod
    def _dot(one, another):
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
            vec = vec / max(sum(vec**2), EPSILON) ** 0.5
        return vec

    def preprocess(self, text):
        text = super(W2VMatcher, self).preprocess(text)
        tokens = text.split()
        vecs = [self.vec_from_word(t) for t in tokens if t in self.w2v]
        if len(vecs) == 0:
            return None
        result = sum(vecs)
        result = result / max(sum(result**2), EPSILON) ** 0.5
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
            vec = vec / max(sum(vec ** 2), EPSILON) ** 0.5
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

    @staticmethod
    def text2bow(tokens, word2idx):
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


def make_matcher_with_regex(base_matcher: BaseMatcher, intents, merge=True, re_matcher: RegexMatcher = None):
    """ Create a mix of the given matcher and a regex matcher """
    labels = []
    texts = []
    re_labels = []
    re_texts = []
    for intent_name, intent in intents.items():
        if 'regexp' in intent:
            exps = intent['regexp']
            if not isinstance(exps, list):
                exps = [exps]
            for exp in exps:
                re_labels.append(intent_name)
                re_texts.append(exp)
        if 'examples' in intent:
            for ex in intent['examples']:
                labels.append(intent_name)
                texts.append(ex)
    base_matcher.fit(texts, labels)
    if re_matcher is None:
        re_matcher = RegexMatcher(merge=merge)
    re_matcher.fit(re_texts, re_labels)
    return MaxMatcher([base_matcher, re_matcher])


_matchers = dict()


def register_matcher(name, matcher_maker):
    _matchers[name] = matcher_maker


def make_matcher(key, **kwargs):
    return _matchers[key](**kwargs)


register_matcher('exact', lambda **kwargs: ExactMatcher(**kwargs))
register_matcher('levenshtein', lambda **kwargs: TextDistanceMatcher(by_words=False, metric='levenshtein', **kwargs))
register_matcher('cosine', lambda **kwargs: TextDistanceMatcher(by_words=True, metric='cosine', **kwargs))
register_matcher('tf-idf', lambda **kwargs: TFIDFMatcher(**kwargs))
register_matcher('simple_text', lambda weights=(0.5, 0.5), **kwargs: WeightedAverageMatcher([
    TextDistanceMatcher(by_words=False, metric='levenshtein'),
    TextDistanceMatcher(by_words=True, metric='cosine'),
], weights=weights, **kwargs))
