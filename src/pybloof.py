from __future__ import division

import operator
import _pybloof
from math import ceil, log

LongBloomFilter = _pybloof.LongBloomFilter
StringBloomFilter = _pybloof.StringBloomFilter
UIntBloomFilter = _pybloof.UIntBloomFilter


def bloom_calculator(n, p):
    """
    Calculate the optimal bloom filter parameters for a given number of elements in filter (n) and false
    positive probability (p)
    """
    m = int(ceil((n * log(p)) / log(1.0 / (pow(2.0, log(2.0))))))
    k = int(log(2.0) * m / n)
    return {'size': m, 'hashes': k}
