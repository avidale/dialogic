import math
import textdistance

from collections import Counter

from ..nlu import basic_nlu


class BaseMatcher:
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def fit(self, texts, labels):
        raise NotImplementedError()

    def match(self, text):
        scores, labels = self.get_scores(text)
        best_score = 0.0
        winner_label = None
        for score, label in zip(scores, labels):
            if score >= self.threshold and score > best_score:
                best_score = score
                winner_label = label
        return winner_label, best_score

    def get_scores(self, text):
        raise NotImplementedError()


class PairwiseMatcher(BaseMatcher):
    def __init__(self, *args, text_normalization='fast', **kwargs):
        super(PairwiseMatcher, self).__init__(*args, **kwargs)
        self.text_normalization = text_normalization
        self._texts = []
        self._labels = []

    def preprocess(self, text):
        if self.text_normalization == 'fast':
            text = basic_nlu.fast_normalize(text)
        return text

    def compare(self, one, another):
        raise NotImplementedError()

    def fit(self, texts, labels):
        self._texts = [self.preprocess(text) for text in texts]
        self._labels = labels

    def get_scores(self, text):
        processed = self.preprocess(text)
        return [self.compare(processed, t) for t in self._texts], self._labels


class ExactMatcher(PairwiseMatcher):
    def compare(self, one, another):
        return float(one == another)


class TextDistanceMatcher(PairwiseMatcher):
    def __init__(self, *args, by_words=True, metric='cosine', **kwargs):
        super(TextDistanceMatcher, self).__init__(*args, **kwargs)
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


class JaccardMatcher(PairwiseMatcher):
    def preprocess(self, text):
        text = super(JaccardMatcher, self).preprocess(text)
        return set(text.split())

    def compare(self, one, another):
        intersection = len(one.intersection(another))
        union = len(one.intersection(another))
        if intersection:
            return intersection / union
        return 0.0


class TFIDFMatcher(PairwiseMatcher):
    def __init__(self, *args, smooth=2.0, ngram=1, **kwargs):
        super(TFIDFMatcher, self).__init__(*args, **kwargs)
        self.smooth = smooth
        self.ngram = ngram
        self.vocab = Counter()

    def fit(self, texts, labels):
        self.vocab = Counter(w for t in texts for w in self._tokenize(t))
        self._texts = [self.preprocess(text) for text in texts]
        self._labels = labels

    def preprocess(self, text):
        text = super(TFIDFMatcher, self).preprocess(text)
        tf = Counter(self._tokenize(text))
        return {w: tf / math.log(self.smooth + self.vocab[w]) for w, tf in tf.items()}

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


_matchers = dict()


def register_matcher(name, matcher_maker):
    _matchers[name] = matcher_maker


def make_matcher(key, **kwargs):
    return _matchers[key](**kwargs)


register_matcher('exact', lambda **kwargs: ExactMatcher(**kwargs))
register_matcher('levenshtein', lambda **kwargs: TextDistanceMatcher(by_words=False, metric='levenshtein', **kwargs))
register_matcher('cosine', lambda **kwargs: TextDistanceMatcher(by_words=True, metric='cosine', **kwargs))
register_matcher('tf-id', lambda **kwargs: TFIDFMatcher(**kwargs))
