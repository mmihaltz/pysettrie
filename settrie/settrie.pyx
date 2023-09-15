# distutils: language = c++
# cython: profile=False

#SetTrie in Cython by Gregory Morse
import sys
import copy

from cpython.object cimport PyObject
from cpython.ref cimport Py_XINCREF, Py_XDECREF
from libcpp cimport bool
cdef extern from "<iterator>" namespace "std" nogil:
    cdef cppclass reverse_iterator[T]:
        pass
    cdef reverse_iterator[T] make_reverse_iterator[T](T)
    cdef cppclass move_iterator[T]:
        pass
    cdef move_iterator[T] make_move_iterator[T](T)
from libcpp.vector cimport vector
from libcpp.stack cimport stack
from libcpp.unordered_set cimport unordered_set
#from libcpp.set cimport set as cset #does not support KeyComparator

from libcpp.utility cimport pair

cdef extern from "<set>" namespace "std" nogil:
    cdef cppclass set[T, KC]: #cannot rename to cset this way?
        ctypedef T value_type
        cppclass iterator:
            T& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(iterator)
            bint operator!=(iterator)
        cppclass reverse_iterator:
            reverse_iterator()
            #reverse_iterator(iterator)
            reverse_iterator(reverse_iterator)
            T& operator*()
            reverse_iterator operator++()
            reverse_iterator operator--()
            bint operator==(reverse_iterator)
            bint operator!=(reverse_iterator)
        cppclass const_iterator(iterator):
            pass
        cppclass const_reverse_iterator(reverse_iterator):
            pass
        set() except +
        set(set&) except +
        set(KC&)
        #set& operator=(set&)
        bint operator==(set&, set&)
        bint operator!=(set&, set&)
        bint operator<(set&, set&)
        bint operator>(set&, set&)
        bint operator<=(set&, set&)
        bint operator>=(set&, set&)
        iterator begin()
        const_iterator const_begin "begin"()
        void clear()
        size_t count(const T&)
        bint empty()
        iterator end()
        const_iterator const_end "end"()
        pair[iterator, iterator] equal_range(const T&)
        #pair[const_iterator, const_iterator] equal_range(T&)
        iterator erase(iterator)
        iterator erase(iterator, iterator)
        size_t erase(T&)
        iterator find(T&)
        const_iterator const_find "find"(T&)
        pair[iterator, bint] insert(const T&) except +
        iterator insert(iterator, const T&) except +
        void insert(iterator, iterator) except +
        #key_compare key_comp()
        iterator lower_bound(T&)
        const_iterator const_lower_bound "lower_bound"(T&)
        size_t max_size()
        reverse_iterator rbegin()
        const_reverse_iterator const_rbegin "rbegin"()
        reverse_iterator rend()
        const_reverse_iterator const_rend "rend"()
        size_t size()
        void swap(set&)
        iterator upper_bound(const T&)
        const_iterator const_upper_bound "upper_bound"(const T&)
        #value_compare value_comp()

from cpython.mem cimport PyMem_Malloc, PyMem_Free
from cython.operator cimport dereference as deref, preincrement as inc
cdef extern from *:
    """
    """

ctypedef void* Void_ptr
ctypedef Node* Node_ptr
ctypedef size_t(*node_hash)(const Node_ptr& s)
cdef size_t node_hashfunc(const Node_ptr& s):
    return hash(<object>s.data)
ctypedef bool(*node_eq)(const Node_ptr& lhs, const Node_ptr& rhs)
cdef bool node_equal(const Node_ptr& lhs, const Node_ptr& rhs):
    return <object>lhs.data == <object>rhs.data

ctypedef unordered_set[Node_ptr, node_hash, node_eq] node_unordered_set
ctypedef unordered_set[Node_ptr, node_hash, node_eq].iterator node_unordered_set_it
cdef node_unordered_set intersection(node_unordered_set s1, node_unordered_set s2):
    cdef node_unordered_set res
    cdef node_unordered_set_it it
    if s1.size() < s2.size():
        it = s1.begin()
        while it != s1.end():
            x = deref(it)
            if s2.find(x) != s2.end(): res.insert(x)
            inc(it)
    else:
        it = s2.begin()
        while it != s2.end():
            x = deref(it)
            if s1.find(x) != s1.end(): res.insert(x)
            inc(it)
    return res

ctypedef bool(*node_comp)(const Node_ptr& lhs, const Node_ptr& rhs)
cdef bool node_comparator(const Node_ptr& lhs, const Node_ptr& rhs):
    return <object>lhs.data < <object>rhs.data
ctypedef set[Node_ptr, node_comp] node_set
ctypedef set[Node_ptr, node_comp].iterator node_set_it
ctypedef set[Node_ptr, node_comp].reverse_iterator node_set_rev_it

ctypedef pair[Node_ptr, Py_ssize_t] node_pair
ctypedef pair[Node_ptr, node_set_it] node_with_it
ctypedef pair[node_set_it, node_set_it] node_set_its
ctypedef pair[node_pair, node_set_its] superset_pair

