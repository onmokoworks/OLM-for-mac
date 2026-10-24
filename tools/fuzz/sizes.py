"""Opt-in odd/even full-comp dimensions, independent of the legacy RNG stream."""
import random
from core import case_seed

VERSION = 'odd-even-v1'


def dimensions(seed, index, maximum, height_maximum=None):
    if maximum < 1:
        raise ValueError('size maximum must be positive')
    rng = random.Random(case_seed(seed, index) ^ 0x715B)

    def axis(maximum):
        # Independent parity draws; tiny values and primes have explicit weight.
        parity = rng.randrange(2) if maximum > 1 else 1
        values = [n for n in (1, 2, 3, 5, 7, 11, 17, 31, 61, 127, 251, 509,
                             1021, 2039, 4093) if n <= maximum and n % 2 == parity]
        if values and rng.random() < .25:
            return rng.choice(values)
        limit = min(maximum, rng.choice((8, 32, 128, maximum, maximum)))
        first = 1 if parity else 2
        return first + 2*rng.randrange((limit-first)//2+1)

    return axis(maximum), axis(height_maximum or maximum)


def selected(adapter, seed, index, legacy):
    mode = getattr(adapter, 'size_sampler', 'default')
    if mode == 'default':
        return legacy
    if mode != VERSION:
        raise ValueError('unknown size sampler: '+mode)
    return dimensions(seed, index, adapter.max_size, getattr(adapter, "size_max_height", None))
