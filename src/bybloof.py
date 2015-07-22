import operator
import _pybloof

LongBloomFilter = _pybloof.LongBloomFilter
StringBloomFilter = _pybloof.StringBloomFilter
UIntBloomFilter = _pybloof.UIntBloomFilter

"""
BloomSpecification and BloomCalculations are from: https://github.com/crankycoder/hydra/

The MIT License (MIT)

Copyright (c) 2010 Victor Ng

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


class UnsupportedOperationException(Exception):
    pass


class BloomSpecification(object):
    """
    A wrapper class that holds two key parameters for a Bloom Filter: the
    number of hash functions used, and the number of buckets per element used.
    """

    def __init__(self, k, buckets_per_element):
        self.K = k
        self.buckets_per_element = buckets_per_element

    def __eq__(self, other):
        c1 = getattr(other, 'K', None) == self.K
        c2 = getattr(other, 'buckets_per_element', None) == self.buckets_per_element
        return c1 and c2


class BloomCalculations(object):
    """
    This calculation class is ported straight from Cassandra.
    """
    min_buckets = 2
    min_k = 1

    PROBS = [
        [1.0],  # dummy row representing 0 buckets per element
        [1.0, 1.0],  # dummy row representing 1 buckets per element
        [1.0, 0.393, 0.400],
        [1.0, 0.283, 0.237, 0.253],
        [1.0, 0.221, 0.155, 0.147, 0.160],
        [1.0, 0.181, 0.109, 0.092, 0.092, 0.101],  # 5
        [1.0, 0.154, 0.0804, 0.0609, 0.0561, 0.0578, 0.0638],
        [1.0, 0.133, 0.0618, 0.0423, 0.0359, 0.0347, 0.0364],
        [1.0, 0.118, 0.0489, 0.0306, 0.024, 0.0217, 0.0216, 0.0229],
        [1.0, 0.105, 0.0397, 0.0228, 0.0166, 0.0141, 0.0133, 0.0135, 0.0145],
        [1.0, 0.0952, 0.0329, 0.0174, 0.0118, 0.00943, 0.00844, 0.00819, 0.00846],  # 10
        [1.0, 0.0869, 0.0276, 0.0136, 0.00864, 0.0065, 0.00552, 0.00513, 0.00509],
        [1.0, 0.08, 0.0236, 0.0108, 0.00646, 0.00459, 0.00371, 0.00329, 0.00314],
        [1.0, 0.074, 0.0203, 0.00875, 0.00492, 0.00332, 0.00255, 0.00217, 0.00199, 0.00194],
        [1.0, 0.0689, 0.0177, 0.00718, 0.00381, 0.00244, 0.00179, 0.00146, 0.00129, 0.00121, 0.0012],
        [1.0, 0.0645, 0.0156, 0.00596, 0.003, 0.00183, 0.00128, 0.001, 0.000852, 0.000775, 0.000744],  # 15
        [1.0, 0.0606, 0.0138, 0.005, 0.00239, 0.00139, 0.000935, 0.000702, 0.000574, 0.000505, 0.00047, 0.000459],
        [1.0, 0.0571, 0.0123, 0.00423, 0.00193, 0.00107, 0.000692, 0.000499, 0.000394, 0.000335, 0.000302, 0.000287,
         0.000284],
        [1.0, 0.054, 0.0111, 0.00362, 0.00158, 0.000839, 0.000519, 0.00036, 0.000275, 0.000226, 0.000198, 0.000183,
         0.000176],
        [1.0, 0.0513, 0.00998, 0.00312, 0.0013, 0.000663, 0.000394, 0.000264, 0.000194, 0.000155, 0.000132, 0.000118,
         0.000111, 0.000109],
        [1.0, 0.0488, 0.00906, 0.0027, 0.00108, 0.00053, 0.000303, 0.000196, 0.00014, 0.000108, 8.89e-05, 7.77e-05,
         7.12e-05, 6.79e-05, 6.71e-05]  # 20
    ]

    opt_k_per_buckets = [max(1, min(enumerate(probs), key=operator.itemgetter(1))[0]) for probs in PROBS]

    @classmethod
    def computeBloomSpec1(cls, buckets_per_element):
        """
        Given the number of buckets that can be used per element, return a
        specification that minimizes the false positive rate.
        @param buckets_per_element The number of buckets per element for the filter.
        @return A spec that minimizes the false positive rate.
        """
        assert buckets_per_element >= 1
        assert buckets_per_element <= len(BloomCalculations.PROBS) - 1
        return BloomSpecification(cls.opt_k_per_buckets[buckets_per_element], buckets_per_element)

    @classmethod
    def computeBloomSpec2(cls, max_buckets_per_element, max_false_positive_probability):
        """
        Given a maximum tolerable false positive probability, compute a Bloom
        specification which will give less than the specified false positive rate,
        but minimize the number of buckets per element and the number of hash
        functions used.  Because bandwidth (and therefore total bitvector size)
        is considered more expensive than computing power, preference is given
        to minimizing buckets per element rather than number of hash functions.
        @param max_buckets_per_element The maximum number of buckets available for the filter.
        @param max_false_positive_probability The maximum tolerable false positive rate.
        @return A Bloom Specification which would result in a false positive rate
        less than specified by the function call
        @throws UnsupportedOperationException if a filter satisfying the parameters cannot be met
        """
        assert max_buckets_per_element >= 1
        assert max_buckets_per_element <= len(BloomCalculations.PROBS) - 1
        maxK = len(BloomCalculations.PROBS[max_buckets_per_element]) - 1

        # Handle the trivial cases
        if max_false_positive_probability >= BloomCalculations.PROBS[cls.min_buckets][cls.min_k]:
            return BloomSpecification(2, cls.opt_k_per_buckets[2])

        if max_false_positive_probability < BloomCalculations.PROBS[max_buckets_per_element][maxK]:
            msg = "Unable to satisfy %s with %s buckets per element"
            raise UnsupportedOperationException(msg % (max_false_positive_probability, max_buckets_per_element))

        # First find the minimal required number of buckets:
        buckets_per_element = 2
        K = cls.opt_k_per_buckets[2]
        while BloomCalculations.PROBS[buckets_per_element][K] > max_false_positive_probability:
            buckets_per_element += 1
            K = cls.opt_k_per_buckets[buckets_per_element]
        # Now that the number of buckets is sufficient, see if we can relax K
        # without losing too much precision.
        while BloomCalculations.PROBS[buckets_per_element][K - 1] <= max_false_positive_probability:
            K -= 1

        return BloomSpecification(K, buckets_per_element)
