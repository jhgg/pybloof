from cpython cimport array
cimport cpython
cimport cython

import bitarray
import struct
import base64

from libc.string cimport memcpy

cdef array.array char_array_template = array.array('b', [])

cdef extern from "MurmurHash3.h" nogil:
    void MurmurHash3_x64_128(void *key, int len, unsigned int seed, void *out)
    void MurmurHash3_x64_128_long(long key, unsigned int seed, void *out)

cdef extern from "stdlib.h" nogil:
    long long int llabs(long long int j)

def hash(key, int seed=0):
    cdef long long result[2]
    if isinstance(key, unicode):
        key = key.encode('utf8')

    MurmurHash3_x64_128(<char*> key, len(key), seed, result)
    return long(result[0]) << 64 | (long(result[1]) & 0xFFFFFFFFFFFFFFFF)

def hash_long(long long key, int seed=0):
    cdef long long result[2]
    MurmurHash3_x64_128_long(key, seed, result)
    return long(result[0]) << 64 | (long(result[1]) & 0xFFFFFFFFFFFFFFFF)

@cython.boundscheck(False)
cdef void _get_hash_buckets(key, unsigned long long * _bucket_indexes, unsigned int hash_count, unsigned long max):
    cdef unsigned long result[2]
    cdef unsigned long hash1, hash2
    cdef unsigned long i

    if isinstance(key, unicode):
        key = key.encode('utf8')

    MurmurHash3_x64_128(<char*>key, len(key), 0, result)
    hash1 = result[0]
    MurmurHash3_x64_128(<char*>key, len(key), result[1] & 0xFFFFFFFF, result)
    hash2 = result[0]

    for i in range(hash_count):
        _bucket_indexes[i] = llabs((hash1 + i * hash2) % max)\

@cython.boundscheck(False)
cdef void _get_hash_buckets_for_long(long long key, unsigned long long * _bucket_indexes, unsigned int hash_count,
                                     unsigned long max):
    cdef unsigned long result[2]
    cdef unsigned long hash1, hash2
    cdef unsigned long i

    MurmurHash3_x64_128_long(key, 0, &result)
    hash1 = result[0]
    MurmurHash3_x64_128_long(key, result[1] & 0xFFFFFFFF, result)
    hash2 = result[0]

    for i in range(hash_count):
        _bucket_indexes[i] = llabs((hash1 + i * hash2) % max)


cdef char* fmt = '!III'
cdef ssize_t header_size = sizeof(unsigned int) * 3
DEF MAX_HASHES = 32

cdef class _BloomFilter:
    cdef unsigned int _size
    cdef unsigned int _hashes
    cdef object _bitarray

    def __cinit__(self, unsigned long size, unsigned int hashes, cpython.bool _clear=True):
        self._size = size
        self._hashes = min(hashes, MAX_HASHES)
        self._bitarray = bitarray.bitarray(size)

        if _clear:
            self._bitarray.setall(False)

    cpdef _from_byte_array(self, array.array byte_array):
        (address, size, endianness, unused, allocated) = self._bitarray.buffer_info()
        memcpy(cpython.PyLong_AsVoidPtr(address), byte_array.data.as_chars + header_size,
               byte_array.ob_size - header_size)

    cpdef is_full(self):
        return self._bitarray.all()

    @classmethod
    def from_byte_array(cls, array.array byte_array):
        assert byte_array.ob_size > header_size
        array_size, bit_size, hashes = struct.unpack_from(fmt, byte_array)
        assert bit_size / 8 <= array_size
        assert array_size == byte_array.ob_size - header_size
        cdef bf = cls(bit_size, hashes, _clear=False)
        bf._from_byte_array(byte_array)
        return bf

    def to_byte_array(self):
        (address, size, endianness, unused, allocated) = self._bitarray.buffer_info()
        cdef unsigned int length = size + header_size
        cdef array.array byte_array = array.clone(char_array_template, length, False)
        struct.pack_into(fmt, byte_array, 0, size, self._size, self._hashes)
        memcpy(byte_array.data.as_chars + header_size, cpython.PyLong_AsVoidPtr(address), size)
        return byte_array

    def to_base64(self):
        return base64.b64encode(self.to_byte_array())

    @classmethod
    def from_base64(cls, bytes s):
        return cls.from_byte_array(array.array('b', base64.b64decode(s)))

    property hashes:
        def __get__(self):
            return self._hashes

    property size:
        def __get__(self):
            return self._size

    cpdef clear(self):
        self._bitarray.setall(False)

