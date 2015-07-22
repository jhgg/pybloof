import _pybloof


def test__mhash3():
    h1 = _pybloof.hash('foo')
    h2 = _pybloof.hash('foo', h1 & 0xFFFFFFFF)
    print h1, h2
    assert (-39287385592190013122878999397579195001,
            -73964642705803263641983394469427790275) == (h1, h2)


def test_null_key():
    h0 = _pybloof.hash('foo')
    h1 = _pybloof.hash('foo\0bar')
    h2 = _pybloof.hash('foo\0baz')
    assert h0 != h1, 'Hash collision for appended null'
    assert h0 != h2, 'Hash collision for appended null'
    assert h1 != h2, 'Hash collision for bytes after null'


def test_mhash3_long():
    h1 = _pybloof.hash_long(123)
    h2 = _pybloof.hash_long(123, h1 & 0xFFFFFFF)

    assert (-121703982708902402444108248539236701464,
            30126007557438804793814493095132085929) == (h1, h2)
