#!/usr/bin/env python3
# coding: utf-8
"""
Module settrie

Requires Python3

Version 0.1.3
Release date: 2015-05-22

Author: Márton Miháltz
Project home: https://github.com/mmihaltz/pysettrie

See README.md for more information.

Licensed under the GNU LESSER GENERAL PUBLIC LICENSE, Version 3.
See https://www.gnu.org/licenses/lgpl.html
"""

import sys
import sortedcontainers

__version__ = "0.1.3"


class SetTrie:
    """Set-trie container of sets for efficient supersets/subsets of a set
       over a set of sets queries.

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

    """

    class Node:
        """Node object used by SetTrie."""

        def __init__(self, data=None):
            # child nodes a.k.a. children
            self.children = sortedcontainers.SortedList()
            # if True, this is the last element of a set in the
            # set-trie use this to store user data (a set
            # element). Must be a hashable (i.e. hash(data) should
            # work) and comparable/orderable (i.e. data1 < data2
            # should work; see
            # https://wiki.python.org/moin/HowTo/Sorting/) type.
            self.flag_last = False
            self.data = data

        # comparison operators to support rich comparisons, sorting
        # etc. using self.data as key
        def __eq__(self, other): return self.data == other.data

        def __ne__(self, other): return self.data != other.data

        def __lt__(self, other): return self.data < other.data

        def __le__(self, other): return self.data <= other.data

        def __gt__(self, other): return self.data > other.data

        def __ge__(self, other): return self.data >= other.data

    def __init__(self, iterable=None):
        """Initialize this set-trie. If iterable is specified, set-trie is
           populated from its items.
        """
        self.root = SetTrie.Node()
        if iterable is not None:
            for s in iterable:
                self.add(s)

    def add(self, aset):
        """Add set aset to the container.  aset must be a sortable and
           iterable container type.
        """
        self._add(self.root, iter(sorted(aset)))

    @staticmethod
    def _add(node, it):
        """Recursive function used by self.insert().
           node is a SetTrieNode object
           it is an iterator over a sorted set"""
        try:
            data = next(it)
            nextnode = None
            try:
                # find first child with this data
                nextnode = node.children[node.children.index(
                    SetTrie.Node(data))]
            except ValueError:  # not found
                nextnode = SetTrie.Node(data)  # create new node
                node.children.add(nextnode)  # add to children & sort
            SetTrie._add(nextnode, it)  # recurse
        except StopIteration:  # end of set to add
            node.flag_last = True

    def contains(self, aset):
        """Returns True iff this set-trie contains set aset."""
        return self._contains(self.root, iter(sorted(aset)))

    def __contains__(self, aset):
        """Returns True iff this set-trie contains set aset.

           This method definition allows the use of the 'in' operator,
           for example:
           >>> t = SetTrie()
           >>> t.add( {1, 3} )
           >>> {1, 3} in t
           True
        """
        return self.contains(aset)

    @staticmethod
    def _contains(node, it):
        """Recursive function used by self.contains()."""
        try:
            data = next(it)
            try:
                # find first child with this data
                matchnode = node.children[node.children.index(
                    SetTrie.Node(data))]
                return SetTrie._contains(matchnode, it)  # recurse
            except ValueError:  # not found
                return False
        except StopIteration:
            return node.flag_last

    def hassuperset(self, aset):
        """Returns True iff there is at least one set in this set-trie that is
           the superset of set aset.
        """
        # TODO: if aset is not a set, convert it to a set first to
        # collapse multiply existing elements
        return SetTrie._hassuperset(self.root, list(sorted(aset)), 0)

    @staticmethod
    def _hassuperset(node, setarr, idx):
        """Used by hassuperset()."""
        if idx > len(setarr) - 1:
            return True
        found = False
        for child in node.children:
            # don't go to subtrees where current element cannot be
            if child.data > setarr[idx]:
                break
            if child.data == setarr[idx]:
                found = SetTrie._hassuperset(child, setarr, idx + 1)
            else:
                found = SetTrie._hassuperset(child, setarr, idx)
            if found:
                break
        return found

    def itersupersets(self, aset):
        """Return an iterator over all sets in this set-trie that are (proper
           or not proper) supersets of set aset.
        """
        path = []
        return SetTrie._itersupersets(self.root, list(sorted(aset)), 0, path)

    @staticmethod
    def _itersupersets(node, setarr, idx, path):
        """Used by itersupersets()."""
        if node.data is not None:
            path.append(node.data)
        if node.flag_last and idx > len(setarr) - 1:
            yield set(path)
        # we still have elements of aset to find
        if idx <= len(setarr) - 1:
            for child in node.children:
                # don't go to subtrees where current element cannot be
                if child.data > setarr[idx]:
                    break
                if child.data == setarr[idx]:
                    yield from SetTrie._itersupersets(child, setarr,
                                                      idx + 1, path)
                else:
                    yield from SetTrie._itersupersets(child, setarr,
                                                      idx, path)
        # no more elements to find: just traverse this subtree to get
        # all supersets
        else:
            for child in node.children:
                yield from SetTrie._itersupersets(child, setarr, idx, path)
        if node.data is not None:
            path.pop()

    def supersets(self, aset):
        """Return a list containing all sets in this set-trie that are
           supersets of set aset.
        """
        return list(self.itersupersets(aset))

    def hassubset(self, aset):
        """Return True iff there is at least one set in this set-trie that is
           the (proper or not proper) subset of set aset.
        """
        return SetTrie._hassubset(self.root, list(sorted(aset)), 0)

    @staticmethod
    def _hassubset(node, setarr, idx):
        """Used by hassubset()."""
        if node.flag_last:
            return True
        if idx > len(setarr) - 1:
            return False
        found = False
        try:
            c = node.children.index(SetTrie.Node(setarr[idx]))
            found = SetTrie._hassubset(node.children[c], setarr, idx + 1)
        except ValueError:
            pass
        if not found:
            return SetTrie._hassubset(node, setarr, idx + 1)
        else:
            return True

    def itersubsets(self, aset):
        """Return an iterator over all sets in this set-trie that are (proper
           or not proper) subsets of set aset.
        """
        path = []
        return SetTrie._itersubsets(self.root, list(sorted(aset)), 0, path)

    @staticmethod
    def _itersubsets(node, setarr, idx, path):
        """Used by itersubsets()."""
        if node.data is not None:
            path.append(node.data)
        if node.flag_last:
            yield set(path)
        for child in node.children:
            if idx > len(setarr) - 1:
                break
            if child.data == setarr[idx]:
                yield from SetTrie._itersubsets(child, setarr, idx + 1, path)
            else:
                # advance in search set until we find child (or get to
                # the end, or get to an element > child)
                jdx = idx + 1
                while jdx < len(setarr) and child.data >= setarr[jdx]:
                    if child.data == setarr[jdx]:
                        yield from SetTrie._itersubsets(child, setarr,
                                                        jdx, path)
                        break
                    jdx += 1
        if node.data is not None:
            path.pop()

    def subsets(self, aset):
        """Return a list of sets in this set-trie that are (proper or not
           proper) subsets of set aset.
        """
        return list(self.itersubsets(aset))

    def iter(self):
        """Returns an iterator over the sets stored in this set-trie (with
           pre-order tree traversal).  The sets are returned in sorted
           order with their elements sorted.
        """
        return self.__iter__()

    def __iter__(self):
        """Returns an iterator over the sets stored in this set-trie (with
           pre-order tree traversal).  The sets are returned in sorted
           order with their elements sorted.

           This method definition enables direct iteration over a
           SetTrie, for example:

           >>> t = SetTrie([{1, 2}, {2, 3, 4}])
           >>> for s in t:
           >>>   print(s)
           {1, 2}
           {2, 3, 4}
        """
        path = []
        yield from SetTrie._iter(self.root, path)

    @staticmethod
    def _iter(node, path):
        """Recursive function used by self.__iter__()."""
        if node.data is not None:
            path.append(node.data)
        if node.flag_last:
            yield set(path)
        for child in node.children:
            yield from SetTrie._iter(child, path)
        if node.data is not None:
            path.pop()

    def aslist(self):
        """Return an array containing all the sets stored in this set-trie.
           The sets are in sorted order with their elements sorted."""
        return list(self)

    def printtree(self, tabchr=' ', tabsize=2, stream=sys.stdout):
        """Print a mirrored 90-degree rotation of the nodes in this trie to
           stream (default: sys.stdout).  Nodes marked as flag_last
           are trailed by the '#' character.  tabchr and tabsize
           determine the indentation: at tree level n, n*tabsize
           tabchar characters will be used.
        """
        self._printtree(self.root, 0, tabchr, tabsize, stream)

    @staticmethod
    def _printtree(node, level, tabchr, tabsize, stream):
        """Used by self.printTree(), recursive preorder traverse and printing
           of trie node
        """
        print(str(node.data).rjust(len(repr(node.data)) + level *
                                   tabsize, tabchr) +
              ('#' if node.flag_last else ''),
              file=stream)
        for child in node.children:
            SetTrie._printtree(child, level + 1, tabchr, tabsize, stream)

    def __str__(self):
        """Returns str(self.aslist())."""
        return str(self.aslist())

    def __repr__(self):
        """Returns str(self.aslist())."""
        return str(self.aslist())


