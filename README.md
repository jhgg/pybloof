# Pybloof

Pybloof is a simple Bloom Filter implementation using the murmur hash 3 as the hashing algorithm. It is inspired by
work by https://github.com/crankycoder/hydra/ with some distinct differences. 

1. To handle the bit-array, I opted to use https://github.com/ilanschnell/bitarray instead of rolling my own. The 
python call overhead is a bit larger than having it in pure cython, but for my purposes it's good enough. 

2. The data is not memory mapped then. Rather, it's stored in memory with methods to efficiently export it to an 
array object (to_byte_array, from_byte_array) or base64 (to_base64, from_base64). It does this as fast as possible, 
most of the time constructing the bloom filter is just a few simple `memcpy`s. 
  
3. There is a specialized bloom filter for storing strings: `StringBloomFilter`, long longs: `LongBloomFilter` and 
unsigned integers: `UIntBloomFilter`. These specializations make the creation of a bloom filter from a list (or array)
of integers vastly more efficient than using a bloom filter written for strings, as it uses murmur3 on the integer or 
long directly, rather than the string representation of that number. 

# Development & Testing

Install the packages and run some tests:

```
$ pip install -r requirements.txt
$ python setup.py develop
$ python setup.py test
```

# Install Guide

Via pip:

```
$ pip install pybloof
```

Via setup.py:

```
$ git clone https://github.com/jhgg/pybloof
$ cd pybloof
$ python setup.py install
```

# API Reference

| Data Type | Bloom Filter |
| --------- | ------------ |
| strings   | `StringBloomFilter` |
| longs     | `LongBloomFilter` |
| unsigned ints | `UIntBloomFilter` |

For these examples, I will be using the `UIntBloomFilter`. 


```python
import pybloof

filter = pybloof.UIntBloomFilter(size=100, hashes=9)

```

#### You can add a single element to a bloom filter:

```python
filter.add(500)
filter.add(7)
```

#### Or you can add a `list` of items

```python
filter.extend([1, 2, 3, 4])
```

#### Or you can add an `array` of unsigned integers. 

```python
import array
some_array = array.array('I', [9, 12, 55, 31])
filter.extend_array(some_array)
```

### You can get an array back of data from the bloom filter, and pass it around to make copies, or serialize the bloom filter to disk. 
This is a fast operation only involving a single `malloc` and `memcpy`. This  creates a copy of the data in the bloom 
filter. Updating the filter after converting it to a byte array, will not update the byte array.

```python
filter_array = filter.to_byte_array()
filter.add(90210)

assert filter_array != filter.to_byte_array()
```

#### In addition, you can copy the bloom filter like this:

```python
filter_2 = UIntBloomFilter.from_byte_array(filter_array) 
assert 90210 not in filter_2
```

#### Also, you can base64 encode and decode the filter:

```python
b64 = filter.to_base64()
filter_3 = UIntBloomFilter.from_base64(b64)
```

#### A bloom filter is useless (all containment queries will return True) once all the bits in the underlying bit array are true. 
You can check to see if this has happened to your bloom filter:

```python
print filter.is_full()
```

If that's happened, then you probably need a larger size. There are functions to do these calculations in `pybloof`
to optimize your bloom filter sizes, see `pybloof.BloomCalculations`. 

#### Finally, you can clear your bloom filter using:

```python
filter.clear()
```

# License:

```
The MIT License (MIT)

Copyright (c) 2015 Jake Heinz

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
```