cdef struct Node:
  node_set* children
  bint flag_last
  void* data

cdef struct NodeWithValue:
  Node node
  void* value

ctypedef Node*(*construct_func)(void* data)
cdef Node* construct_node(void* data):
  cdef Node* n
  n = <Node*>PyMem_Malloc(sizeof(Node))
  if not n: raise MemoryError()
  n.children = new node_set(node_comparator)
  n.flag_last = False
  Py_XINCREF(<PyObject*>data)
  n.data = data
  return n
  
cdef Node* construct_node_value(void* data):
  cdef Node* n
  n = <Node*>PyMem_Malloc(sizeof(NodeWithValue))
  if not n: raise MemoryError()
  n.children = new node_set(node_comparator)
  n.flag_last = False
  Py_XINCREF(<PyObject*>data)
  n.data = data
  (<NodeWithValue*>n).value = NULL
  return n

ctypedef void(*destruct_func)(Node* n)
cdef void destruct_node(Node* n):
  for x in deref(n.children):
    destruct_node(x)
  del n.children
  Py_XDECREF(<PyObject*>n.data)
  PyMem_Free(n)

cdef void destruct_node_value(Node* n):
  for x in deref(n.children):
    destruct_node(x)
  del n.children
  Py_XDECREF(<PyObject*>n.data)
  Py_XDECREF(<PyObject*>(<NodeWithValue*>n).value)
  PyMem_Free(n)
  
cdef Py_ssize_t bisect_left(a, x, Py_ssize_t lo, Py_ssize_t hi=-1):
    if hi == -1: hi = len(a)
    cdef Py_ssize_t mid
    while lo < hi:
      mid = (lo+hi)//2
      if a[mid] < x: lo = mid+1
      else: hi = mid
    return lo
    
ctypedef void(*value_cb)(vector[Void_ptr] path, Node* node, res)
ctypedef object(*set_cb)(Node* node, setarr, Py_ssize_t idx, vector[Void_ptr] path, res, value_cb ValueCallback)
ctypedef object(*iter_cb)(Node* node, vector[Void_ptr] path, res, value_cb ValueCallback)
ctypedef bint(*hasset_cb)(Node* node, setarr, Py_ssize_t idx)
ctypedef object(*print_cb)(Node* node)
ctypedef void(*print_func_cb)(Node* node, level, tabchr, tabsize, stream, print_cb)