class SetTrieMap:
    """Mapping container for efficient storage of key-value pairs where
      the keys are sets.  Uses efficient trie
      implementation. Supports querying for values associated to
      subsets or supersets of stored key sets.

      Usage:
      ------
      >>> from settrie import SetTrieMap
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
    """

    class Node:
        """Node object used by SetTrieMap. You probably don't need to use it
           from the outside.
        """

        def __init__(self, data=None, value=None):
            # child nodes a.k.a. children
            self.children = sortedcontainers.SortedList()
            # if True, this is the last element of a key set store a
            # member element of the key set. Must be a hashable
            # (i.e. hash(data) should work) and comparable/orderable
            # (i.e. data1 < data2 should work; see
            # https://wiki.python.org/moin/HowTo/Sorting/) type.
            self.flag_last = False
            self.data = data
            # the value associated to the key set if flag_last ==
            # True, otherwise None
            self.value = None

        # comparison operators to support rich comparisons, sorting
        # etc. using self.data as key
        def __eq__(self, other): return self.data == other.data

        def __ne__(self, other): return self.data != other.data

        def __lt__(self, other): return self.data < other.data

        def __le__(self, other): return self.data <= other.data

        def __gt__(self, other): return self.data > other.data

        def __ge__(self, other): return self.data >= other.data

    def __init__(self, iterable=None):
        """Set up this SetTrieMap object.  If iterable is specified, it must
           be an iterable of (keyset, value) pairs from which set-trie
           is populated.
        """
        self.root = SetTrieMap.Node()
        if iterable is not None:
            for key, value in iterable:
                self.assign(key, value)

    def assign(self, akey, avalue):
        """Add key akey with associated value avalue to the container.
           akey must be a sortable and iterable container type."""
        self._assign(self.root, iter(sorted(akey)), avalue)

    @staticmethod
    def _assign(node, it, val):
        """Recursive function used by self.assign()."""
        try:
            data = next(it)
            nextnode = None
            try:
                # find first child with this data
                nextnode = node.children[node.children.index(
                    SetTrieMap.Node(data))]
            except ValueError:  # not found
                nextnode = SetTrieMap.Node(data)  # create new node
                node.children.add(nextnode)  # add to children & sort
            SetTrieMap._assign(nextnode, it, val)  # recurse
        except StopIteration:  # end of set to add
            node.flag_last = True
            node.value = val

    def contains(self, keyset):
        """Returns True iff this set-trie contains set keyset as a key."""
        return self._contains(self.root, iter(sorted(keyset)))

    def __contains__(self, keyset):
        """Returns True iff this set-trie contains set keyset as a key.  This
           method definition allows the use of the 'in' operator, for
           example:

           >>> t = SetTrieMap()
           >>> t.assign( {1, 3}, 'M' )
           >>> {1, 3} in t
           True
        """
        return self.contains(keyset)

    @staticmethod
    def _contains(node, it):
        """Recursive function used by self.contains()."""
        try:
            data = next(it)
            try:
                # find first child with this data
                matchnode = node.children[node.children.index(
                    SetTrieMap.Node(data))]
                return SetTrieMap._contains(matchnode, it)  # recurse
            except ValueError:  # not found
                return False
        except StopIteration:
            return node.flag_last

    def get(self, keyset, default=None):
        """Return the value associated to keyset if keyset is in this
           SetTrieMap, else default.
        """
        return self._get(self.root, iter(sorted(keyset)), default)

    @staticmethod
    def _get(node, it, default):
        """Recursive function used by self.get()."""
        try:
            data = next(it)
            try:
                # find first child with this data
                matchnode = node.children[node.children.index(
                    SetTrieMap.Node(data))]
                return SetTrieMap._get(matchnode, it, default)  # recurse
            except ValueError:  # not found
                return default
        except StopIteration:
            return (node.value if node.flag_last else default)

    def hassuperset(self, aset):
        """Returns True iff there is at least one key set in this SetTrieMap
           that is the superset of set aset.
        """
        return SetTrieMap._hassuperset(self.root, list(sorted(aset)), 0)

    @staticmethod
    def _hassuperset(node, setarr, idx):
        """Used by hassuperset()."""
        if idx > len(setarr) - 1:
            return True
        found = False
        for child in node.children:
            # don't go to subtrees where current element cannot be
            if child.data > setarr[idx]:
                break
            if child.data == setarr[idx]:
                found = SetTrieMap._hassuperset(child, setarr, idx + 1)
            else:
                found = SetTrieMap._hassuperset(child, setarr, idx)
            if found:
                break
        return found

    def itersupersets(self, aset, mode=None):
        """Return an iterator over all (keyset, value) pairs from this
           SetTrieMap for which set keyset is a superset (proper or
           not proper) of set aset.  If mode is not None, the
           following values are allowed:

           mode='keys': return an iterator over only the keysets that
                        are supersets of aset is returned
           mode='values': return an iterator over only the values that
                          are associated to keysets that are supersets
                          of aset

           If mode is neither of 'keys', 'values' or None, behavior is
           equivalent to mode=None.

        """
        path = []
        return SetTrieMap._itersupersets(self.root, list(sorted(aset)), 0,
                                         path, mode)

    @staticmethod
    def _itersupersets(node, setarr, idx, path, mode):
        """Used by itersupersets()."""
        if node.data is not None:
            path.append(node.data)
        if node.flag_last and idx > len(setarr) - 1:
            if mode == 'keys':
                yield set(path)
            elif mode == 'values':
                yield node.value
            else:
                yield (set(path), node.value)
        # we still have elements of aset to find
        if idx <= len(setarr) - 1:
            for child in node.children:
                # don't go to subtrees where current element cannot be
                if child.data > setarr[idx]:
                    break
                if child.data == setarr[idx]:
                    yield from SetTrieMap._itersupersets(child,
                                                         setarr, idx +
                                                         1, path,
                                                         mode)
                else:
                    yield from SetTrieMap._itersupersets(child,
                                                         setarr, idx,
                                                         path, mode)
        # no more elements to find: just traverse this subtree to get
        # all supersets
        else:
            for child in node.children:
                yield from SetTrieMap._itersupersets(child, setarr,
                                                     idx, path, mode)
        if node.data is not None:
            path.pop()

    def supersets(self, aset, mode=None):
        """Return a list containing pairs of (keyset, value) for which keyset
           is superset of set aset.

           Parameter mode: see documentation for itersupersets().
        """
        return list(self.itersupersets(aset, mode))

    def hassubset(self, aset):
        """Return True iff there is at least one set in this SetTrieMap that
           is the (proper or not proper) subset of set aset.
        """
        return SetTrieMap._hassubset(self.root, list(sorted(aset)), 0)

    @staticmethod
    def _hassubset(node, setarr, idx):
        """Used by hassubset()."""
        if node.flag_last:
            return True
        if idx > len(setarr) - 1:
            return False
        found = False
        try:
            c = node.children.index(SetTrieMap.Node(setarr[idx]))
            found = SetTrieMap._hassubset(node.children[c], setarr, idx + 1)
        except ValueError:
            pass
        if not found:
            return SetTrieMap._hassubset(node, setarr, idx + 1)
        else:
            return True

    def itersubsets(self, aset, mode=None):
        """Return an iterator over pairs (keyset, value) from this SetTrieMap
           for which keyset is (proper or not proper) subset of set aset.
           If mode is not None, the following values are allowed:

           mode='keys': return an iterator over only the keysets that
                        are subsets of aset is returned

           mode='values': return an iterator over only the values that
                          are associated to keysets that are subsets of aset

           If mode is neither of 'keys', 'values' or None, behavior is
           equivalent to mode=None.
        """
        path = []
        return SetTrieMap._itersubsets(self.root, list(sorted(aset)),
                                       0, path, mode)

    @staticmethod
    def _itersubsets(node, setarr, idx, path, mode):
        """Used by itersubsets()."""
        if node.data is not None:
            path.append(node.data)
        if node.flag_last:
            if mode == 'keys':
                yield set(path)
            elif mode == 'values':
                yield node.value
            else:
                yield (set(path), node.value)
        for child in node.children:
            if idx > len(setarr) - 1:
                break
            if child.data == setarr[idx]:
                yield from SetTrieMap._itersubsets(child, setarr,
                                                   idx + 1, path, mode)
            else:
                # advance in search set until we find child (or get to
                # the end, or get to an element > child)
                jdx = idx + 1
                while jdx < len(setarr) and child.data >= setarr[jdx]:
                    if child.data == setarr[jdx]:
                        yield from SetTrieMap._itersubsets(child,
                                                           setarr,
                                                           jdx, path,
                                                           mode)
                        break
                    jdx += 1
        if node.data is not None:
            path.pop()

    def subsets(self, aset, mode=None):
        """Return a list of (keyset, value) pairs from this set-trie
           for which keyset is (proper or not proper) subset of set aset.
           Parameter mode: see documentation for itersubsets().
        """
        return list(self.itersubsets(aset, mode))

    def iter(self, mode=None):
        """Returns an iterator to all (keyset, value) pairs stored in this
           SetTrieMap (using pre-order tree traversal).  The pairs are
           returned sorted to their keys, which are also sorted.  If
           mode is not None, the following values are allowed:

           mode='keys': return an iterator over only the keysets that
                        are subsets of aset

           mode='values': return an iterator over only the values that
                          are associated to keysets that are subsets
                          of aset

           If mode is neither of 'keys', 'values' or None, behavior is
           equivalent to mode=None.
        """
        path = []
        yield from SetTrieMap._iter(self.root, path, mode)

    def keys(self):
        """Alias for self.iter(mode='keys')."""
        return self.iter(mode='keys')

    def values(self):
        """Alias for self.iter(mode='values')."""
        return self.iter(mode='values')

    def items(self):
        """Alias for self.iter(mode=None)."""
        return self.iter(mode=None)

    def __iter__(self):
        """Same as self.iter(mode='keys')."""
        return self.keys()

    @staticmethod
    def _iter(node, path, mode):
        """Recursive function used by self.iter()."""
        if node.data is not None:
            path.append(node.data)
        if node.flag_last:
            if mode == 'keys':
                yield set(path)
            elif mode == 'values':
                yield node.value
            else:
                yield (set(path), node.value)
        for child in node.children:
            yield from SetTrieMap._iter(child, path, mode)
        if node.data is not None:
            path.pop()

    def aslist(self):
        """Return a list containing all the (keyset, value) pairs stored in
           this SetTrieMap.  The pairs are returned sorted to their
           keys, which are also sorted.
        """
        return list(self.iter())

    def printtree(self, tabchr=' ', tabsize=2, stream=sys.stdout):
        """Print a mirrored 90-degree rotation of the nodes in this SetTrieMap
           to stream (default: sys.stdout).  Nodes marked as flag_last
           are trailed by the '#' character.  tabchr and tabsize
           determine the indentation: at tree level n, n*tabsize
           tabchar characters will be used.  Associated values are
           printed after ': ' trailing flag_last=True nodes.
        """
        self._printtree(self.root, 0, tabchr, tabsize, stream)

    @staticmethod
    def _printtree(node, level, tabchr, tabsize, stream):
        """Used by self.printTree(), recursive preorder traverse and printing
           of trie node
        """
        print((str(node.data).rjust(len(repr(node.data)) + level * tabsize,
                                    tabchr) +
               (': {}'.format(repr(node.value)) if
                node.flag_last else
                '')),
              file=stream)
        for child in node.children:
            SetTrieMap._printtree(child, level + 1, tabchr, tabsize, stream)

    def __str__(self):
        """Returns str(self.aslist())."""
        return str(self.aslist())

    def __repr__(self):
        """Returns str(self.aslist())."""
        return str(self.aslist())


