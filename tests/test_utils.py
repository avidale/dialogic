from tgalice.utils.collections import make_unique, sample_at_most

import random


def test_make_unique():
    random.seed(42)
    for n in range(100):
        x = [random.randrange(10) for i in range(n)]
        y = make_unique(x)
        seen = set()
        for element in x:
            if element not in seen:
                assert y[len(seen)] == element
                seen.add(element)


def test_sample_at_most():
    random.seed(42)
    for n in range(100):
        for m in range(100):
            x = [random.randrange(10) for i in range(n)]
            y = sample_at_most(x, m)
            assert len(set(y)) == len(y)
            assert len(y) == min(m, len(set(x)))
            assert not set(y).difference(set(x))
