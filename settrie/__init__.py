#!/usr/bin/env python3
# coding: utf-8
"""
Module settrie

Requires Python3

Version 0.1.5
Release date: 2019-11-30

Author: Márton Miháltz
Project home: https://github.com/mmihaltz/pysettrie
Version 0.1.4: Refactoring by Balázs Indig
Version 0.1.5: Optimization and further refactoring by Gregory Morse

See README.md for more information.

Licensed under the GNU LESSER GENERAL PUBLIC LICENSE, Version 3.
See https://www.gnu.org/licenses/lgpl.html
"""

import sys
import sortedcontainers
import bisect
from collections import deque

__version__ = "0.1.5"

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
    
    def __init__(self, iterable=None, recursion=False, generator=False):
        """Initialize this set-trie. If iterable is specified, set-trie is
           populated from its items.
        """
        self.total_nodes = 0
        self._generator = generator
        self._YieldLast = SetTrie._yield_last if self._generator else SetTrie._return_last
        if recursion is True: self._doiter, self._hassuperset, self._doitersupersets, self._hassubset, self._doitersubsets, self._printtree = SetTrie._iter_recurse, SetTrie._hassuperset_recurse, SetTrie._itersupersets_recurse, SetTrie._hassubset_recurse, SetTrie._itersubsets_recurse, SetTrie._printtree_recurse
        elif recursion is False: self._doiter, self._hassuperset, self._doitersupersets, self._hassubset, self._doitersubsets, self._printtree = SetTrie._iter_stack_gen, SetTrie._hassuperset_stack_gen, SetTrie._itersupersets_stack_gen, SetTrie._hassubset_stack_item, SetTrie._itersubsets_stack_item, SetTrie._printtree_stack_gen
        else: self._doiter, self._hassuperset, self._doitersupersets, self._hassubset, self._doitersubsets, self._printtree = SetTrie._iter_stack_item, SetTrie._hassuperset_stack_item, SetTrie._itersupersets_stack_item, SetTrie._hassubset_stack_item, SetTrie._itersubsets_stack_item, SetTrie._printtree_stack_item
        if not hasattr(self, '_NodeTemplate'): self._NodeTemplate = SetTrie.Node
        if not hasattr(self, '_ValueCallback'): self._ValueCallback = self._YieldLast
        if not hasattr(self, '_PrintCallback'): self._PrintCallback = SetTrie._print_last
        self.root = self._NodeTemplate()
        if iterable is not None:
            for s in iterable:
                self.add(s)

    def add(self, aset):
        """Add set aset to the container.  aset must be a sortable and
           iterable container type.
        """
        _, notadd = SetTrie._add(self.root, iter(sorted(aset)), self._NodeTemplate)
        if not notadd: self.total_nodes += 1

    @staticmethod
    def _add(node, it, NodeTemplate):
        """Recursive function used by self.add().
           node is a SetTrieNode object
           it is an iterator over a sorted set"""
        for data in it:
            nextnode, childs = NodeTemplate(data), node.children  # create new node
            # find first child with this data
            idx = childs.bisect_left(nextnode)
            if len(childs) <= idx:
                childs.add(nextnode) # add to children & sort
                node = nextnode
            else:
                testnode = childs[idx]
                if testnode != nextnode:
                    childs.add(nextnode)  # add to children & sort   
                    node = nextnode
                else: node = testnode
        ret = (node, node.flag_last)
        node.flag_last = True  # end of set to add
        return ret
    
    def remove(self, aset):
        """Remove set aset from the container.  aset must be a sortable and
           iterable container type.
        """
        if SetTrie._remove(self.root, iter(sorted(aset)), self._NodeTemplate):
            self.total_nodes -= 1
    
    @staticmethod
    def _remove(node, it, NodeTemplate):
        """Recursive function used by self.remove().
           node is a SetTrieNode object
           it is an iterator over a sorted set"""
        nodes = list()
        for data in it:
            nodes.append(node)  # add to post-recursion stack
            nextnode, childs = NodeTemplate(data), node.children
            idx = childs.bisect_left(nextnode)
            if len(childs) <= idx: return False #not in container
            node = childs[idx]
            if node != nextnode: return False # not in container
        if not node.flag_last: return False
        node.flag_last = False # final node set to off
        nextnode = node
        for node in reversed(nodes): #  walk backwards through child nodes
            if nextnode.flag_last or len(nextnode.children) != 0: break
            node.children.remove(nextnode)
            nextnode = node
        return True

    def contains(self, aset):
        """Returns True iff this set-trie contains set aset."""
        return SetTrie._contains(self.root, iter(sorted(aset)), self._NodeTemplate) is not None

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
    def _contains(node, it, NodeTemplate):
        """Recursive function used by self.contains()."""
        for data in it:
            # find first child with this data
            curnode, childs = NodeTemplate(data), node.children
            idx = childs.bisect_left(curnode)
            if len(childs) <= idx: return None
            node = childs[idx]
            if node != curnode: return None  # not found
        return node if node.flag_last else None

    def hassuperset(self, aset):
        """Returns True iff there is at least one set in this set-trie that is
           the superset of set aset.
        """
        # TODO: if aset is not a set, convert it to a set first to
        # collapse multiply existing elements
        return self._hassuperset(self.root, tuple(sorted(aset)), 0, self._NodeTemplate)

    @staticmethod
    def _hassuperset_recurse(node, setarr, idx, NodeTemplate):
        """Used by hassuperset()."""
        if idx > len(setarr) - 1:
            return node.flag_last or len(node.children) != 0
        found = False
        curnode, childs = NodeTemplate(setarr[idx]), node.children
        i = childs.bisect_left(curnode)
        for child in childs.islice(0, i):
            if SetTrie._hassuperset_recurse(child, setarr, idx, NodeTemplate): return True
        if len(childs) > i:
            checknode = childs[i]
            if curnode == checknode:
                found = SetTrie._hassuperset_recurse(checknode, setarr, idx + 1, NodeTemplate)
        return found
    @staticmethod
    def _hassuperset_stack_item(node, setarr, idx, NodeTemplate):
        """Used by hassuperset()."""
        len_s = len(setarr)
        if idx > len_s - 1:
            return node.flag_last or len(node.children) != 0
        s = deque()
        s.append((node, idx))
        while s:
            node, idx = s.pop()
            curnode, childs = NodeTemplate(setarr[idx]), node.children
            i = childs.bisect_left(curnode)
            s.extend((x, idx) for x in childs.islice(0, i))
            if len(childs) > i:
                checknode = childs[i]
                if curnode == checknode:
                    if idx + 1 > len_s - 1: return True
                    s.append((checknode, idx + 1))
        return False
    @staticmethod
    def _hassuperset_stack_gen(node, setarr, idx, NodeTemplate):
        """Used by hassuperset()."""
        len_s = len(setarr)
        if idx > len_s - 1:
            return node.flag_last or len(node.children) != 0
        s = deque()
        s.append((iter((node,)), idx))
        while s:
            it, idx = s[-1]
            node = next(it, s)
            if node is s:
                s.pop()
                continue
            curnode, childs = NodeTemplate(setarr[idx]), node.children
            i = childs.bisect_left(curnode)
            s.append((childs.islice(0, i), idx))
            if len(childs) > i:
                checknode = childs[i]
                if curnode == checknode:
                    if idx + 1 > len_s - 1: return True
                    s.append((iter((checknode,)), idx + 1))
        return False

    def _itersupersets(self, aset):
        return self._doitersupersets(self.root, tuple(sorted(aset)), 0, set(), None if self._generator else list(), self._NodeTemplate, self._ValueCallback)

    @staticmethod
    def _itersupersets_recurse(node, setarr, idx, path, res, NodeTemplate, ValueCallback):
        """Used by itersupersets()."""
        if idx > len(setarr) - 1:
            # no more elements to find: just traverse this subtree to get
            # all supersets
            r = SetTrie._iter_recurse(node, path, res, ValueCallback)
            if not res is None: yield next(r)
            else: yield from r
            return
        if node.data is not None:
            path.add(node.data)
        curnode, childs = NodeTemplate(setarr[idx]), node.children
        i = childs.bisect_left(curnode)
        for child in childs.islice(0, i):
            r = SetTrie._itersupersets_recurse(child, setarr, idx, path, res, NodeTemplate, ValueCallback)
            if not res is None: next(r)
            else: yield from r
        if len(childs) > i:
            checknode = childs[i]
            if curnode == checknode:
                r = SetTrie._itersupersets_recurse(checknode, setarr, idx + 1, path, res, NodeTemplate, ValueCallback)
                if not res is None: next(r)
                else: yield from r
        if node.data is not None:
            path.remove(node.data)
        if not res is None: yield res
    @staticmethod
    def _itersupersets_stack_item(node, setarr, idx, path, res, NodeTemplate, ValueCallback):
        """Used by itersupersets()."""
        len_s = len(setarr)
        if idx > len_s - 1:
            # no more elements to find: just traverse this subtree to get
            # all supersets
            if not res is None: yield next(SetTrie._iter_stack_item(node, path, res, ValueCallback))
            else: yield from SetTrie._iter_stack_item(node, path, res, ValueCallback)
            return
        s = deque()
        s.append((node, idx))
        while s:
            node, idx = s.pop()
            if node is None:
                path.remove(idx)
                continue
            if idx > len_s - 1:
                r = SetTrie._iter_stack_item(node, path, res, ValueCallback)
                if not res is None: next(r)
                else: yield from r
                continue
            if not node.data is None:
                path.add(node.data)
                s.append((None, node.data))
            curnode, childs = NodeTemplate(setarr[idx]), node.children
            i = childs.bisect_left(curnode)
            if len(childs) > i:
                checknode = childs[i]
                if curnode == checknode:
                    s.append((checknode, idx + 1))
            s.extend((x, idx) for x in childs.islice(0, i, True))
        if not res is None: yield res
    @staticmethod
    def _itersupersets_stack_gen(node, setarr, idx, path, res, NodeTemplate, ValueCallback):
        """Used by itersupersets()."""
        len_s = len(setarr)
        if idx > len_s - 1:
            # no more elements to find: just traverse this subtree to get
            # all supersets
            if not res is None: yield next(SetTrie._iter_stack_item(node, path, res, ValueCallback))
            else: yield from SetTrie._iter_stack_item(node, path, res, ValueCallback)
            return
        s = deque()
        s.append((node.data, iter((node,)), idx))
        while s:
            lastpath, it, idx = s[-1]
            node = next(it, s)
            if node is s:
                if not lastpath is None: path.remove(lastpath)
                s.pop()
                continue
            if idx > len_s - 1:
                r = SetTrie._iter_stack_item(node, path, res, ValueCallback)
                if not res is None: next(r)
                else: yield from r
                continue
            if not node.data is None:
                path.add(node.data)
            curnode, childs = NodeTemplate(setarr[idx]), node.children
            i = childs.bisect_left(curnode)
            if len(childs) > i:
                checknode = childs[i]
                if curnode == checknode:
                    s.append((node.data, iter((checknode,)), idx + 1))
                    s.append((None, childs.islice(0, i), idx))
                else:
                    s.append((node.data, childs.islice(0, i), idx))
            else:
                s.append((node.data, childs.islice(0, i), idx))
        if not res is None: yield res
        
    def itersupersets(self, aset):
        """Return an iterator over all sets in this set-trie that are (proper
           or not proper) supersets of set aset.
        """
        return self._make_generator(self._itersupersets(aset))
    def supersets(self, aset):
        """Return a list containing all sets in this set-trie that are
           supersets of set aset.
        """
        return self._make_list(self._itersupersets(aset))

    def hassubset(self, aset):
        """Return True iff there is at least one set in this set-trie that is
           the (proper or not proper) subset of set aset.
        """
        return self._hassubset(self.root, tuple(sorted(aset)), 0, self._NodeTemplate)

    @staticmethod
    def _hassubset_recurse(node, setarr, idx, NodeTemplate):
        """Used by hassubset()."""
        if node.flag_last:
            return True
        len_s = len(setarr)
        if idx > len_s - 1:
            return False
        curnode, childs = NodeTemplate(setarr[idx]), node.children
        i = childs.bisect_left(curnode)
        if len(childs) > i:
            checknode = childs[i]
            if curnode == checknode:
                i += 1
                if SetTrie._hassubset_recurse(checknode, setarr, idx + 1, NodeTemplate): return True
            for child in childs.islice(i):
                jdx = bisect.bisect_left(setarr, child.data, idx + 1)
                if jdx < len_s and child.data == setarr[jdx]:
                    if SetTrie._hassubset_recurse(child, setarr, jdx + 1, NodeTemplate): return True
                    idx = jdx
                else: idx = jdx - 1
        return False

    @staticmethod
    def _hassubset_stack_item(node, setarr, idx, NodeTemplate):
        """Used by hassubset()."""
        len_s = len(setarr)
        s = deque()
        s.append((node, idx))
        while s:
            node, idx = s.pop()
            if node.flag_last:
                return True
            if idx > len_s - 1:
                continue
            curnode, childs = NodeTemplate(setarr[idx]), node.children
            i = childs.bisect_left(curnode)
            if len(childs) > i:
                checknode = childs[i]
                if curnode == checknode:
                    i += 1
                    s.append((checknode, idx + 1))
                for child in childs.islice(i):
                    jdx = bisect.bisect_left(setarr, child.data, idx + 1)
                    if jdx < len_s and child.data == setarr[jdx]:
                        s.append((child, jdx + 1))
                        idx = jdx
                    else: idx = jdx - 1
        return False

    def _itersubsets(self, aset):
        return self._doitersubsets(self.root, tuple(sorted(aset)), 0, set(), None if self._generator else list(), self._NodeTemplate, self._ValueCallback)

    @staticmethod
    def _itersubsets_recurse(node, setarr, idx, path, res, NodeTemplate, ValueCallback):
        """Used by itersubsets()."""
        if node.data is not None:
            path.add(node.data)
        if node.flag_last:
            if not res is None: ValueCallback(path, node, res)
            else: yield from ValueCallback(path, node, res)
        len_s = len(setarr)
        if idx <= len_s - 1:
            curnode, childs = NodeTemplate(setarr[idx]), node.children
            i = childs.bisect_left(curnode)
            if len(childs) > i:
                checknode = childs[i]
                if curnode == checknode:
                    i += 1
                    r = SetTrie._itersubsets_recurse(checknode, setarr, idx + 1, path, res, NodeTemplate, ValueCallback)
                    if not res is None: next(r)
                    else: yield from r
                for child in childs.islice(i):
                    jdx = bisect.bisect_left(setarr, child.data, idx + 1)
                    if jdx < len_s and child.data == setarr[jdx]:
                        r = SetTrie._itersubsets_recurse(child, setarr, jdx + 1, path, res, NodeTemplate, ValueCallback)
                        if not res is None: next(r)
                        else: yield from r
                        idx = jdx
                    else: idx = jdx - 1
        if node.data is not None:
            path.remove(node.data)
        if not res is None: yield res

    @staticmethod
    def _itersubsets_stack_item(node, setarr, idx, path, res, NodeTemplate, ValueCallback):
        """Used by itersubsets()."""
        len_s = len(setarr)
        s = deque()
        s.append((node, idx))
        while s:
            node, idx = s.pop()
            if node is None:
                path.remove(idx)
                continue
            if node.data is not None:
                path.add(node.data)
                s.append((None, node.data))
            if node.flag_last:
                if not res is None: ValueCallback(path, node, res)
                else: yield from ValueCallback(path, node, res)
            if idx <= len_s - 1:
                curnode, childs = NodeTemplate(setarr[idx]), node.children
                i = childs.bisect_left(curnode)
                if len(childs) > i:
                    checknode = childs[i]
                    iseq = curnode == checknode
                    if iseq:
                        i += 1
                    mx = len_s
                    for child in childs.islice(i, None, True):
                        jdx = bisect.bisect_left(setarr, child.data, idx + 1, mx)
                        if jdx < len_s and child.data == setarr[jdx]:
                            s.append((child, jdx + 1))
                            mx = jdx + 1
                        else: mx = jdx
                    if iseq:
                        s.append((checknode, idx + 1))
        if not res is None: yield res

    def itersubsets(self, aset):
        """Return an iterator over all sets in this set-trie that are (proper
           or not proper) subsets of set aset.
        """
        return self._make_generator(self._itersubsets(aset))
    def subsets(self, aset):
        """Return a list of sets in this set-trie that are (proper or not
           proper) subsets of set aset.
        """
        return self._make_list(self._itersubsets(aset))

    def _iter(self):
        return self._doiter(self.root, set(), None if self._generator else list(), self._ValueCallback)
        
    def iter(self):
        """Returns an iterator over the sets stored in this set-trie (with
           pre-order tree traversal).  The sets are returned in sorted
           order with their elements sorted.
        """
        #yield from SetTrie._iterold(self.root, path)
        return self._make_generator(self._iter())
        
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
        return self._make_generator(self._doiter(self.root, set(), None if self._generator else list(), self._YieldLast))
            
    @staticmethod
    def _iter_recurse(node, path, res, ValueCallback):
        """Recursive function used by self.__iter__()."""
        if node.data is not None:
            path.add(node.data)
        if node.flag_last:
            if not res is None: ValueCallback(path, node, res)
            else: yield from ValueCallback(path, node, res)
        for child in node.children:
            if not res is None: next(SetTrie._iter_recurse(child, path, res, ValueCallback))
            else: yield from SetTrie._iter_recurse(child, path, res, ValueCallback)
        if node.data is not None:
            path.remove(node.data)
        if not res is None: yield res
    @staticmethod
    def _iter_stack_item(node, path, res, ValueCallback):
        """Non-recursive stack-based function used by self.__iter__()."""
        s = deque()
        if node.data is not None:
            s.append(node.data)
            path.add(node.data)
        s.extend(reversed(node.children))
        if node.flag_last:
            if not res is None: ValueCallback(path, node, res)
            else: yield from ValueCallback(path, node, res)
        while s:
            node = s.pop()
            if not isinstance(node, (SetTrie.Node, SetTrieMap.NodeWithValue)):
                path.remove(node)
                continue
            path.add(node.data)
            if node.flag_last:
                if not res is None: ValueCallback(path, node, res)
                else: yield from ValueCallback(path, node, res)
            s.append(node.data)
            s.extend(reversed(node.children))
        if not res is None: yield res
    @staticmethod
    def _iter_stack_gen(node, path, res, ValueCallback):
        """Non-recursive stack-based function used by self.__iter__()."""
        s = deque()
        if node.data is not None:
            path.add(node.data)
        s.append((node.data, iter(node.children)))
        if node.flag_last:
            if not res is None: ValueCallback(path, node, res)
            else: yield from ValueCallback(path, node, res)
        while s:
            (lastpath, it) = s[-1]
            node = next(it, s)
            if node is s:
                if lastpath is not None: path.remove(lastpath)
                s.pop()
                continue
            path.add(node.data)
            if node.flag_last:
                if not res is None: ValueCallback(path, node, res)
                else: yield from ValueCallback(path, node, res)
            s.append((node.data, iter(node.children)))
        if not res is None: yield res
        
    def aslist(self):
        """Return an array containing all the sets stored in this set-trie.
           The sets are in sorted order with their elements sorted."""
        return self._make_list(self._iter())

    def empty(self):
        return len(self.root.children) == 0
    
    @staticmethod
    def _yield_last(path, _, res): yield set(path)
    @staticmethod
    def _return_last(path, _, res): res.append(set(path))
    
    @staticmethod
    def _print_last(node): return '#' if node.flag_last else ''
    
    def _make_generator(self, l): return l if self._generator else iter(next(l))
    def _make_list(self, l): return list(l) if self._generator else next(l)
        
    def printtree(self, tabchr=' ', tabsize=2, stream=sys.stdout):
        """Print a mirrored 90-degree rotation of the nodes in this trie to
           stream (default: sys.stdout).  Nodes marked as flag_last
           are trailed by the '#' character.  tabchr and tabsize
           determine the indentation: at tree level n, n*tabsize
           tabchar characters will be used.
        """
        self._printtree(self.root, 0, tabchr, tabsize, stream, self._PrintCallback)

    @staticmethod
    def _printtree_recurse(node, level, tabchr, tabsize, stream, PrintCallback):
        """Used by self.printTree(), recursive preorder traverse and printing
           of trie node
        """
        print(str(node.data).rjust(len(repr(node.data)) + level *
                                   tabsize, tabchr) +
              PrintCallback(node),
              file=stream)
        for child in node.children:
            SetTrie._printtree_recurse(child, level + 1, tabchr, tabsize, stream, PrintCallback)
    @staticmethod
    def _printtree_stack_item(node, level, tabchr, tabsize, stream, PrintCallback):
        s = deque()
        s.append(node)
        while s:
            node = s.pop()
            if node is None:
                level -= 1
                continue
            print(str(node.data).rjust(len(repr(node.data)) + level *
                                   tabsize, tabchr) +
                  PrintCallback(node),
                  file=stream)
            level += 1
            s.append(None)
            s.extend(reversed(node.children))
    @staticmethod
    def _printtree_stack_gen(node, level, tabchr, tabsize, stream, PrintCallback):
        s = deque()
        s.append(iter((node,)))
        while s:
            it = s[-1]
            node = next(it, s)
            if node is s:
                level -= 1
                s.pop()
                continue
            print(str(node.data).rjust(len(repr(node.data)) + level *
                                   tabsize, tabchr) +
                  PrintCallback(node),
                  file=stream)
            level += 1
            s.append(iter(node.children))

    def __str__(self):
        """Returns str(self.aslist())."""
        return str(self.aslist())

    def __repr__(self):
        """Returns str(self.aslist())."""
        return str(self.aslist())

  def __len__(self):
      return self.total_nodes