class SetTrieMultiMap:
    """Like SetTrieMap, but the associated values are lists that can have
       multiple items added.

       Usage:
       ------
       >>> from settrie import SetTrieMultiMap
       >>> m.assign({1,2}, 'A')
       >>> m.assign({1,2,3}, 'B')
       >>> m.assign({1,2,3}, 'BB')
       >>> m.assign({2,3,5}, 'C')
       >>> m
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

    """

    class Node:
        """Node object used by SetTrieMultiMap. You probably don't need to
           use it from the outside.
        """

        def __init__(self, data=None, value=None):
            # child nodes a.k.a. children
            self.children = sortedcontainers.SortedList()
            # if True, this is the last element of a key set store a
            # member element of the key set. Must be a hashable
            # (i.e. hash(data) should work) and comparable/orderable
            # (i.e. data1 < data2 should work; see
            # https://wiki.python.org/moin/HowTo/Sorting/) type.
            self.flag_last = False
            self.data = data
            # the list of values associated to the key set if
            # flag_last == True, otherwise None
            self.value = None

        # comparison operators to support rich comparisons, sorting
        # etc. using self.data as key
        def __eq__(self, other): return self.data == other.data

        def __ne__(self, other): return self.data != other.data

        def __lt__(self, other): return self.data < other.data

        def __le__(self, other): return self.data <= other.data

        def __gt__(self, other): return self.data > other.data

        def __ge__(self, other): return self.data >= other.data

    def __init__(self, iterable=None):
        """Set up this SetTrieMultiMap object.  If iterable is specified, it
           must be an iterable of (keyset, value) pairs from which
           set-trie is populated; key may be repeated, all associated
           values will be stored.
        """
        self.root = SetTrieMultiMap.Node()
        if iterable is not None:
            for key, value in iterable:
                self.assign(key, value)

    def assign(self, akey, avalue):
        """Add key akey with associated value avalue to the container.  akey
           must be a sortable and iterable container type.  If akey is
           an already exising key, avalue will be appended to the
           associated values.

           Multiple occurrences of the same value for the same key are
           preserved.

           Returns number of values associated to akey after the
           assignment, ie. returns 1 if akey was a nonexisting key
           before this function call, returns (number of items before
           call + 1) if akey was an already existing key.
        """
        valcnt = [0]
        self._assign(self.root, iter(sorted(akey)), avalue, valcnt)
        return valcnt[0]

    @staticmethod
    def _assign(node, it, val, valcnt):
        """Recursive function used by self.assign()."""
        try:
            data = next(it)
            nextnode = None
            try:
                # find first child with this data
                nextnode = node.children[node.children.index(
                    SetTrieMultiMap.Node(data))]
            except ValueError:  # not found
                nextnode = SetTrieMultiMap.Node(data)  # create new node
                node.children.add(nextnode)  # add to children & sort
            SetTrieMultiMap._assign(nextnode, it, val, valcnt)  # recurse
        except StopIteration:  # end of set to add
            node.flag_last = True
            if node.value is None:
                node.value = []
            node.value.append(val)
            # return # of values for key after this assignment
            valcnt[0] = len(node.value)

    def contains(self, keyset):
        """Returns True iff this set-trie contains set keyset as a key."""
        return self._contains(self.root, iter(sorted(keyset)))

    def __contains__(self, keyset):
        """Returns True iff this set-trie contains set keyset as a key.  This
           method definition allows the use of the 'in' operator, for
           example:
           >>> t = SetTrieMap()
           >>> t.assign( {1, 3}, 'M' )
           >>> {1, 3} in t
           True
        """
        return self.contains(keyset)

    @staticmethod
    def _contains(node, it):
        """Recursive function used by self.contains()."""
        try:
            data = next(it)
            try:
                # find first child with this data
                matchnode = node.children[node.children.index(
                    SetTrieMultiMap.Node(data))]
                return SetTrieMap._contains(matchnode, it)  # recurse
            except ValueError:  # not found
                return False
        except StopIteration:
            return node.flag_last

    def count(self, keyset):
        """Returns the number of values associated to keyset. If keyset is
           unknown, returns 0.
        """
        return self._count(self.root, iter(sorted(keyset)))

    @staticmethod
    def _count(node, it):
        """Recursive function used by self.count()."""
        try:
            data = next(it)
            try:
                # find first child with this data
                matchnode = node.children[node.children.index(
                    SetTrieMultiMap.Node(data))]
                return SetTrieMultiMap._count(matchnode, it)  # recurse
            except ValueError:  # not found
                return 0
        except StopIteration:
            if node.flag_last and node.value is not None:
                return len(node.value)
            else:
                return 0

    def iterget(self, keyset):
        """Return an iterator to the values associated to keyset."""
        return self._iterget(self.root, iter(sorted(keyset)))

    @staticmethod
    def _iterget(node, it):
        """Recursive function used by self.get()."""
        try:
            data = next(it)
            try:
                # find first child with this data
                matchnode = node.children[node.children.index(
                    SetTrieMultiMap.Node(data))]
                yield from SetTrieMultiMap._iterget(matchnode, it)  # recurse
            except ValueError:  # not found
                return None
        except StopIteration:
            if node.flag_last:
                yield from node.value

    def get(self, keyset, default=None):
        """Return a list of values associated to keyset if keyset is in this
           SetTrieMultiMap, else default.
        """
        return self._get(self.root, iter(sorted(keyset)), default)

    @staticmethod
    def _get(node, it, default):
        """Recursive function used by self.get()."""
        try:
            data = next(it)
            try:
                # find first child with this data
                matchnode = node.children[node.children.index(
                    SetTrieMultiMap.Node(data))]
                return SetTrieMultiMap._get(matchnode, it, default)  # recurse
            except ValueError:  # not found
                return default
        except StopIteration:
            return (node.value if node.flag_last else default)

    def hassuperset(self, aset):
        """Returns True iff there is at least one key set in this
           SetTrieMultiMap that is the superset of set aset.
        """
        return SetTrieMap._hassuperset(self.root, list(sorted(aset)), 0)

    def itersupersets(self, aset, mode=None):
        """Return an iterator over all (keyset, value) pairs from this
           SetTrieMultiMap for which set keyset is a superset (proper
           or not proper) of set aset.  If mode is not None, the
           following values are allowed:

           mode='keys': return an iterator over only the keysets that
                        are supersets of aset is returned
           mode='values': return an iterator over only the values that
                          are associated to keysets that are supersets
                          of aset

           If mode is neither of 'keys', 'values' or None, behavior is
           equivalent to mode=None.

        """
        path = []
        return SetTrieMultiMap._itersupersets(self.root,
                                              list(sorted(aset)), 0,
                                              path, mode)

    @staticmethod
    def _itersupersets(node, setarr, idx, path, mode):
        """Used by itersupersets()."""
        if node.data is not None:
            path.append(node.data)
        if node.flag_last and idx > len(setarr) - 1:
            if mode == 'keys':
                yield set(path)
            elif mode == 'values':
                yield from node.value
            else:
                yield from [(set(path), val) for val in node.value]
        if idx <= len(setarr) - 1:  # we still have elements of aset to find
            for child in node.children:
                # don't go to subtrees where current element cannot be
                if child.data > setarr[idx]:
                    break
                if child.data == setarr[idx]:
                    yield from SetTrieMultiMap._itersupersets(child,
                                                              setarr,
                                                              idx + 1,
                                                              path, mode)
                else:
                    yield from SetTrieMultiMap._itersupersets(child,
                                                              setarr,
                                                              idx,
                                                              path,
                                                              mode)
        # no more elements to find: just traverse this subtree to get
        # all supersets
        else:
            for child in node.children:
                yield from SetTrieMultiMap._itersupersets(child,
                                                          setarr, idx,
                                                          path, mode)
        if node.data is not None:
            path.pop()

    def supersets(self, aset, mode=None):
        """Return a list containing pairs of (keyset, value) for which keyset
           is superset of set aset.

           Parameter mode: see documentation for itersupersets().
        """
        return list(self.itersupersets(aset, mode))

    def hassubset(self, aset):
        """Return True iff there is at least one set in this SetTrieMultiMap
           that is the (proper or not proper) subset of set aset.
        """
        return SetTrieMultiMap._hassubset(self.root, list(sorted(aset)), 0)

    @staticmethod
    def _hassubset(node, setarr, idx):
        """Used by hassubset()."""
        if node.flag_last:
            return True
        if idx > len(setarr) - 1:
            return False
        found = False
        try:
            c = node.children.index(SetTrieMultiMap.Node(setarr[idx]))
            found = SetTrieMultiMap._hassubset(
                node.children[c], setarr, idx + 1)
        except ValueError:
            pass
        if not found:
            return SetTrieMultiMap._hassubset(node, setarr, idx + 1)
        else:
            return True

    def itersubsets(self, aset, mode=None):
        """Return an iterator over pairs (keyset, value) from this
           SetTrieMultiMap for which keyset is (proper or not proper)
           subset of set aset.  If mode is not None, the following
           values are allowed:

           mode='keys': return an iterator over only the keysets that
                        are subsets of aset is returned
           mode='values': return an iterator over only the values that
                          are associated to keysets that are subsets
                          of aset

           If mode is neither of 'keys', 'values' or None, behavior is
           equivalent to mode=None.
        """
        path = []
        return SetTrieMultiMap._itersubsets(self.root,
                                            list(sorted(aset)), 0,
                                            path, mode)

    @staticmethod
    def _itersubsets(node, setarr, idx, path, mode):
        """Used by itersubsets()."""
        if node.data is not None:
            path.append(node.data)
        if node.flag_last:
            if mode == 'keys':
                yield set(path)
            elif mode == 'values':
                yield from node.value
            else:
                yield from [(set(path), val) for val in node.value]
        for child in node.children:
            if idx > len(setarr) - 1:
                break
            if child.data == setarr[idx]:
                yield from SetTrieMultiMap._itersubsets(child, setarr,
                                                        idx + 1, path,
                                                        mode)
            else:
                # advance in search set until we find child (or get to
                # the end, or get to an element > child)
                jdx = idx + 1
                while jdx < len(setarr) and child.data >= setarr[jdx]:
                    if child.data == setarr[jdx]:
                        yield from SetTrieMultiMap._itersubsets(child,
                                                                setarr,
                                                                jdx,
                                                                path,
                                                                mode)
                        break
                    jdx += 1
        if node.data is not None:
            path.pop()

    def subsets(self, aset, mode=None):
        """Return a list of (keyset, value) pairs
           for which keyset is (proper or not proper) subset of set aset.
           Parameter mode: see documentation for itersubsets().
        """
        return list(self.itersubsets(aset, mode))

    def iter(self, mode=None):
        """Returns an iterator to all (keyset, value) pairs stored in this
           SetTrieMultiMap (using pre-order tree traversal).  The
           pairs are returned sorted to their keys, which are also
           sorted.  If mode is not None, the following values are
           allowed:

           mode='keys': return an iterator over only the keysets that
                        are subsets of aset
           mode='values': return an iterator over only the values that
                          are associated to keysets that are subsets
                          of aset

           If mode is neither of 'keys', 'values' or None, behavior is
           equivalent to mode=None.
        """
        path = []
        yield from SetTrieMultiMap._iter(self.root, path, mode)

    def keys(self):
        """Alias for self.iter(mode='keys')."""
        return self.iter(mode='keys')

    def values(self):
        """Alias for self.iter(mode='values')."""
        return self.iter(mode='values')

    def items(self):
        """Alias for self.iter(mode=None)."""
        return self.iter(mode=None)

    def __iter__(self):
        """Same as self.iter(mode='keys')."""
        return self.keys()

    @staticmethod
    def _iter(node, path, mode):
        """Recursive function used by self.iter()."""
        if node.data is not None:
            path.append(node.data)
        if node.flag_last:
            if mode == 'keys':
                yield set(path)
            elif mode == 'values':
                yield from node.value
            else:
                yield from [(set(path), val) for val in node.value]
        for child in node.children:
            yield from SetTrieMultiMap._iter(child, path, mode)
        if node.data is not None:
            path.pop()

    def aslist(self):
        """Return a list containing all the (keyset, value) pairs stored in
           this SetTrieMap.  The pairs are returned sorted to their
           keys, which are also sorted.
        """
        return list(self.iter())

    def printtree(self, tabchr=' ', tabsize=2, stream=sys.stdout):
        """Print a mirrored 90-degree rotation of the nodes in this SetTrieMap
           to stream (default: sys.stdout).  Nodes marked as flag_last
           are trailed by the '#' character.  tabchr and tabsize
           determine the indentation: at tree level n, n*tabsize
           tabchar characters will be used.  Associated values are
           printed after ': ' trailing flag_last=True nodes.
        """
        self._printtree(self.root, 0, tabchr, tabsize, stream)

    @staticmethod
    def _printtree(node, level, tabchr, tabsize, stream):
        """Used by self.printTree(), recursive preorder traverse and printing
           of trie node
        """
        print((str(node.data).rjust(len(repr(node.data)) + level * tabsize,
                                    tabchr) +
               (': {}'.format(repr(node.value)) if node.flag_last else '')),
              file=stream)
        for child in node.children:
            SetTrieMap._printtree(child, level + 1, tabchr, tabsize, stream)

    def __str__(self):
        """Returns str(self.aslist())."""
        return str(self.aslist())

    def __repr__(self):
        """Returns str(self.aslist())."""
        return str(self.aslist())
