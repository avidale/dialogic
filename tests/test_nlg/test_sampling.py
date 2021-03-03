from dialogic.nlg.sampling import sample


def test_sample():
    pattern = '{cat|dog}{ never| always}* says {bow-wow|meow}'
    variants = {sample(pattern, rnd=True) for i in range(1000)}
    assert 'cat never says bow-wow' in variants
    assert 'dog says meow' in variants
    assert len(variants) == 2 * 3 * 2
    assert len({sample(pattern, rnd=False) for i in range(1000)}) == 1