cdef class LongBloomFilter(_BloomFilter):
    @cython.boundscheck(False)
    cpdef add(self, long long item):
        cdef unsigned long long _bucket_indexes[MAX_HASHES]
        cdef unsigned int i
        _get_hash_buckets_for_long(item, _bucket_indexes, self._hashes, self._size)
        for i in range(self._hashes):
            self._bitarray[_bucket_indexes[i]] = 1

    @cython.boundscheck(False)
    cpdef extend(self, items):
        cdef unsigned int i

        cdef unsigned long long _bucket_indexes[MAX_HASHES]
        for item in items:
            _get_hash_buckets_for_long(item, _bucket_indexes, self._hashes, self._size)
            for i in range(self._hashes):
                self._bitarray[_bucket_indexes[i]] = 1

    @cython.boundscheck(False)
    cpdef extend_array(self, long long[:] items):
        cdef unsigned int i

        cdef unsigned long long _bucket_indexes[MAX_HASHES]
        for item in items:
            _get_hash_buckets_for_long(item, _bucket_indexes, self._hashes, self._size)
            for i in range(self._hashes):
                self._bitarray[_bucket_indexes[i]] = 1

    @cython.boundscheck(False)
    cpdef contains(self, long long item):
        cdef unsigned long long _bucket_indexes[MAX_HASHES]
        cdef unsigned int i
        _get_hash_buckets_for_long(item, _bucket_indexes, self._hashes, self._size)

        for i in range(self._hashes):
            if not self._bitarray[_bucket_indexes[i]]:
                return False

        return True

    def __contains__(self, long long item):
        return self.contains(item)

cdef class UIntBloomFilter(_BloomFilter):
    @cython.boundscheck(False)
    cpdef add(self, unsigned int item):
        cdef unsigned long long _bucket_indexes[MAX_HASHES]
        cdef unsigned int i
        _get_hash_buckets_for_long(item, _bucket_indexes, self._hashes, self._size)
        for i in range(self._hashes):
            self._bitarray[_bucket_indexes[i]] = 1

    @cython.boundscheck(False)
    cpdef extend(self, items):
        cdef unsigned int i

        cdef unsigned long long _bucket_indexes[MAX_HASHES]
        for item in items:
            _get_hash_buckets_for_long(item, _bucket_indexes, self._hashes, self._size)
            for i in range(self._hashes):
                self._bitarray[_bucket_indexes[i]] = 1

    @cython.boundscheck(False)
    cpdef extend_array(self, unsigned int[:] items):
        cdef unsigned int i

        cdef unsigned long long _bucket_indexes[MAX_HASHES]
        for item in items:
            _get_hash_buckets_for_long(item, _bucket_indexes, self._hashes, self._size)
            for i in range(self._hashes):
                self._bitarray[_bucket_indexes[i]] = 1

    @cython.boundscheck(False)
    cpdef contains(self, unsigned int item):
        cdef unsigned long long _bucket_indexes[MAX_HASHES]
        cdef unsigned int i
        _get_hash_buckets_for_long(item, _bucket_indexes, self._hashes, self._size)
        for i in range(self._hashes):
            if not self._bitarray[_bucket_indexes[i]]:
                return False

        return True

    def __contains__(self, unsigned int item):
        return self.contains(item)

cdef class StringBloomFilter(_BloomFilter):
    cpdef add(self, item):
        cdef unsigned long long _bucket_indexes[MAX_HASHES]
        cdef unsigned int i
        _get_hash_buckets(item, _bucket_indexes, self._hashes, self._size)

        for i in range(self._hashes):
            self._bitarray[_bucket_indexes[i]] = 1

    @cython.boundscheck(False)
    cpdef contains(self, item):
        cdef unsigned long long _bucket_indexes[MAX_HASHES]
        cdef unsigned int i

        _get_hash_buckets(item, _bucket_indexes, self._hashes, self._size)
        for i in range(self._hashes):
            if not self._bitarray[_bucket_indexes[i]]:
                return False

        return True

    def __contains__(self, item):
        return self.contains(item)
