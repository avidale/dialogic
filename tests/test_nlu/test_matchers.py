import numpy as np
import pytest
import math


from tgalice.nlu import matchers

sample_texts = ['привет', 'добрый день', 'сколько времени']
sample_labels = ['hello', 'hello', 'get_time']

NO_MATCH = (None, -math.inf)


def test_exact_matcher():
    matcher = matchers.make_matcher('exact')
    matcher.fit(sample_texts, sample_labels)
    assert matcher.match('привет') == ('hello', 1)
    assert matcher.match('приветик') == NO_MATCH
    assert matcher.match('добрый день') == ('hello', 1)
    assert matcher.match('день добрый') == NO_MATCH


def test_jaccard_matcher():
    matcher = matchers.JaccardMatcher(threshold=0.1)
    matcher.fit(sample_texts, sample_labels)
    assert matcher.match('добрый день') == ('hello', 1)
    assert matcher.match('добрый вечер') == ('hello', 1/3)
    assert matcher.match('добрый') == ('hello', 1/2)


def test_tfidf_matcher():
    new_texts = ['добрый день', 'доброй ночи', 'добрый вечер', 'доброе утро', 'животное хомяк', 'животное пингвин']
    new_labels = ['hello', 'hello', 'hello', 'hello', 'animal', 'animal']
    matcher = matchers.TFIDFMatcher(threshold=0.3, text_normalization='fast_lemmatize')
    matcher.fit(new_texts, new_labels)
    assert matcher.match('добрый день') == ('hello', 1)
    assert matcher.match('добрый упоротыш') == NO_MATCH
    assert matcher.match('добрый хомяк')[0] == 'animal'
    assert matcher.match('животное собака')[0] == 'animal'


@pytest.mark.parametrize('weights', [None, (1, 1), (0.2, 0.8)])
def test_average_matcher(weights):
    matcher = matchers.WeightedAverageMatcher(
        matchers=[matchers.make_matcher('exact'), matchers.JaccardMatcher()],
        threshold=0.1, weights=weights,
    )
    matcher.fit(sample_texts, sample_labels)
    weights = weights or (0.5, 0.5)
    w0, w1 = weights[0] / sum(weights), weights[1] / sum(weights)
    assert matcher.match('добрый день') == ('hello', 1)
    assert matcher.match('добрый вечер') == ('hello', 0 * w0 + 1/3 * w1)
    assert matcher.match('добрый') == ('hello', 0 * w0 + 1/2 * w1)


def test_max_matcher():
    matcher = matchers.MaxMatcher(
        matchers=[matchers.make_matcher('exact'), matchers.JaccardMatcher()],
        threshold=0.1,
    )
    matcher.fit(sample_texts, sample_labels)
    assert matcher.match('добрый день') == ('hello', 1)
    assert matcher.match('добрый вечер') == ('hello', 1/3)
    assert matcher.match('добрый') == ('hello', 1/2)


class PrefixModel:
    """ Its main goal is to mimic interface of scikit-learn models """
    def __init__(self):
        self.classes_ = []
        self._x = []
        self._y = []

    def fit(self, X, y):
        self.classes_ = sorted(set(y))
        self._y2i = {val: i for i, val in enumerate(self.classes_)}
        self._x = X
        self._y = y

    def longest_common_prefix(self, lhs, rhs):
        if lhs == rhs == '':
            return 0.0
        result = 0
        for left, right in zip(lhs, rhs):
            if left == right:
                result += 1
            else:
                break
        return result * 2.0 / (len(lhs) + len(rhs))

    def predict_proba(self, X):
        scores = np.zeros((len(X), len(self.classes_)), dtype=np.float)
        for i, text in enumerate(X):
            for x, y in zip(self._x, self._y):
                scores[i, self._y2i[y]] = max(scores[i, self._y2i[y]], self.longest_common_prefix(x, text))
        return scores


def test_model_matcher():
    matcher = matchers.ModelBasedMatcher(model=PrefixModel())
    matcher.fit(sample_texts, sample_labels)
    assert matcher.match('добрый день') == ('hello', 1)
    assert matcher.match('добрый д') == ('hello', 8 / ((8 + 11) / 2))
    assert matcher.match('добрый') == ('hello', 6 / ((6 + 11) / 2))


@pytest.mark.parametrize('matcher_class', [matchers.W2VMatcher, matchers.WMDMatcher])
def test_vectorized_matcher(matcher_class):
    w2v = {
        k: np.array(v) for k, v in
        {
            'привет': [1, 0, 0],
            'добрый': [0.5, 0.5, 0],
            'злой': [0.45, 0.55, 0],
            'день': [0.1, 0.2, 0.7],
            'ночь': [0.0, 0.4, 0.7],
            'сколько': [0.0, 0.1, 0.9],
            'времени': [0.0, 0.5, 0.5],
        }.items()
    }
    matcher = matcher_class(w2v=w2v)
    matcher.fit(sample_texts, sample_labels)
    assert matcher.match('времени сколько') == ('get_time', 1)
    assert matcher.match('абракадабра') == NO_MATCH
    label, score = matcher.match('злой ночь')
    assert label == 'hello'
    assert 0.95 < score < 0.99


def test_scores_aggregation():
    matcher = matchers.JaccardMatcher(threshold=0.1)
    matcher.fit(sample_texts, sample_labels)
    assert matcher.aggregate_scores('добрый день') == {'hello': 1}
    assert matcher.aggregate_scores('добрый день', use_threshold=False) == {'hello': 1, 'get_time': 0}
    assert matcher.aggregate_scores('привет сколько времени') == {'hello': 1/3, 'get_time': 2/3}


def test_regex_matcher():
    more_texts = sample_texts + ['.*врем.*']
    more_labels = sample_labels + ['get_time']

    matcher = matchers.RegexMatcher(add_end=False)
    matcher.fit(more_texts, more_labels)
    assert matcher.aggregate_scores('привет мир') == {'hello': 1}
    assert matcher.aggregate_scores('привет расскажи время') == {'get_time': 1, 'hello': 1}

    matcher = matchers.RegexMatcher(add_end=True)
    matcher.fit(more_texts, more_labels)
    assert matcher.aggregate_scores('привет мир') == {}
    assert matcher.aggregate_scores('расскажи время') == {'get_time': 1}
    assert matcher.aggregate_scores('привет расскажи время') == {'get_time': 1}


def test_joint_matcher_with_regex():
    intents = {
        'a': {'examples': ['an a'], 'regexp': 'a+'}
    }
    jm = matchers.make_matcher_with_regex(base_matcher=matchers.ExactMatcher(), intents=intents)
    assert jm.aggregate_scores('an a') == {'a': 1}
    assert jm.aggregate_scores('aaaa') == {'a': 1}
