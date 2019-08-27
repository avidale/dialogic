import random


def make_unique(seq):
    """ Remove duplicates from a sequence (keep=first), without losing its ordering """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def sample_at_most(seq, n=1):
    """ Sample min(n, len(seq)) unique elements from seq in random order """
    seq = list(set(seq))
    random.shuffle(seq)
    return seq[:n]
