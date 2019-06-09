import textdistance
from tgalice.nlu import basic_nlu


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
    def __init__(self, *args, **kwargs):
        super(PairwiseMatcher, self).__init__(*args, **kwargs)
        self._texts = []
        self._labels = []

    def preprocess(self, text):
        raise NotImplementedError()

    def compare(self, one, another):
        raise NotImplementedError()

    def fit(self, texts, labels):
        self._texts = [self.preprocess(text) for text in texts]
        self._labels = labels

    def get_scores(self, text):
        processed = self.preprocess(text)
        return [self.compare(processed, t) for t in self._texts], self._labels


class TextDistanceMatcher(PairwiseMatcher):
    def __init__(self, *args, by_words=True, metric='cosine', normalize='fast', **kwargs):
        super(TextDistanceMatcher, self).__init__(*args, **kwargs)
        self.by_words = by_words
        self.metric = metric
        self.normalize = normalize
        self.fun = getattr(textdistance, metric).normalized_similarity

    def preprocess(self, text):
        if self.normalize == 'fast':
            text = basic_nlu.fast_normalize(text)
        if self.by_words:
            return text.split()
        return text

    def compare(self, one, another):
        print(one, another, self.fun(one, another))
        return self.fun(one, another)


class ExactMatcher(PairwiseMatcher):
    def preprocess(self, text):
        return basic_nlu.fast_normalize(text)

    def compare(self, one, another):
        return float(one == another)


class JaccardMatcher(PairwiseMatcher):
    def preprocess(self, text):
        return set(basic_nlu.fast_normalize(text).split())

    def compare(self, one, another):
        intersection = len(one.intersection(another))
        union = len(one.intersection(another))
        if intersection:
            return intersection / union
        return 0.0


_matchers = dict()


def register_matcher(name, matcher_maker):
    _matchers[name] = matcher_maker


def make_matcher(key, **kwargs):
    return _matchers[key](**kwargs)


register_matcher('exact', lambda **kwargs: ExactMatcher(**kwargs))
register_matcher('levenshtein', lambda **kwargs: TextDistanceMatcher(by_words=False, metric='levenshtein', **kwargs))
register_matcher('cosine', lambda **kwargs: TextDistanceMatcher(by_words=True, metric='cosine', **kwargs))
