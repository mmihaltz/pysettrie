"""
runfile('makesettrie.py',
        wdir='.',
        args='build_ext --inplace')
cd /D .
"%ProgramData%\Anaconda3\python.exe" makesettrie.py build_ext --inplace
import os
os.chdir('.')
import settrietest
import unittest
unittest.main(settrietest.TestSetTrie())
unittest.main(settrietest.TestSetTrieItemStack())
unittest.main(settrietest.TestSetTrieRecursion())
unittest.main(settrietest.TestSetTrieMap())
unittest.main(settrietest.TestSetTrieMultiMap())
unittest.main(settrietest.TestSetTrieGenerator())
unittest.main(settrietest.TestSetTrieItemStackGen())
unittest.main(settrietest.TestSetTrieRecursionGen())
import os
with open(os.devnull, 'w') as dev:
    %timeit unittest.main(settrietest.TestSetTrie(), testRunner=unittest.TextTestRunner(dev))
%timeit settrietest.TestSetTrie().test_performance()
import cProfile
cProfile.run('import settrietest; settrietest.TestSetTrie().test_performance()', 'settriestats', sort='tottime')
import pstats
p = pstats.Stats('settriestats')
p.strip_dirs().sort_stats('tottime').print_stats()
"""
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

setup(
    ext_modules = cythonize([
    Extension("settrie", ["settrie.pyx"])],
    language_level=3
    ) #"settrie.pyx")
)