class SetTrieMap(SetTrie):
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
    class NodeWithValue(SetTrie.Node):
        """Node object used by SetTrieMap. You probably don't need to use it
           from the outside.
        """
        def __init__(self, data=None, value=None):
            SetTrie.Node.__init__(self, data)
            self.value = value
    def __init__(self, iterable=None, recursion=False, generator=False):
        """Set up this SetTrieMap object.  If iterable is specified, it must
           be an iterable of (keyset, value) pairs from which set-trie
           is populated.
        """
        self._NodeTemplate = SetTrieMap.NodeWithValue
        if not hasattr(self, '_ValueCallback'):
            self._ValueCallback = SetTrieMap._yield_last_kv if generator else SetTrieMap._return_last_kv
        if not hasattr(self, '_ValueOnlyCallback'):
            self._ValueOnlyCallback = SetTrieMap._yield_last_value if generator else SetTrieMap._return_last_value
        self._PrintCallback = SetTrieMap._print_last
        SetTrie.__init__(self, iterable, recursion, generator)
    def _keys(self):
        return self._doiter(self.root, set(), None if self._generator else list(), self._YieldLast)
    def iterkeys(self):
        return self._make_generator(self._keys())
    def keys(self):
        """Alias for self.iterkeys()."""
        return self._make_list(self._keys())
    def _values(self):
        return self._doiter(self.root, set(), None if self._generator else list(), self._ValueOnlyCallback)
    def itervalues(self):
        return self._make_generator(self._values())
    def values(self):
        """Alias for self.itervalues()."""
        return self._make_list(self._values())
    def items(self):
        """
        Alias for self.aslist().
        """
        return self.aslist()
    def get(self, keyset, default=None):
        """Return the value associated to keyset if keyset is in this
           SetTrieMap, else default.
        """
        node = SetTrie._contains(self.root, keyset, self._NodeTemplate)
        if node is None: return default
        return node.value
    def add(self, aset):
        key, value = aset
        self.assign(key, value)
    def assign(self, akey, avalue):
        """Add key akey with associated value avalue to the container.
           akey must be a sortable and iterable container type."""
        node, notadd = SetTrie._add(self.root, akey, self._NodeTemplate)
        if not notadd: self.total_nodes += 1
        node.value = avalue
    def _itersubsetskeys(self, aset):
        return self._doitersubsets(self.root, tuple(sorted(aset)), 0, set(),
                                   None if self._generator else list(),
                                   self._NodeTemplate, self._YieldLast)
    def itersubsetskeys(self, aset):
        return self._make_generator(self._itersubsetskeys(aset))
    def subsetskeys(self, aset):
        return self._make_list(self._itersubsetskeys(aset))
    def _itersubsetsvalues(self, aset):
        return self._doitersubsets(self.root, tuple(sorted(aset)), 0, set(),
                                   None if self._generator else list(),
                                   self._NodeTemplate, self._ValueOnlyCallback)
    def itersubsetsvalues(self, aset):
        return self._make_generator(self._itersubsetsvalues(aset))
    def subsetsvalues(self, aset):
        return self._make_list(self._itersubsetsvalues(aset))
    def _itersupersetskeys(self, aset):
        return self._doitersupersets(self.root, tuple(sorted(aset)), 0, set(),
                                     None if self._generator else list(),
                                     self._NodeTemplate, self._YieldLast)
    def itersupersetskeys(self, aset):
        return self._make_generator(self._itersupersetskeys(aset))
    def supersetskeys(self, aset):
        return self._make_list(self._itersupersetskeys(aset))
    def _itersupersetsvalues(self, aset):
        return self._doitersupersets(self.root, tuple(sorted(aset)), 0, set(),
                                     None if self._generator else list(),
                                     self._NodeTemplate, self._ValueOnlyCallback)
    def itersupersetsvalues(self, aset):
        return self._make_generator(self._itersupersetsvalues(aset))
    def supersetsvalues(self, aset):
        return self._make_list(self._itersupersetsvalues(aset))
    @staticmethod
    def _yield_last_kv(path, node, _):
        yield set(path), node.value
    @staticmethod
    def _return_last_kv(path, node, res):
        res.append((set(path), node.value))
    @staticmethod
    def _yield_last_value(_, node, __):
        yield node.value
    @staticmethod
    def _return_last_value(_, node, res):
        res.append(node.value)
    @staticmethod
    def _print_last(node):
        """Used by self.printTree(), recursive preorder traverse and printing
           of trie node
        """
        return ': {}'.format(repr(node.value)) if node.flag_last else ''