cdef class SetTrie:
  cdef Node* root
  cdef Py_ssize_t total_nodes
  cdef print_func_cb _printtree
  cdef set_cb _doitersupersets
  cdef set_cb _doitersubsets
  cdef iter_cb _doiter
  cdef hasset_cb _hassubset
  cdef hasset_cb _hassuperset
  cdef construct_func _construct_func
  cdef destruct_func _destruct_func
  cdef value_cb _YieldLast
  cdef value_cb _ValueCallback
  cdef print_cb _PrintCallback
  def __cinit__(self):
    self.root = construct_node(NULL)
    self.total_nodes = 0
  def __init__(self, iterable=None, recursion=False):
    self._YieldLast = SetTrie._return_last
    if self._construct_func == NULL: self._construct_func = construct_node
    if self._destruct_func == NULL: self._destruct_func = destruct_node
    if recursion is True: self._doiter, self._hassuperset, self._doitersupersets, self._hassubset, self._doitersubsets, self._printtree = SetTrie._iter_recurse, SetTrie._hassuperset_recurse, SetTrie._itersupersets_recurse, SetTrie._hassubset_recurse, SetTrie._itersubsets_recurse, SetTrie._printtree_recurse
    elif recursion is False: self._doiter, self._hassuperset, self._doitersupersets, self._hassubset, self._doitersubsets, self._printtree = SetTrie._iter_stack_gen, SetTrie._hassuperset_stack_gen, SetTrie._itersupersets_stack_gen, SetTrie._hassubset_stack_item, SetTrie._itersubsets_stack_item, SetTrie._printtree_stack_gen
    else: self._doiter, self._hassuperset, self._doitersupersets, self._hassubset, self._doitersubsets, self._printtree = SetTrie._iter_stack_item, SetTrie._hassuperset_stack_item, SetTrie._itersupersets_stack_item, SetTrie._hassubset_stack_item, SetTrie._itersubsets_stack_item, SetTrie._printtree_stack_item
    if self._ValueCallback == NULL: self._ValueCallback = self._YieldLast
    if self._PrintCallback == NULL: self._PrintCallback = SetTrie._print_last
    if iterable is not None:
      for s in iterable:
        self.add(s)
  def __dealloc__(self):
    destruct_node(self.root)
        
  def add(self, aset):
    """Add set aset to the container.  aset must be a sortable and
       iterable container type.
    """
    cdef pair[Node_ptr, bint] ret
    ret = SetTrie._add(self.root, iter(sorted(aset)), self._construct_func) #holdset
    if not ret.second: self.total_nodes += 1
    
  @staticmethod
  cdef pair[Node_ptr, bint] _add(Node* node, it, construct_func constfunc):
    """Recursive function used by self.add().
       node is a SetTrieNode object
       it is an iterator over a sorted set"""
    cdef Node* testnode
    cdef Node* nextnode
    cdef Node findnode
    cdef node_set_it idx
    cdef node_set* childs
    for data in it:
      # find first child with this data
      findnode.data, childs = <void*>data, node.children
      idx = childs.lower_bound(&findnode)
      if idx == childs.end():
        nextnode = constfunc(<void*>data)
        childs.insert(nextnode) # add to children & sort
        node = nextnode
      else:
        testnode = deref(idx)
        if <object>testnode.data != data:
          nextnode = constfunc(<void*>data)
          childs.insert(nextnode)  # add to children & sort   
          node = nextnode
        else:
          node = testnode
    cdef pair[Node_ptr, bint] ret = pair[Node_ptr, bint](node, node.flag_last)
    node.flag_last = True  # end of set to add
    return ret

  def remove(self, aset):
      """Remove set aset from the container.  aset must be a sortable and
         iterable container type.
      """
      cdef bint removed = SetTrie._remove(self.root, iter(sorted(aset)), self._destruct_func)
      if removed: self.total_nodes -= 1
  
  @staticmethod
  cdef _remove(Node* node, it, destruct_func destfunc):
      """Recursive function used by self.remove().
         node is a SetTrieNode object
         it is an iterator over a sorted set"""
      cdef vector[Node_ptr] nodes
      cdef Node newnode
      cdef node_set_it idx
      cdef node_set* childs
      for data in it:
          nodes.push_back(node)  # add to post-recursion stack
          newnode.data, childs = <void*>data, node.children
          idx = childs.lower_bound(&newnode)
          if idx == childs.end(): return False #not in container
          node = deref(idx)
          if <object>node.data != data: return False # not in container
      if not node.flag_last: return False
      node.flag_last = False # final node set to off
      cdef Node* nextnode = node
      cdef vector[Node_ptr].reverse_iterator iter = nodes.rbegin()
      while iter != nodes.rend(): #  walk backwards through child nodes
          if nextnode.flag_last or not nextnode.children.empty(): break
          deref(iter).children.erase(nextnode)
          destfunc(nextnode)
          nextnode = deref(iter)
          inc(iter)
      return True

  def contains(self, aset):
      """Returns True iff this set-trie contains set aset."""
      return SetTrie._contains(self.root, iter(sorted(aset))) != NULL

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
  cdef Node* _contains(Node* node, it):
      """Recursive function used by self.contains()."""
      cdef Node curnode
      cdef node_set_it idx
      cdef node_set* childs
      for data in it:
          # find first child with this data
          curnode.data, childs = <void*>data, node.children
          idx = childs.lower_bound(&curnode)
          if idx == childs.end(): return NULL
          node = deref(idx)
          if <object>node.data != data: return NULL  # not found
      return node if node.flag_last else NULL
      
  def hassuperset(self, aset):
      """Returns True iff there is at least one set in this set-trie that is
         the superset of set aset.
      """
      # TODO: if aset is not a set, convert it to a set first to
      # collapse multiply existing elements
      return self._hassuperset(self.root, tuple(sorted(aset)), 0)

  @staticmethod
  cdef bint _hassuperset_recurse(Node* node, setarr, Py_ssize_t idx):
      """Used by hassuperset()."""
      if idx > len(setarr) - 1:
          return node.flag_last or not node.children.empty()
      found = False
      cdef Node curnode
      cdef node_set_it i
      cdef node_set_it it
      cdef Node* checknode
      cdef node_set* childs
      curnode.data, childs = <void*>setarr[idx], node.children
      i = childs.lower_bound(&curnode)
      it = childs.begin()
      while it != i:
          if SetTrie._hassuperset_recurse(deref(it), setarr, idx): return True
          inc(it)
      if i != childs.end():
          checknode = deref(i)
          if setarr[idx] == <object>checknode.data:
              found = SetTrie._hassuperset_recurse(checknode, setarr, idx + 1)
      return found

  @staticmethod
  cdef bint _hassuperset_stack_item(Node* node, setarr, Py_ssize_t idx):
      """Used by hassuperset()."""
      len_s = len(setarr)
      if idx > len_s - 1:
          return node.flag_last or not node.children.empty()
      cdef stack[node_pair] s
      cdef Node curnode
      cdef node_set_it i
      cdef node_set_it it
      cdef Node* checknode
      cdef node_set* childs
      s.push(node_pair(node, idx))
      while not s.empty():
          v = s.top()
          s.pop()
          node, idx = v.first, v.second
          curnode.data, childs = <void*>setarr[idx], node.children
          i = childs.lower_bound(&curnode)
          it = childs.begin()
          while it != i:
              s.push(node_pair(deref(it), idx))
              inc(it)
          if i != childs.end():
              checknode = deref(i)
              if setarr[idx] == <object>checknode.data:
                  if idx + 1 > len_s - 1: return True
                  s.push(node_pair(checknode, idx + 1))
      return False
  @staticmethod
  cdef bint _hassuperset_stack_gen(Node* node, setarr, Py_ssize_t idx):
      """Used by hassuperset()."""
      len_s = len(setarr)
      if idx > len_s - 1:
          return node.flag_last or not node.children.empty()
      cdef stack[superset_pair] s
      cdef Node curnode
      cdef node_set_it i
      cdef node_set_it it
      cdef node_pair np
      cdef Node* checknode
      cdef node_set* childs
      cdef node_set_its sent = node_set_its(node_set_it(), node_set_it())
      s.push(superset_pair(node_pair(node, idx), sent))
      while not s.empty():
          v = s.top()
          node, idx = v.first.first, v.first.second
          if node == NULL:
              if v.second.first == v.second.second:
                  s.pop()
                  continue
              node = deref(v.second.first)
              inc(s.top().second.first)
          else: s.pop()
          curnode.data, childs = <void*>setarr[idx], node.children
          i = childs.lower_bound(&curnode)          
          s.push(superset_pair(node_pair(NULL, idx), node_set_its(childs.begin(), i)))
          if i != childs.end():
              checknode = deref(i)
              if setarr[idx] == <object>checknode.data:
                  if idx + 1 > len_s - 1: return True
                  np = node_pair(checknode, idx + 1)
                  s.push(superset_pair(np, sent))
      return False
      
  def _itersupersets(self, aset):
      """Return an iterator over all sets in this set-trie that are (proper
         or not proper) supersets of set aset.
      """
      cdef vector[Void_ptr] path
      return self._doitersupersets(self.root, tuple(sorted(aset)), 0, path, list(), self._ValueCallback)

  @staticmethod
  cdef _itersupersets_recurse(Node* node, setarr, Py_ssize_t idx, vector[Void_ptr] path, res, value_cb ValueCallback):
      """Used by itersupersets()."""
      if idx > len(setarr) - 1:
          # no more elements to find: just traverse this subtree to get
          # all supersets
          return SetTrie._iter_recurse(node, path, res, ValueCallback)
      if node.data != NULL:
          path.push_back(node.data)
      cdef Node curnode
      cdef node_set_it i
      cdef node_set_it it
      cdef Node* checknode
      cdef node_set* childs
      curnode.data, childs = <void*>setarr[idx], node.children
      i = childs.lower_bound(&curnode)
      it = childs.begin()
      while it != i:
          SetTrie._itersupersets_recurse(deref(it), setarr, idx, path, res, ValueCallback)
          inc(it)
      if i != childs.end():
          checknode = deref(i)
          if setarr[idx] == <object>checknode.data:
              SetTrie._itersupersets_recurse(checknode, setarr, idx + 1, path, res, ValueCallback)
      if node.data != NULL:
          path.pop_back()
      return res

  @staticmethod
  cdef _itersupersets_stack_item(Node* node, setarr, Py_ssize_t idx, vector[Void_ptr] path, res, value_cb ValueCallback):
      """Used by itersupersets()."""
      len_s = len(setarr)
      if idx > len_s - 1:
          # no more elements to find: just traverse this subtree to get
          # all supersets
          return SetTrie._iter_stack_item(node, path, res, ValueCallback)
      cdef stack[node_pair] s
      cdef Node curnode
      cdef node_set_rev_it it
      cdef node_set_it i
      cdef Node* checknode
      cdef node_set* childs
      s.push(node_pair(node, idx))
      while not s.empty():
          v = s.top()
          s.pop()
          node, idx = v.first, v.second
          if node == NULL:
              path.pop_back()
              continue
          if idx > len_s - 1:
              SetTrie._iter_stack_item(node, path, res, ValueCallback)
              continue
          if node.data != NULL:
              path.push_back(node.data)
              s.push(node_pair(NULL, -1))
          curnode.data, childs = <void*>setarr[idx], node.children
          i = childs.lower_bound(&curnode)
          if i != childs.end():
              checknode = deref(i)
              if setarr[idx] == <object>checknode.data:
                  s.push(node_pair(checknode, idx + 1))
          it = <node_set_rev_it>make_reverse_iterator(i)
          #it = node_set_rev_it(<node_set_rev_it>i) #&*r == &*(i-1)
          while it != childs.rend():
              s.push(node_pair(deref(it), idx))
              inc(it)
      return res
  @staticmethod
  cdef _itersupersets_stack_gen(Node* node, setarr, Py_ssize_t idx, vector[Void_ptr] path, res, value_cb ValueCallback):
      """Used by itersupersets()."""
      len_s = len(setarr)
      if idx > len_s - 1:
          # no more elements to find: just traverse this subtree to get
          # all supersets
          return SetTrie._iter_stack_item(node, path, res, ValueCallback)
      cdef stack[superset_pair] s
      cdef Node curnode
      cdef node_set_rev_it it
      cdef node_set_it i
      cdef Node* checknode
      cdef node_set* childs
      cdef node_pair np
      cdef node_set_its sent = node_set_its(node_set_it(), node_set_it())
      s.push(superset_pair(node_pair(node, idx), sent))
      while not s.empty():
          v = s.top()
          node, idx = v.first.first, v.first.second
          if idx == -1:
              path.pop_back()
              s.pop()
              continue
          if node == NULL:
              if v.second.first == v.second.second:
                  s.pop()
                  continue
              node = deref(v.second.first)
              inc(s.top().second.first)
          else: s.pop()
          if idx > len_s - 1:
              SetTrie._iter_stack_item(node, path, res, ValueCallback)
              continue
          if node.data != NULL:
              path.push_back(node.data)
              s.push(superset_pair(node_pair(NULL, -1), sent))
          curnode.data, childs = <void*>setarr[idx], node.children
          i = childs.lower_bound(&curnode)
          if i != childs.end():
              checknode = deref(i)
              if setarr[idx] == <object>checknode.data:
                  np = node_pair(checknode, idx + 1)
                  s.push(superset_pair(np, sent))
          s.push(superset_pair(node_pair(NULL, idx), node_set_its(childs.begin(), i)))
      return res
      
  def itersupersets(self, aset):
      """Return an iterator over all sets in this set-trie that are (proper
         or not proper) supersets of set aset.
      """
      return self._make_generator(self._itersupersets(aset))
  def supersets(self, aset):
      """Return a list containing all sets in this set-trie that are
         supersets of set aset.
      """
      return self._itersupersets(aset)

  def hassubset(self, aset):
      """Return True iff there is at least one set in this set-trie that is
         the (proper or not proper) subset of set aset.
      """
      return self._hassubset(self.root, tuple(sorted(aset)), 0)

  @staticmethod
  cdef bint _hassubset_recurse(Node* node, setarr, Py_ssize_t idx):
      """Used by hassubset()."""
      if node.flag_last:
          return True
      len_s = len(setarr)
      if idx > len_s - 1:
          return False
      cdef Node curnode
      cdef node_set_it i
      cdef Node* child
      cdef node_set* childs
      curnode.data, childs = <void*>setarr[idx], node.children
      i = childs.lower_bound(&curnode)
      if i != childs.end():
          checknode = deref(i)
          if setarr[idx] == <object>checknode.data:
              inc(i)
              if SetTrie._hassubset_recurse(checknode, setarr, idx + 1): return True
          while i != childs.end():
              child = deref(i)
              jdx = bisect_left(setarr, <object>child.data, idx + 1)
              if jdx < len_s and <object>child.data == setarr[jdx]:
                  if SetTrie._hassubset_recurse(child, setarr, jdx + 1): return True
                  idx = jdx
              else: idx = jdx - 1
              inc(i)
      return False

  @staticmethod
  cdef bint _hassubset_stack_item(Node* node, setarr, Py_ssize_t idx):
      """Used by hassubset()."""
      len_s = len(setarr)
      cdef stack[node_pair] s
      cdef Node curnode
      cdef node_set_it i
      cdef Node* child
      cdef node_set* childs
      s.push(node_pair(node, idx))
      while not s.empty():
          v = s.top()
          s.pop()
          node, idx = v.first, v.second
          if node.flag_last:
              return True
          if idx > len_s - 1:
              continue
          curnode.data, childs = <void*>setarr[idx], node.children
          i = childs.lower_bound(&curnode)
          if i != childs.end():
              checknode = deref(i)
              if setarr[idx] == <object>checknode.data:
                  inc(i)
                  s.push(node_pair(checknode, idx + 1))
              while i != childs.end():
                  child = deref(i)
                  jdx = bisect_left(setarr, <object>child.data, idx + 1)
                  if jdx < len_s and <object>child.data == setarr[jdx]:
                      s.push(node_pair(child, jdx + 1))
                      idx = jdx
                  else: idx = jdx - 1
                  inc(i)
      return False

  def _itersubsets(self, aset):
      """Return an iterator over all sets in this set-trie that are (proper
         or not proper) subsets of set aset.
      """
      cdef vector[Void_ptr] path
      return self._doitersubsets(self.root, tuple(sorted(aset)), 0, path, list(), self._ValueCallback)

  @staticmethod
  cdef _itersubsets_recurse(Node* node, setarr, Py_ssize_t idx, vector[Void_ptr] path, res, value_cb ValueCallback):
      """Used by itersubsets()."""
      cdef Node curnode
      cdef node_set_it i
      cdef Node* checknode
      cdef Node* child
      cdef node_set* childs
      if node.data != NULL:
          path.push_back(node.data)
      if node.flag_last:
          ValueCallback(path, node, res)
      len_s = len(setarr)
      if idx <= len_s - 1:
          curnode.data, childs = <void*>setarr[idx], node.children
          i = childs.lower_bound(&curnode)
          if i != childs.end():
              checknode = deref(i)
              if setarr[idx] == <object>checknode.data:
                  inc(i)
                  SetTrie._itersubsets_recurse(checknode, setarr, idx + 1, path, res, ValueCallback)
              while i != childs.end():
                  child = deref(i)
                  jdx = bisect_left(setarr, <object>child.data, idx + 1)
                  if jdx < len_s and <object>child.data == setarr[jdx]:
                      SetTrie._itersubsets_recurse(child, setarr, jdx + 1, path, res, ValueCallback)
                      idx = jdx
                  else: idx = jdx - 1
                  inc(i)
      if node.data != NULL:
          path.pop_back()
      return res

  @staticmethod
  cdef _itersubsets_stack_item(Node* node, setarr, Py_ssize_t idx, vector[Void_ptr] path, res, value_cb ValueCallback):
      """Used by itersubsets()."""
      len_s = len(setarr)
      cdef stack[node_pair] s
      cdef Node curnode
      cdef node_set_it i
      cdef node_set_rev_it it
      cdef node_set_rev_it irev
      cdef Node* checknode
      cdef Node* child
      cdef node_set* childs
      s.push(node_pair(node, idx))
      while not s.empty():
          v = s.top()
          s.pop()
          node, idx = v.first, v.second
          if node == NULL:
              path.pop_back()
              continue
          if node.data != NULL:
              path.push_back(node.data)
              s.push(node_pair(NULL, -1))
          if node.flag_last:
              ValueCallback(path, node, res)
          if idx <= len_s - 1:
              curnode.data, childs = <void*>setarr[idx], node.children
              i = childs.lower_bound(&curnode)
              if i != childs.end():
                  checknode = deref(i)
                  iseq = setarr[idx] == <object>checknode.data
                  if iseq:
                      inc(i)
                  mx, it, revi = len_s, childs.rbegin(), <node_set_rev_it>make_reverse_iterator(i)
                  while revi != it:
                      child = deref(it)
                      jdx = bisect_left(setarr, <object>child.data, idx + 1, mx)
                      if jdx < len_s and <object>child.data == setarr[jdx]:
                          s.push(node_pair(child, jdx + 1))
                          mx = jdx + 1
                      else: mx = jdx
                      inc(it)
                  if iseq:
                      s.push(node_pair(checknode, idx + 1))
      return res

  def itersubsets(self, aset):
      """Return an iterator over all sets in this set-trie that are (proper
         or not proper) subsets of set aset.
      """
      return self._make_generator(self._itersubsets(aset))
  def subsets(self, aset):
      """Return a list of sets in this set-trie that are (proper or not
         proper) subsets of set aset.
      """
      return self._itersubsets(aset)
        
  def _iter(self):
      cdef vector[Void_ptr] l
      return self._doiter(self.root, l, list(), self._ValueCallback)

  def iter(self):
      """Returns an iterator over the sets stored in this set-trie (with
         pre-order tree traversal).  The sets are returned in sorted
         order with their elements sorted.
      """
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
      cdef vector[Void_ptr] l
      return self._make_generator(self._doiter(self.root, l, list(), self._YieldLast))

  @staticmethod
  cdef _iter_recurse(Node* node, vector[Void_ptr] path, res, value_cb ValueCallback):
      #cdef vector[Void_ptr] path
      #cdef stack[Node*] s
      """Recursive function used by self.__iter__()."""
      #for n in node.children:      
      if node.data != NULL:
          path.push_back(node.data)
      if node.flag_last:
          ValueCallback(path, node, res)
      for child in deref(node.children):
          SetTrie._iter_recurse(child, path, res, ValueCallback)
      if node.data != NULL:
          path.pop_back()
      return res

  @staticmethod
  cdef _iter_stack_item(Node* node, vector[Void_ptr] path, res, value_cb ValueCallback):
      """Non-recursive stack-based function used by self.__iter__()."""
      cdef stack[Node_ptr] s
      cdef node_set_rev_it it
      if node.data != NULL:
          s.push(NULL)
          path.push_back(node.data)
      if node.flag_last:
          ValueCallback(path, node, res)
      it = node.children.rbegin()
      while it != node.children.rend():
          s.push(deref(it))
          inc(it)
      while not s.empty():
          node = s.top()
          s.pop()
          if node == NULL:
              path.pop_back()
              continue
          path.push_back(node.data)
          if node.flag_last:
              ValueCallback(path, node, res)
          s.push(NULL)
          it = node.children.rbegin()
          while it != node.children.rend():
              s.push(deref(it))
              inc(it)
      return res

  @staticmethod
  cdef _iter_stack_gen(Node* node, vector[Void_ptr] path, res, value_cb ValueCallback):
      """Non-recursive stack-based function used by self.__iter__()."""
      cdef stack[node_with_it] s
      cdef node_set_it it
      cdef node_with_it i
      if node.data != NULL:
          path.push_back(node.data)
      if node.flag_last:
          ValueCallback(path, node, res)
      s.push(node_with_it(node, node.children.begin()))
      while not s.empty():
          i = s.top()
          node, it = i.first, i.second
          if it == node.children.end():
              if node.data != NULL: path.pop_back()
              s.pop()
              continue
          node = deref(it)
          inc(s.top().second)
          #s.pop()
          #s.push(node_with_it(i.first, inc(it)))
          path.push_back(node.data)
          if node.flag_last:
              ValueCallback(path, node, res)
          s.push(node_with_it(node, node.children.begin()))
      return res
  
  def aslist(self):
      """Return an array containing all the sets stored in this set-trie.
         The sets are in sorted order with their elements sorted."""
      return self._iter()

  def empty(self):
      return self.root.children.empty()

  @staticmethod
  cdef void _return_last(vector[Void_ptr] path, Node* _, res): res.append({<object>x for x in path})
  
  @staticmethod
  cdef _print_last(Node* node): return '#' if node.flag_last else ''
  
  def _make_generator(self, l): return iter(l)

  def printtree(self, tabchr=' ', tabsize=2, stream=sys.stdout):
      """Print a mirrored 90-degree rotation of the nodes in this trie to
         stream (default: sys.stdout).  Nodes marked as flag_last
         are trailed by the '#' character.  tabchr and tabsize
         determine the indentation: at tree level n, n*tabsize
         tabchar characters will be used.
      """
      self._printtree(self.root, 0, tabchr, tabsize, stream, self._PrintCallback)

  @staticmethod
  cdef void _printtree_recurse(Node* node, level, tabchr, tabsize, stream, print_cb PrintCallback):
      """Used by self.printTree(), recursive preorder traverse and printing
         of trie node
      """
      obj = <object>node.data if node.data != NULL else None
      print(str(obj).rjust(len(repr(obj)) + level *
                                 tabsize, tabchr) +
                PrintCallback(node), file=stream)
      for child in deref(node.children):
          SetTrie._printtree_recurse(child, level + 1, tabchr, tabsize, stream, PrintCallback)

  @staticmethod
  cdef void _printtree_stack_item(Node* node, level, tabchr, tabsize, stream, print_cb PrintCallback):
      """Used by self.printTree(), recursive preorder traverse and printing
         of trie node
      """
      cdef stack[Node_ptr] s
      cdef node_set_rev_it it
      s.push(node)
      while not s.empty():
          node = s.top()
          s.pop()
          if node == NULL:
              level -= 1
              continue
          obj = <object>node.data if node.data != NULL else None
          print(str(obj).rjust(len(repr(obj)) + level *
                                     tabsize, tabchr) +
                    PrintCallback(node), file=stream)
          level += 1
          s.push(NULL)
          it = node.children.rbegin()
          while it != node.children.rend():
              s.push(deref(it))
              inc(it)
  @staticmethod
  cdef void _printtree_stack_gen(Node* node, level, tabchr, tabsize, stream, print_cb PrintCallback):
      cdef stack[node_with_it] s
      cdef node_set_it it
      s.push(node_with_it(NULL, node_set_it()))
      while not s.empty():
          i = s.top()
          if i.first == NULL: s.pop()
          else:
              node, it = i.first, i.second
              if it == node.children.end():
                  level -= 1
                  s.pop()
                  continue
              node = deref(it)
              inc(s.top().second)
              #s.pop()
              #s.push(node_with_it(i.first, inc(it)))
          obj = <object>node.data if node.data != NULL else None
          print(str(obj).rjust(len(repr(obj)) + level *
                                     tabsize, tabchr) +
                    PrintCallback(node), file=stream)
          level += 1
          s.push(node_with_it(node, node.children.begin()))
              
  def __str__(self):
      """Returns str(self.aslist())."""
      return str(self.aslist())

  def __repr__(self):
      """Returns str(self.aslist())."""
      return str(self.aslist())
  
  def __len__(self):
      return self.total_nodes

