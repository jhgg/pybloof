from array import array
import _pybloof


def test_pybloof():
    dmc = _pybloof.StringBloomFilter(500, 9)
    dmc.add('test')

    assert 'test' in dmc
    assert 'duck' not in dmc


def test_long_pybloof():
    dmc = _pybloof.LongBloomFilter(500, 9)

    dmc.add(1015L)
    dmc.add(1015L)

    assert dmc.size == 500

    assert 1015L in dmc
    assert 1015 in dmc
    assert 2015 not in dmc

    origin = dmc.to_byte_array().tostring().encode('hex')
    dmc_2 = _pybloof.LongBloomFilter.from_byte_array(dmc.to_byte_array())
    clone = dmc_2.to_byte_array().tostring().encode('hex')
    assert origin == clone

    assert 1015L in dmc_2
    assert 1015 in dmc_2
    assert 2015 not in dmc_2

    assert dmc.size == dmc_2.size
    assert dmc.hashes == dmc_2.hashes

    base64 = dmc.to_base64()
    dmc_3 = _pybloof.LongBloomFilter.from_base64(base64)

    assert 1015L in dmc_3
    assert 1015 in dmc_3
    assert 2015 not in dmc_3

    assert dmc.size == dmc_3.size

    dmc.clear()

    assert 1015 not in dmc
    assert dmc.size == 500


def test_extend():
    dmc = _pybloof.LongBloomFilter(500, 9)

    dmc.extend([10, 25, 35])

    dmc2 = _pybloof.LongBloomFilter(500, 9)
    dmc2.extend_array(array('l', [10, 25, 35]))

    assert dmc2.to_base64() == dmc.to_base64()


def test_extend_uint():
    dmc = _pybloof.UIntBloomFilter(500, 9)

    dmc.extend([10, 25, 35])

    dmc2 = _pybloof.UIntBloomFilter(500, 9)
    dmc2.extend_array(array('I', [10, 25, 35]))

    assert dmc2.to_base64() == dmc.to_base64()