class SetTrieMultiMap(SetTrieMap):
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
    def __init__(self, iterable=None, recursion=False, generator=False):
        """Set up this SetTrieMultiMap object.  If iterable is specified, it
           must be an iterable of (keyset, value) pairs from which
           set-trie is populated; key may be repeated, all associated
           values will be stored.
        """
        self._ValueCallback = SetTrieMultiMap._yield_last_kv if generator else SetTrieMultiMap._return_last_kv
        self._ValueOnlyCallback = SetTrieMultiMap._yield_last_value if generator else SetTrieMultiMap._return_last_value
        SetTrieMap.__init__(self, iterable, recursion, generator)
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
        node, _ = SetTrie._add(self.root, akey, self._NodeTemplate)
        if node.value is None: node.value = [avalue]
        else: node.value.append(avalue)
        return len(node.value)
    def count(self, keyset):
        """Returns the number of values associated to keyset. If keyset is
           unknown, returns 0.
        """
        node = SetTrie._contains(self.root, keyset, self._NodeTemplate)
        if node is None: return 0
        return len(node.value)
    def iterget(self, keyset):
        """Return an iterator to the values associated to keyset."""
        node = SetTrie._contains(self.root, keyset, self._NodeTemplate)
        if node is None: return iter(())
        return iter(node.value)
    @staticmethod
    def _yield_last_kv(path, node, _):
        if not node.value is None:
            for x in node.value: yield set(path), x
    @staticmethod
    def _return_last_kv(path, node, res):
        if not node.value is None:
            res.extend([(set(path), x) for x in node.value])
    @staticmethod
    def _yield_last_value(_, node, __):
        if not node.value is None:
            for x in node.value: yield x
    @staticmethod
    def _return_last_value(_, node, res):
        if not node.value is None:
            res.extend(node.value)
