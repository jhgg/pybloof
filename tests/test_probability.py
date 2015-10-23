
import _pybloof

import random
import string

def random_string(length):
    char_set = string.ascii_letters + string.digits
    return ''.join(random.sample(char_set*6, 6))

def test_string_bf():
    bloom_filter = _pybloof.StringBloomFilter
    member_generator =  lambda x: random_string(10)

    bf_est_elements=    20
    FP_rate =           0.1
    bf_size=            96
    bf_hashes=          3

    members_added_count = int(bf_est_elements*0.8)
    FP_rate_real = calculate_false_positive_rate(bloom_filter, member_generator, bf_size, bf_hashes, members_added_count)
    print("False positive rate, aim: {}, real: {}".format(FP_rate, FP_rate_real))
    assert FP_rate >= FP_rate_real

def test_long_bf():
    bloom_filter = _pybloof.LongBloomFilter
    member_generator =  lambda x: random.randint(-9223372036854775807, 9223372036854775807)

    bf_est_elements=    20
    FP_rate =           0.1
    bf_size=            96
    bf_hashes=          3

    members_added_count = int(bf_est_elements*0.8)
    FP_rate_real = calculate_false_positive_rate(bloom_filter, member_generator, bf_size, bf_hashes, members_added_count)
    print("False positive rate, aim: {}, real: {}".format(FP_rate, FP_rate_real))
    assert FP_rate >= FP_rate_real

def test_uint_bf():
    bloom_filter = _pybloof.UIntBloomFilter
    member_generator =  lambda x: random.randint(0, 4294967295)

    bf_est_elements=    20
    FP_rate =           0.1
    bf_size=            96
    bf_hashes=          3

    members_added_count = int(bf_est_elements*0.8)
    FP_rate_real = calculate_false_positive_rate(bloom_filter, member_generator, bf_size, bf_hashes, members_added_count)
    print("False positive rate, aim: {}, real: {}".format(FP_rate, FP_rate_real))
    assert FP_rate >= FP_rate_real

def calculate_false_positive_rate(bloom_filter, member_generator, bf_size, bf_hashes, members_added_count):

    # Create bloom filter and add random members
    bf = bloom_filter(bf_size, bf_hashes)
    members_added = map(member_generator, [None] * members_added_count)
    [bf.add(e) for e in members_added]

    # Create random test members
    test_members_count = members_added_count * 100
    test_members = map(member_generator, [None] * test_members_count)

    # Test to see if the members are 'in' the filter
    members_added = set(members_added)
    test = [e in bf for e in test_members if e not in members_added] # Use only test members which are not in the member set

    # Calculate FP rate
    false_positives = len([e for e in test if e == True])
    false_positives_rate = false_positives / float(test_members_count)
    return false_positives_rate