#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""
Module settrie

Requires Python3

Version 0.1.4
Release date: 2016-12-06

Author: Márton Miháltz
Project home: https://github.com/mmihaltz/pysettrie
Version 0.1.4: Refactoring by Balázs Indig

See README.md for more information.

Licensed under the GNU LESSER GENERAL PUBLIC LICENSE, Version 3.
See https://www.gnu.org/licenses/lgpl.html
"""

import sys

import sortedcontainers

__version__ = "0.1.4"


class Node:
    """Node object used by SetTrie."""

    def __init__(self, data=None, value=None):
        self.children = sortedcontainers.SortedList()  # child nodes a.k.a. children
        # if True, this is the last element of
        #  a) a set in the set-trie use this to store user data (a set element).
        #  b) a key set store a member element of the key set.
        self.flag_last = False
        # Must be a hashable (i.e. hash(data) should work) and comparable/orderable
        # (i.e. data1 < data2 should work; see https://wiki.python.org/moin/HowTo/Sorting/) type.
        self.data = data
        self.value = value  # the value/list of values associated to the key set if flag_last == True, otherwise None

    # comparison operators to support rich comparisons, sorting etc. using self.data as key
    def __eq__(self, other): return self.data == other.data

    def __ne__(self, other): return self.data != other.data

    def __lt__(self, other): return self.data < other.data

    def __le__(self, other): return self.data <= other.data

    def __gt__(self, other): return self.data > other.data

    def __ge__(self, other): return self.data >= other.data


class SetTrie:
    """
     Set-trie container of sets for efficient supersets/subsets of a set over a set of sets queries.

     Usage:
     ------
     >>> from settrie import SetTrie
     >>> t = SetTrie( [{1, 3}, {1, 2, 3}] )
     >>> t.add( {3, 4, 5} )
     >>> t
     [{1, 2, 3}, {1, 3}, {3, 4, 5}]
     >>> {1, 3} in t
     True
     >>> t.hassuperset( {1, 3} )
     True
     >>> t.supersets( {1, 3} )
     [{1, 2, 3}, {1, 3}]
     >>> t.subsets({1, 2, 3, 5})
     [{1, 2, 3}, {1, 3}]


     >>> t = SetTrie()
     >>> t.add( {1, 3} )
     >>> {1, 3} in t
     True
    """

    def __init__(self, iterable=None):
        """
         Initialize this set-trie. If iterable is specified, set-trie is populated from its items.
        """
        self.root = Node()
        if iterable is not None:
            for s in iterable:
                self.add(s)

    def contains(self, aset):
        """
        Returns True iff this set-trie contains element aset.
        """
        return self.r_contains(self.root, iter(sorted(aset)))

    def __contains__(self, aset):
        """
           Returns True iff this set-trie contains the elements in aset.
           This method definition allows the use of the 'in' operator
        """
        return self.contains(aset)

    def r_contains(self, node, it):
        """
        Recursive function used by self.contains().
        """
        try:
            data = next(it)
            try:
                matchnode = node.children[node.children.index(Node(data))]  # find first child with this data
                return self.r_contains(matchnode, it)  # recurse
            except ValueError:  # not found
                return False
        except StopIteration:
            return node.flag_last

    def hassuperset(self, aset):
        """
        Returns True iff there is at least one element in this set-trie that is the superset of set aset.
        """
        # TODO: if aset is not a set, convert it to a set first to collapse multiply existing elements
        return self.r_hassuperset(self.root, list(sorted(aset)), 0)

    def r_hassuperset(self, node, setarr, idx):
        """
        Used by hassuperset().
        """
        if idx > len(setarr) - 1:
            return True
        found = False
        for child in node.children:
            if child.data > setarr[idx]:  # don't go to subtrees where current element cannot be
                break
            if child.data == setarr[idx]:
                found = self.r_hassuperset(child, setarr, idx + 1)
            else:
                found = self.r_hassuperset(child, setarr, idx)
            if found:
                break
        return found

    def itersupersets(self, aset, mode=None):
        """
        Return an iterator over all elements in this set-trie that are (proper or not proper) supersets of set aset.
        """
        path = []
        return self._itersupersets(self.root, list(sorted(aset)), 0, path, mode)

    def _itersupersets(self, node, setarr, idx, path, mode):
        """
        Used by itersupersets().
        """
        if node.data is not None:
            path.append(node.data)
        if node.flag_last and idx > len(setarr) - 1:
            yield from self.yield_last(path, node, mode)
        if idx <= len(setarr) - 1:  # we still have elements of aset to find
            for child in node.children:
                if child.data > setarr[idx]:  # don't go to subtrees where current element cannot be
                    break
                if child.data == setarr[idx]:
                    yield from self._itersupersets(child, setarr, idx+1, path, mode)
                else:
                    yield from self._itersupersets(child, setarr, idx, path, mode)
        else:  # no more elements to find: just traverse this subtree to get all supersets
            for child in node.children:
                yield from self._itersupersets(child, setarr, idx, path, mode)
        if node.data is not None:
            path.pop()

    def supersets(self, aset, mode=None):
        """
        Return a list containing all elements in this set-trie that are supersets of set aset.
        """
        return list(self.itersupersets(aset, mode))

    def hassubset(self, aset):
        """
        Return True iff there is at least one set in this set that is the (proper or not proper) subset of set aset.
        """
        return self._hassubset(self.root, list(sorted(aset)), 0)

    def _hassubset(self, node, setarr, idx):
        """
        Used by hassubset().
        """
        if node.flag_last:
            return True
        if idx > len(setarr) - 1:
            return False
        found = False
        try:
            c = node.children.index(Node(setarr[idx]))
            found = self._hassubset(node.children[c], setarr, idx+1)
        except ValueError:
            pass
        if not found:
            return self._hassubset(node, setarr, idx+1)
        else:
            return True

    def itersubsets(self, aset, mode=None):
        """
        Return an iterator over all elements in this set-trie that are (proper or not proper) subsets of set aset.
        """
        path = []
        return self._itersubsets(self.root, list(sorted(aset)), 0, path, mode)

    def _itersubsets(self, node, setarr, idx, path, mode):
        """
        Used by itersubsets().
        """
        if node.data is not None:
            path.append(node.data)
        if node.flag_last:
            yield from self.yield_last(path, node, mode)
        for child in node.children:
            if idx > len(setarr) - 1:
                break
            if child.data == setarr[idx]:
                yield from self._itersubsets(child, setarr, idx+1, path, mode)
            else:
                # advance in search set until we find child (or get to the end, or get to an element > child)
                jdx = idx + 1
                while jdx < len(setarr) and child.data >= setarr[jdx]:
                    if child.data == setarr[jdx]:
                        yield from self._itersubsets(child, setarr, jdx, path, mode)
                        break
                    jdx += 1
        if node.data is not None:
            path.pop()

    def subsets(self, aset, mode=None):
        """
        Return a list of elems in this set-trie that are (proper or not proper) subsets of set aset.
        """
        return list(self.itersubsets(aset, mode))

    def iter(self, mode=None):
        """
           Returns an iterator over the elems stored in this set-trie (with pre-order tree traversal).
           The elems are returned in sorted order.
        """
        _ = mode  # Dummy command, to silence IDE
        path = []
        yield from self._iter(self.root, path, mode)

    def __iter__(self):
        """
           Returns an iterator over the elements stored in this set-trie (with pre-order tree traversal).
           The elements are returned in sorted order with their elements sorted.
        """
        return self.keys()

    def _iter(self, node, path, mode=None):
        """
        Recursive function used by self.iter().
        """
        if node.data is not None:
            path.append(node.data)
        if node.flag_last:
            yield from self.yield_last(path, node, mode)
        for child in node.children:
            yield from self._iter(child, path, mode)
        if node.data is not None:
            path.pop()

    def aslist(self):
        """
           Return a list containing all the elements stored.
           The elements are returned in sorted order.
        """
        return list(self.iter())

    def printtree(self, tabchr=' ', tabsize=2, stream=sys.stdout):
        """
           Print a mirrored 90-degree rotation of the nodes in this trie to stream (default: sys.stdout).
           Nodes marked as flag_last are trailed by the '#' character.
           tabchr and tabsize determine the indentation: at tree level n, n*tabsize tabchar characters will be used.
        """
        self.r_printtree(self.root, 0, tabchr, tabsize, stream)

    def r_printtree(self, node, level, tabchr, tabsize, stream):
        """
        Used by self.printTree(), recursive preorder traverse and printing of trie node
        """
        print(str(node.data).rjust(len(repr(node.data))+level*tabsize, tabchr) + self.print_last(node), file=stream)
        for child in node.children:
            self.r_printtree(child, level+1, tabchr, tabsize, stream)

    def __str__(self):
        """
        Returns str(self.aslist()).
        """
        return str(self.aslist())

    def __repr__(self):
        """
        Returns str(self.aslist()).
        """
        return str(self.aslist())

    # Above this line all function is common to all set-trie types
    # ------------------------------------------------------------------------------------------------------------------
    # Below this line is the differences among the functionality
    def keys(self):
        """
           This method definition enables direct iteration over a SetTrie, for example:
           >>> t = SetTrie([{1, 2}, {2, 3, 4}])
           >>> for s in t:
           >>>   print(s)
           {1, 2}
           {2, 3, 4}
        """
        return self.iter(mode=None)

    @staticmethod
    def print_last(node):
        """
        Last element is denoted by a '#' character.
        """
        return '#' if node.flag_last else ''

    @staticmethod
    def yield_last(path, node, mode):
        _ = node  # Dummy command to silence the IDE
        _ = mode  # Dummy command to silence the IDE
        return [set(path)]

    def add(self, aset):
        """
           Add set aset to the container.
           aset must be a sortable and iterable container type.
        """
        self._add(self.root, iter(sorted(aset)))

    def _add(self, node, it):
        """
           Recursive function used by self.insert().
           node is a SetTrieNode object
           it is an iterator over a sorted set
        """
        try:
            data = next(it)
            try:
                nextnode = node.children[node.children.index(Node(data))]  # find first child with this data
            except ValueError:  # not found
                nextnode = Node(data)  # create new node
                node.children.add(nextnode)  # add to children & sort
            self._add(nextnode, it)  # recurse
        except StopIteration:  # end of set to add
            node.flag_last = True


class SetTrieMap(SetTrie):
    """
        Mapping container for efficient storage of key-value pairs where the keys are sets.
        Uses efficient trie implementation. Supports querying for values associated to subsets or supersets
        of stored key sets.

        Usage:
        ------
        >>> from settrie import SetTrieMap
        >>> m = SetTrieMap()
        >>> m.assign({1,2}, 'A')
        >>> m.assign({1,2,3}, 'B')
        >>> m.assign({2,3,5}, 'C')
        >>> m
        [({1, 2}, 'A'), ({1, 2, 3}, 'B'), ({2, 3, 5}, 'C')]
        >>> m.get( {1,2,3} )
        'B'
        >>> m.get( {1, 2, 3, 4}, 'Nope!')
        'Nope!'
        >>> list(m.keys())
        [{1, 2}, {1, 2, 3}, {2, 3, 5}]
        >>> m.supersets( {1,2} )
        [({1, 2}, 'A'), ({1, 2, 3}, 'B')]
        >>> m.supersets({1, 2}, mode='keys')
        [{1, 2}, {1, 2, 3}]
        >>> m.supersets({1, 2}, mode='values')
        ['A', 'B']

        >>> t = SetTrieMap()
        >>> t.assign( {1, 3}, 'M' )
        >>> {1, 3} in t
        True
    """

    # Above this line all function is common to all set-trie types
    # ------------------------------------------------------------------------------------------------------------------
    # Below this line is the differences among the functionality
    def keys(self):
        """
        Alias for self.iter(mode='keys').
        """
        return self.iter(mode='keys')

    def values(self):
        """
        Alias for self.iter(mode='values').
        """
        return self.iter(mode='values')

    def items(self):
        """
        Alias for self.iter(mode=None).
        """
        return self.iter(mode=None)

    def get(self, keyset, default=None):
        """
        Return the value/a list of values associated to keyset if keyset is in this Map, else default.
        """
        return self._get(self.root, iter(sorted(keyset)), default)

    def _get(self, node, it, default):
        """
        Recursive function used by self.get().
        """
        try:
            data = next(it)
            try:
                matchnode = node.children[node.children.index(Node(data))]  # find first child with this data
                return self._get(matchnode, it, default)  # recurse
            except ValueError:  # not found
                return default
        except StopIteration:
            return node.value if node.flag_last else default

    @staticmethod
    def print_last(node):
        """
        Associated values are printed after ': ' trailing flag_last=True nodes.
        """
        return ': {}'.format(repr(node.value)) if node.flag_last else ''

    # Above this line all function is common to Map set-trie types
    # ------------------------------------------------------------------------------------------------------------------
    # Below this line is the differences among the functionality
    @staticmethod
    def yield_last(path, node, mode):
        """
        If mode is not None, the following values are allowed:
        mode='keys': return an iterator over only the keysets that are subsets of aset is returned
        mode='values': return an iterator over only the values that are associated to keysets that are subsets of
        aset
        If mode is neither of 'keys', 'values' or None, behavior is equivalent to mode=None.
        """
        if mode == 'keys':
            return [set(path)]
        elif mode == 'values':
            return [node.value]
        else:
            return [set(path), node.value]

    def add(self, aset):
        """
           Set up this Map object.
           If iterable is specified, it must be an iterable of (keyset, value) pairs
           from which set-trie is populated.
        """
        key, value = aset
        self.assign(key, value)

    def assign(self, akey, avalue):
        """
           Add key akey with associated value avalue to the container.
           akey must be a sortable and iterable container type.
        """
        self._assign(self.root, iter(sorted(akey)), avalue)

    def _assign(self, node, it, val, valcnt=None):
        """
        Recursive function used by self.assign().
        """
        try:
            data = next(it)
            try:
                nextnode = node.children[node.children.index(Node(data))]  # find first child with this data
            except ValueError:  # not found
                nextnode = Node(data)  # create new node
                node.children.add(nextnode)  # add to children & sort
            self._assign(nextnode, it, val, valcnt)  # recurse
        except StopIteration:  # end of set to add
            node.flag_last = True
            node.value = val


class SetTrieMultiMap(SetTrieMap):
    """
        Like SetTrieMap, but the associated values are lists that can have multiple items added.

        Usage:
        ------
        >>> from settrie import SetTrieMultiMap
        >>> m = SetTrieMultiMap()
        >>> m.assign({1,2}, 'A')
        >>> m.assign({1,2,3}, 'B')
        >>> m.assign({1,2,3}, 'BB')
        >>> m.assign({2,3,5}, 'C')
        >>>  m
        [({1, 2}, 'A'), ({1, 2, 3}, 'B'), ({1, 2, 3}, 'BB'), ({2, 3, 5}, 'C')]
        >>> m.get( {1,2,3} )
        ['B', 'BB']
        >>> m.get( {1, 2, 3, 4}, 'Nope!')
        'Nope!'
        >>> list(m.keys())
        [{1, 2}, {1, 2, 3}, {2, 3, 5}]
        >>> m.supersets( {1,2} )
        [({1, 2}, 'A'), ({1, 2, 3}, 'B'), ({1, 2, 3}, 'BB')]
        >>> m.supersets({1, 2}, mode='keys')
        [{1, 2}, {1, 2, 3}]
        >>> m.supersets({1, 2}, mode='values')
        ['A', 'B', 'BB']

        >>> t = SetTrieMap()
        >>> t.assign( {1, 3}, 'M' )
        >>> {1, 3} in t
        True
    """

    # Above this line all function is common to Map set-trie types
    # ------------------------------------------------------------------------------------------------------------------
    # Below this line is the differences among the functionality
    @staticmethod
    def yield_last(path, node, mode):
        """
        If mode is not None, the following values are allowed:
        mode='keys': return an iterator over only the keysets that are subsets of aset is returned
        mode='values': return an iterator over only the values that are associated to keysets that are subsets of
        aset
        If mode is neither of 'keys', 'values' or None, behavior is equivalent to mode=None.
        """
        if mode == 'keys':
            return [set(path)]
        elif mode == 'values':
            return node.value
        else:
            return [(set(path), val) for val in node.value]

    def add(self, aset):
        """
           Set up this Map object.
           If iterable is specified, it must be an iterable of (keyset, value) pairs
           from which set-trie is populated; key may be repeated, all associated values will be stored.
        """
        key, value = aset
        self.assign(key, value)

    def assign(self, akey, avalue):
        """
           Add key akey with associated value avalue to the container.
           akey must be a sortable and iterable container type.
           If akey is an already exising key, avalue will be appended to the associated values.
           Multiple occurrences of the same value for the same key are preserved.
           Returns number of values associated to akey after the assignment,
           ie. returns 1 if akey was a nonexisting key before this function call,
           returns (number of items before call + 1) if akey was an already existing key.
           """
        valcnt = [0]
        self._assign(self.root, iter(sorted(akey)), avalue, valcnt)
        return valcnt[0]

    def _assign(self, node, it, val, valcnt=None):
        """
        Recursive function used by self.assign().
        """
        try:
            data = next(it)
            try:
                nextnode = node.children[node.children.index(Node(data))]  # find first child with this data
            except ValueError:  # not found
                nextnode = Node(data)  # create new node
                node.children.add(nextnode)  # add to children & sort
            self._assign(nextnode, it, val, valcnt)  # recurse
        except StopIteration:  # end of set to add
            node.flag_last = True
            if node.value is None:
                node.value = []
            node.value.append(val)
            valcnt[0] = len(node.value)  # return # of values for key after this assignment

    def count(self, keyset):
        """
        Returns the number of values associated to keyset. If keyset is unknown, returns 0.
        """
        return self._count(self.root, iter(sorted(keyset)))

    def _count(self, node, it):
        """
        Recursive function used by self.count().
        """
        try:
            data = next(it)
            try:
                matchnode = node.children[node.children.index(Node(data))]  # find first child with this data
                return self._count(matchnode, it)  # recurse
            except ValueError:  # not found
                return 0
        except StopIteration:
            if node.flag_last and node.value is not None:
                return len(node.value)
            else:
                return 0

    def iterget(self, keyset):
        """
        Return an iterator to the values associated to keyset.
        """
        return self._iterget(self.root, iter(sorted(keyset)))

    def _iterget(self, node, it):
        """
        Recursive function used by self.get().
        """
        try:
            data = next(it)
            try:
                matchnode = node.children[node.children.index(Node(data))]  # find first child with this data
                yield from self._iterget(matchnode, it)  # recurse
            except ValueError:  # not found
                return None
        except StopIteration:
            if node.flag_last:
                yield from node.value