cdef class SetTrieMap(SetTrie):
    cdef value_cb _ValueOnlyCallback
    def __init__(self, iterable=None, recursion=False):
        self._construct_func = construct_node_value
        self._destruct_func = destruct_node_value
        if self._ValueCallback == NULL:
            self._ValueCallback = SetTrieMap._return_last_kv
        if self._ValueOnlyCallback == NULL:
            self._ValueOnlyCallback = SetTrieMap._return_last_value
        self._PrintCallback = SetTrieMap._print_last
        SetTrie.__init__(self, iterable, recursion)
    def _keys(self):
        cdef vector[Void_ptr] l
        return self._doiter(self.root, l, list(), self._YieldLast)
    def iterkeys(self):
        return self._make_generator(self._keys())
    def keys(self):
        return self._keys()
    def _values(self):
        cdef vector[Void_ptr] l
        return self._doiter(self.root, l, list(), self._ValueOnlyCallback)
    def itervalues(self):
        return self._make_generator(self._values())
    def values(self):
        return self._values()
    def items(self):
        """
        Alias for self.aslist().
        """
        return self.aslist()
    def get(self, keyset, default=None):
        cdef Node* node = SetTrie._contains(self.root, iter(sorted(keyset)))
        if node == NULL: return default
        if (<NodeWithValue*>node).value == NULL: return None
        return <object>(<NodeWithValue*>node).value
    def add(self, aset):
        key, value = aset
        self.assign(key, value)
    def assign(self, akey, avalue):
        cdef Node* node
        v = SetTrie._add(self.root, iter(sorted(akey)), self._construct_func)
        node, notadd = v.first, v.second
        if not notadd: self.total_nodes += 1
        if (<NodeWithValue*>node).value != NULL:
            Py_XDECREF(<PyObject*>(<NodeWithValue*>node).value)
        cdef void* aptr = <void*>avalue
        Py_XINCREF(<PyObject*>aptr)
        (<NodeWithValue*>node).value = aptr
    def _itersubsetskeys(self, aset):
        cdef vector[Void_ptr] l
        return self._doitersubsets(self.root, tuple(sorted(aset)), 0, l,
                                   list(), self._YieldLast)
    def itersubsetskeys(self, aset):
        return self._make_generator(self._itersubsetskeys(aset))
    def subsetskeys(self, aset):
        return self._itersubsetskeys(aset)
    def _itersubsetsvalues(self, aset):
        cdef vector[Void_ptr] l
        return self._doitersubsets(self.root, tuple(sorted(aset)), 0, l,
                                   list(), self._ValueOnlyCallback)
    def itersubsetsvalues(self, aset):
        return self._make_generator(self._itersubsetsvalues(aset))
    def subsetsvalues(self, aset):
        return self._itersubsetsvalues(aset)
    def _itersupersetskeys(self, aset):
        cdef vector[Void_ptr] l
        return self._doitersupersets(self.root, tuple(sorted(aset)), 0, l,
                                     list(), self._YieldLast)
    def itersupersetskeys(self, aset):
        return self._make_generator(self._itersupersetskeys(aset))
    def supersetskeys(self, aset):
        return self._itersupersetskeys(aset)
    def _itersupersetsvalues(self, aset):
        cdef vector[Void_ptr] l
        return self._doitersupersets(self.root, tuple(sorted(aset)), 0, l,
                                     list(), self._ValueOnlyCallback)
    def itersupersetsvalues(self, aset):
        return self._make_generator(self._itersupersetsvalues(aset))
    def supersetsvalues(self, aset):
        return self._itersupersetsvalues(aset)
    @staticmethod
    cdef void _return_last_kv(vector[Void_ptr] path, Node* node, res):
        res.append(({<object>x for x in path}, <object>(<NodeWithValue*>node).value))
    @staticmethod
    cdef void _return_last_value(vector[Void_ptr] _, Node* node, res):
        res.append(<object>(<NodeWithValue*>node).value)
    @staticmethod
    cdef _print_last(Node* node):
        return ': {}'.format(repr(<object>(<NodeWithValue*>node).value)) if node.flag_last else ''

