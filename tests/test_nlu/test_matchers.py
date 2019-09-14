import numpy as np
import pytest

from tgalice.nlu import matchers

sample_texts = ['привет', 'добрый день', 'сколько времени']
sample_labels = ['hello', 'hello', 'get_time']


def test_exact_matcher():
    matcher = matchers.make_matcher('exact')
    matcher.fit(sample_texts, sample_labels)
    assert matcher.match('привет') == ('hello', 1)
    assert matcher.match('приветик') == (None, 0)
    assert matcher.match('добрый день') == ('hello', 1)
    assert matcher.match('день добрый') == (None, 0)


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
    assert matcher.match('добрый упоротыш') == (None, 0)
    assert matcher.match('добрый хомяк')[0] == 'animal'
    assert matcher.match('животное собака')[0] == 'animal'


def test_average_matcher():
    matcher = matchers.WeightedAverageMatcher(
        matchers=[matchers.make_matcher('exact'), matchers.JaccardMatcher()],
        threshold=0.1
    )
    matcher.fit(sample_texts, sample_labels)
    assert matcher.match('добрый день') == ('hello', 1)
    assert matcher.match('добрый вечер') == ('hello', 1/3 * 0.5 + 0 * 0.5)
    assert matcher.match('добрый') == ('hello', 1/2 * 0.5 + 0 * 0.5)


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
        for l, r in zip(lhs, rhs):
            if l == r:
                result += 1
            else:
                break
        print(result)
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
    assert matcher.match('абракадабра') == (None, 0)
    label, score = matcher.match('злой ночь')
    assert label == 'hello'
    assert 0.95 < score < 0.99
