pysettrie
=========

pysettrie is a pure-python package that provides support for efficient storage and querying of sets of sets 
using the trie data structure, supporting operations like finding all the supersets/subsets of a given set 
from a collection of sets.

The following classes are included: 
- SetTrie: set-trie container for sets; supports efficient supersets/subsets of a given search set calculations. 
- SetTrieMap: mapping container using sets as keys; supports efficient operations like SetTrie but also stores values associated to the key sets.

For further documentation, please see docstring comments in the source file (settrie.py).

Module test_settrie.py contains unittests for SetTrie and SetTrieMap classes.

Version 1.0
Release date: 2014-12-06
Author: Márton Miháltz 
<mmihaltz@gmail.com>
[https://sites.google.com/site/mmihaltz/](https://sites.google.com/site/mmihaltz/)

This module depends on the [sortedcollection](http://grantjenks.com/docs/sortedcontainers/) module.
One recommended way to install (tested on Ubuntu):
sudo pip3 install sortedcontainers
If you don't have pip3:
sudo apt-get install python3-setuptools
sudo easy_install3 pip

Based on:
I.Savnik: Index data structure for fast subset and superset queries. CD-ARES, IFIP LNCS, 2013.
http://osebje.famnit.upr.si/~savnik/papers/cdares13.pdf
Remarks on paper: 
- Algorithm 1. does not mention to sort children (or do sorted insert) in insert operation (line 5)
- Algorithm 4. is wrong, will always return false, line 7 should be: "for (each child of node labeled l: word.currentElement <= l) & (while not found) do"
- the descriptions of getAllSubSets and getAllSuperSets operations are wrong, would not produce all sub/supersets
See also:
http://stackoverflow.com/questions/9353100/quickly-checking-if-set-is-superset-of-stored-sets
http://stackoverflow.com/questions/1263524/superset-search?rq=1

Licensed under the [GNU LESSER GENERAL PUBLIC LICENSE, Version 3](See https://www.gnu.org/licenses/lgpl.html).