cdef class SetTrieMultiMap(SetTrieMap):
    def __init__(self, iterable=None, recursion=False):
        self._ValueCallback = SetTrieMultiMap._return_last_kv
        self._ValueOnlyCallback = SetTrieMultiMap._return_last_value
        SetTrieMap.__init__(self, iterable, recursion)
    def assign(self, akey, avalue):
        cdef Node* node = SetTrie._add(self.root, iter(sorted(akey)), construct_node_value).first
        if (<NodeWithValue*>node).value == NULL:
            l = [avalue]
            Py_XINCREF(<PyObject*><void*>l)
            (<NodeWithValue*>node).value = <void*>l
        else: (<object>(<NodeWithValue*>node).value).append(avalue)
        return len(<object>(<NodeWithValue*>node).value)
    def count(self, keyset):
        cdef Node* node = SetTrie._contains(self.root, iter(sorted(keyset)))
        if node == NULL or (<NodeWithValue*>node).value == NULL: return 0
        return len(<object>(<NodeWithValue*>node).value)
    def iterget(self, keyset):
        cdef Node* node = SetTrie._contains(self.root, iter(sorted(keyset)))
        if node == NULL or (<NodeWithValue*>node).value == NULL: return iter(())
        return iter(<object>(<NodeWithValue*>node).value)
    @staticmethod
    cdef void _return_last_kv(vector[Void_ptr] path, Node* node, res):
        if (<NodeWithValue*>node).value != NULL:
            res.extend([({<object>y for y in path}, x) for x in <object>(<NodeWithValue*>node).value])
    @staticmethod
    cdef void _return_last_value(vector[Void_ptr] _, Node* node, res):
        if (<NodeWithValue*>node).value != NULL:
            res.extend(<object>(<NodeWithValue*>node).value)
