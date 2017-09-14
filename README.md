pysettrie
=========
[![Build Status](https://travis-ci.org/datamade/pysettrie.svg)](https://travis-ci.org/datamade/pysettrie)

https://github.com/mmihaltz/pysettrie

pysettrie is a python3 package that provides support for efficient storage and querying of sets of sets 
using the trie data structure, supporting operations like finding all the supersets/subsets of a given set 
from a collection of sets.
The original motivation for this module was to provide efficient search for supersets of sets of feature-value pairs in our natural language parser project (e.g. matching nouns against verb argument positions).

The following classes are included: 
- SetTrie: set-trie container for sets; supports efficient supersets/subsets of a given search set calculations. 
- SetTrieMap: mapping container using sets as keys; supports efficient operations like SetTrie but also stores values associated to the key sets.
- SetTrieMultiMap: like SetTrieMap, but supports multiple values associated to each key.

For further information, please see [documentation](docs/build/html/index.html)

Module test_settrie.py contains unittests for all the containers.

Author: Márton Miháltz 
[https://sites.google.com/site/mmihaltz/](https://sites.google.com/site/mmihaltz/)

This package depends on the [sortedcollection](http://grantjenks.com/docs/sortedcontainers/) module.
One recommended way to install (tested on Ubuntu):
```
sudo pip3 install sortedcontainers
```
If you don't have pip3:
```
sudo apt-get install python3-setuptools
sudo easy_install3 pip
```

pysettrie is partly based on:
I.Savnik: Index data structure for fast subset and superset queries. CD-ARES, IFIP LNCS, 2013.
http://osebje.famnit.upr.si/~savnik/papers/cdares13.pdf
Remarks on paper: 
- Algorithm 1. does not mention to sort children (or do sorted insert) in insert operation (line 5)
- Algorithm 4. is wrong, will always return false, line 7 should be: "for (each child of node labeled l: word.currentElement <= l) & (while not found) do"
- the descriptions of getAllSubSets and getAllSuperSets operations are wrong, would not produce all sub/supersets

See also:
- http://stackoverflow.com/questions/9353100/quickly-checking-if-set-is-superset-of-stored-sets
- http://stackoverflow.com/questions/1263524/superset-search?rq=1

Changes:
* Version 0.1.3:
  - SetTrieMultiMap.assign() returns number of values associated to key after assignment.

Licensed under the [GNU LESSER GENERAL PUBLIC LICENSE, Version 3](https://www.gnu.org/licenses/lgpl.html).

