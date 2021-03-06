from . import ProgressiveTest, skip, skipIf

from progressivis.core import aio
from progressivis import Print
from progressivis.table.stirrer import Stirrer
from progressivis.linalg import (Unary, Binary, ColsBinary, Reduce,
                                 func2class_name,
                                 unary_module, make_unary,
                                 binary_module, make_binary,
                                 reduce_module, make_reduce,
                                 binary_dict_int_tst,
                                 unary_dict_gen_tst,
                                 binary_dict_gen_tst)
import progressivis.linalg as arr
from progressivis.core.bitmap import bitmap
from progressivis.stats import RandomTable, RandomDict
import numpy as np

#@skip
class TestUnary(ProgressiveTest):
    def test_unary(self):
        s = self.scheduler()
        random = RandomTable(10, rows=100_000, scheduler=s)
        module = Unary(np.log, scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.log(random.table().to_array())
        res2 = module.table().to_array()
        self.assertEqual(module.name, "unary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_unary2(self):
        s = self.scheduler()
        random = RandomTable(10, rows=100_000, scheduler=s)
        module = Unary(np.log, columns=['_3', '_5', '_7'], scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.log(random.table().to_array()[:, [2, 4, 6]])
        res2 = module.table().to_array()
        self.assertEqual(module.name, "unary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def _t_stirred_unary(self, **kw):
        s = self.scheduler()
        random = RandomTable(10, rows=100_000, scheduler=s)
        stirrer = Stirrer(update_column='_3',
                          fixed_step_size=1000, scheduler=s, **kw)
        stirrer.input.table = random.output.table
        module = Unary(np.log, columns=['_3', '_5', '_7'], scheduler=s)
        module.input.table = stirrer.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.log(stirrer.table().to_array()[:, [2, 4, 6]])
        ix1 = stirrer.table().index.to_array()
        res1 = res1[ix1.argsort()]
        res2 = module.table().to_array()
        ix2 =  module.table().index.to_array()
        res2 = res2[ix2.argsort()]
        self.assertEqual(module.name, "unary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_unary3(self):
        self._t_stirred_unary(delete_rows=5)

    def test_unary4(self):
        self._t_stirred_unary(update_rows=5)

    def _t_impl(self, cls, ufunc, mod_name):
        print("Testing", mod_name)
        s = self.scheduler()
        random = RandomTable(10, rows=10_000, scheduler=s)
        module = cls(scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = ufunc(random.table().to_array())
        res2 = module.table().to_array()
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

def add_un_tst(k, ufunc):
    cls = func2class_name(k)
    mod_name = k+'_1'
    def _f(self_):
        TestUnary._t_impl(self_, arr.__dict__[cls], ufunc, mod_name)
    setattr(TestUnary, 'test_'+k, _f)

for k, ufunc in unary_dict_gen_tst.items():
    add_un_tst(k, ufunc)

from progressivis.linalg import Arccosh, Invert, BitwiseNot

#@skip
class TestOtherUnaries(ProgressiveTest):
    def test_arccosh(self):
        #from progressivis.linalg import Arccosh
        module_name = "arccosh_1"
        print("Testing", module_name)
        s = self.scheduler()
        random = RandomTable(10, random=lambda x: np.random.rand(x)*10000.0,
                             rows=100_000, scheduler=s)
        module = Arccosh(scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.arccosh(random.table().to_array())
        res2 = module.table().to_array()
        #print(res1)
        #print("=============================")
        #print(res2)
        self.assertEqual(module.name, module_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))
    def test_invert(self):
        #from progressivis.linalg import Invert
        module_name = "invert_1"
        print("Testing", module_name)
        s = self.scheduler()
        random = RandomTable(10, random=lambda x: np.random.randint(100_000, size=x),
                             dtype='int64',
                             rows=100_000, scheduler=s)
        module = Invert(scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.invert(random.table().to_array())
        res2 = module.table().to_array()
        #print(res1)
        #print("=============================")
        #print(res2)
        self.assertEqual(module.name, module_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))
    def test_bitwise_not(self):
        #from progressivis.linalg import Invert
        module_name = 'bitwise_not_1'
        print("Testing", module_name)
        s = self.scheduler()
        random = RandomTable(10, random=lambda x: np.random.randint(100_000, size=x),
                             dtype='int64',
                             rows=100_000, scheduler=s)
        module = BitwiseNot(scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.bitwise_not(random.table().to_array())
        res2 = module.table().to_array()
        #print(res1)
        #print("=============================")
        #print(res2)
        self.assertEqual(module.name, module_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

#@skip
class TestColsBinary(ProgressiveTest):
    def test_cols_binary(self):
        s = self.scheduler()
        cols = 10
        random = RandomTable(cols, rows=100_000, scheduler=s)
        module = ColsBinary(np.add, first=['_3', '_5', '_7'],
                              second=['_4', '_6', '_8'], scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        self.assertListEqual(module.table().columns,
                             ['_3', '_5', '_7'])
        arr = random.table().to_array()
        res1 = np.add(arr[:, [2, 4, 6]],
                      arr[:, [3, 5, 7]])
        res2 = module.table().to_array()
        self.assertEqual(module.name, "cols_binary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_cols_binary2(self):
        s = self.scheduler()
        cols = 10
        random = RandomTable(cols, rows=100, scheduler=s)
        module = ColsBinary(np.add, first=['_3', '_5', '_7'],
                            second=['_4', '_6', '_8'],
                            cols_out=['x', 'y', 'z'],
                            scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        self.assertListEqual(module.table().columns,
                             ['x', 'y', 'z'])

    def t_stirred_cols_binary(self, **kw):
        s = self.scheduler()
        cols = 10
        random = RandomTable(cols, rows=10_000, scheduler=s)
        stirrer = Stirrer(update_column='_3',
                          fixed_step_size=1000, scheduler=s, **kw)
        stirrer.input.table = random.output.table
        module = ColsBinary(np.add, first=['_3', '_5', '_7'],
                              second=['_4', '_6', '_8'], scheduler=s)
        module.input.table = stirrer.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        self.assertListEqual(module.table().columns,
                             ['_3', '_5', '_7'])
        arr = stirrer.table().to_array()
        res1 = np.add(arr[:, [2, 4, 6]],
                      arr[:, [3, 5, 7]])
        ix1 = stirrer.table().index.to_array()
        res1 = res1[ix1.argsort()]
        res2 = module.table().to_array()
        ix2 = module.table().index.to_array()
        res2 = res2[ix2.argsort()]
        self.assertEqual(module.name, "cols_binary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_cols_binary3(self):
        self.t_stirred_cols_binary(delete_rows=5)

    def test_cols_binary4(self):
        self.t_stirred_cols_binary(update_rows=5)

    def _t_impl(self, cls, ufunc, mod_name):
        print("Testing", mod_name)
        s = self.scheduler()
        random = RandomTable(10, rows=10_000, scheduler=s)
        module = cls(first=['_3', '_5', '_7'],
                     second=['_4', '_6', '_8'],
                     cols_out=['x', 'y', 'z'], scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        self.assertListEqual(module.table().columns,
                             ['x', 'y', 'z'])
        arr = random.table().to_array()
        res1 = ufunc(arr[:, [2, 4, 6]],
                      arr[:, [3, 5, 7]])
        res2 = module.table().to_array()
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

def add_cols_bin_tst(c, k, ufunc):
    cls = f"Cols{func2class_name(k)}"
    mod_name = f'cols_{k}_1'
    def _f(self_):
        c._t_impl(self_, arr.__dict__[cls], ufunc, mod_name)
    setattr(c, 'test_'+k, _f)

for k, ufunc in binary_dict_gen_tst.items():
     add_cols_bin_tst(TestColsBinary, k, ufunc)

from progressivis.linalg import ColsLdexp
#@skip
class TestOtherColsBinaries(ProgressiveTest):
    def _t_impl(self, cls, ufunc, mod_name):
        print("Testing", mod_name)
        s = self.scheduler()
        cols = 10
        random = RandomTable(cols, rows=10_000, scheduler=s,
                              random=lambda x: np.random.randint(10, size=x),
                             dtype='int64')
        module = cls(first=['_3', '_5', '_7'],
                     second=['_4', '_6', '_8'],
                     cols_out=['x', 'y', 'z'], scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        self.assertListEqual(module.table().columns,
                             ['x', 'y', 'z'])
        arr = random.table().to_array()
        res1 = ufunc(arr[:, [2, 4, 6]],
                      arr[:, [3, 5, 7]])
        res2 = module.table().to_array()
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_ldexp(self):
        cls, ufunc, mod_name = ColsLdexp, np.ldexp, 'cols_ldexp_1'
        print("Testing", mod_name)
        s = self.scheduler()
        cols = 10
        random = RandomTable(cols, rows=10_000, scheduler=s,
                              random=lambda x: np.random.randint(10, size=x),
                             dtype='int64')
        module = cls(first=['_3', '_5', '_7'],
                     second=['_4', '_6', '_8'],
                     cols_out=['x', 'y', 'z'], scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        self.assertListEqual(module.table().columns,
                             ['x', 'y', 'z'])
        arr = random.table().to_array()
        res1 = ufunc(arr[:, [2, 4, 6]],
                      arr[:, [3, 5, 7]])
        res2 = module.table().to_array()
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))


def add_other_cols_bin_tst(c, k, ufunc):
    cls = f"Cols{func2class_name(k)}"
    mod_name = f"cols_{k}_1"
    def _f(self_):
        c._t_impl(self_, arr.__dict__[cls], ufunc, mod_name)
    setattr(c, f"test_cols_{k}", _f)
    
for k, ufunc in binary_dict_int_tst.items():
    if k == 'ldexp':
        continue
    add_other_cols_bin_tst(TestOtherColsBinaries, k, ufunc)

#@skip
class TestBinary(ProgressiveTest):
    def test_binary(self):
        s = self.scheduler()
        random1 = RandomTable(3, rows=100_000, scheduler=s)
        random2 = RandomTable(3, rows=100_000, scheduler=s)
        module = Binary(np.add, scheduler=s)
        module.input.first = random1.output.table
        module.input.second = random2.output.table        
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.add(random1.table().to_array(),
                      random2.table().to_array())
        res2 = module.table().to_array()
        self.assertEqual(module.name, "binary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_binary2(self):
        s = self.scheduler()
        cols = 10
        random1 = RandomTable(cols, rows=100_000, scheduler=s)
        random2 = RandomTable(cols, rows=100_000, scheduler=s)
        with self.assertRaises(AssertionError):
            module = Binary(np.add, columns=['_3', '_5', '_7'], scheduler=s)

    def test_binary3(self):
        s = self.scheduler()
        random1 = RandomTable(10, rows=100_000, scheduler=s)
        random2 = RandomTable(10, rows=100_000, scheduler=s)        
        module = Binary(np.add, columns={'first': ['_3', '_5', '_7'],
                                         'second': ['_4', '_6', '_8']},
                        scheduler=s)
        module.input.first = random1.output.table
        module.input.second = random2.output.table        
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.add(random1.table().to_array()[:, [2, 4, 6]],
                      random2.table().to_array()[:, [3, 5, 7]])
        res2 = module.table().to_array()
        self.assertEqual(module.name, "binary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def _t_stirred_binary(self, **kw):
        s = self.scheduler()
        random1 = RandomTable(10, rows=100000, scheduler=s)
        random2 = RandomTable(10, rows=100000, scheduler=s)
        stirrer1 = Stirrer(update_column='_3',
                          fixed_step_size=1000, scheduler=s, **kw)
        stirrer1.input.table = random1.output.table
        stirrer2 = Stirrer(update_column='_3',
                          fixed_step_size=1000, scheduler=s, **kw)
        stirrer2.input.table = random2.output.table
        module = Binary(np.add, columns={'first': ['_3', '_5', '_7'],
                                         'second': ['_4', '_6', '_8']},
                        scheduler=s)
        module.input.first = stirrer1.output.table
        module.input.second = stirrer2.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        idx1 = stirrer1.table().index.to_array()
        idx2 = stirrer2.table().index.to_array()
        common = bitmap(idx1)&bitmap(idx2)
        t1 = stirrer1.table().loc[common,:].to_array()[:, [2, 4, 6]]
        t2 = stirrer2.table().loc[common,:].to_array()[:, [3, 5, 7]]
        res1 = np.add(t1, t2)
        res2 = module.table().to_array()
        ix = module.table().index.to_array()
        res2 = res2[ix.argsort()]
        self.assertEqual(module.name, "binary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_stirred_binary1(self):
        self._t_stirred_binary(delete_rows=5)

    def test_stirred_binary2(self):
        self._t_stirred_binary(update_rows=5)

    def _t_impl(self, cls, ufunc, mod_name):
        print("Testing", mod_name)
        s = self.scheduler()
        random1 = RandomTable(3, rows=10_000, scheduler=s)
        random2 = RandomTable(3, rows=10_000, scheduler=s)
        module = cls(scheduler=s)
        module.input.first = random1.output.table
        module.input.second = random2.output.table        
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = ufunc(random1.table().to_array(),
                      random2.table().to_array())
        res2 = module.table().to_array()
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

def add_bin_tst(c, k, ufunc):
    cls = func2class_name(k)
    mod_name = k+'_1'
    def _f(self_):
        c._t_impl(self_, arr.__dict__[cls], ufunc, mod_name)
    setattr(c, 'test_'+k, _f)
    
for k, ufunc in binary_dict_gen_tst.items():
     add_bin_tst(TestBinary, k, ufunc)

#@skip
class TestBinaryTD(ProgressiveTest):
    def test_binary(self):
        s = self.scheduler()
        cols = 3
        random1 = RandomTable(cols, rows=100000, scheduler=s)
        random2 =  RandomDict(cols, scheduler=s)
        module = Binary(np.add, scheduler=s)
        module.input.first = random1.output.table
        module.input.second = random2.output.table        
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.add(random1.table().to_array(),
                      np.array(list(random2.table().values())))
        res2 = module.table().to_array()
        self.assertEqual(module.name, "binary_1")        
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_binary2(self):
        s = self.scheduler()
        cols = 10
        random1 = RandomTable(cols, rows=100_000, scheduler=s)
        random2 = RandomDict(cols, scheduler=s)
        with self.assertRaises(AssertionError):
            module = Binary(np.add, columns=['_3', '_5', '_7'], scheduler=s)

    def test_binary3(self):
        s = self.scheduler()
        cols = 10
        random1 = RandomTable(cols, rows=100_000, scheduler=s)
        random2 = RandomDict(cols, scheduler=s)
        module = Binary(np.add, columns={'first': ['_3', '_5', '_7'],
                                         'second': ['_4', '_6', '_8']},
                        scheduler=s)
        module.input.first = random1.output.table
        module.input.second = random2.output.table        
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.add(random1.table().to_array()[:, [2, 4, 6]],
                      np.array(list(random2.table().values()))[[3, 5, 7]])
        res2 = module.table().to_array()
        self.assertEqual(module.name, "binary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def _t_impl(self, cls, ufunc, mod_name):
        print("Testing", mod_name)
        s = self.scheduler()
        cols = 3
        random1 = RandomTable(3, rows=10_000, scheduler=s)
        random2 = RandomDict(cols, scheduler=s)
        module = cls(scheduler=s)
        module.input.first = random1.output.table
        module.input.second = random2.output.table        
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = ufunc(random1.table().to_array(),
                      np.array(list(random2.table().values())))
        res2 = module.table().to_array()
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

for k, ufunc in binary_dict_gen_tst.items():
     add_bin_tst(TestBinaryTD, k, ufunc)

from progressivis.linalg import Ldexp

#@skip
class TestOtherBinaries(ProgressiveTest):
    def _t_impl(self, cls, ufunc, mod_name):
        print("Testing", mod_name)
        s = self.scheduler()
        random1 = RandomTable(3, rows=100_000, scheduler=s,
                              random=lambda x: np.random.randint(10, size=x),
                             dtype='int64')
        random2 = RandomTable(3, rows=100_000, scheduler=s,
                              random=lambda x: np.random.randint(10, size=x),
                             dtype='int64')
        module = cls(scheduler=s)
        module.input.first = random1.output.table
        module.input.second = random2.output.table        
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = ufunc(random1.table().to_array(),
                      random2.table().to_array())
        res2 = module.table().to_array()
        #print(res1)
        #print("=============================")
        #print(res2)
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))
    def test_ldexp(self):
        cls, ufunc, mod_name = Ldexp, np.ldexp, 'ldexp_1'
        print("Testing", mod_name)
        s = self.scheduler()
        random1 = RandomTable(3, rows=100_000, scheduler=s)
        random2 = RandomTable(3, rows=100_000, scheduler=s,
                              random=lambda x: np.random.randint(10, size=x),
                             dtype='int64')
        module = cls(scheduler=s)
        module.input.first = random1.output.table
        module.input.second = random2.output.table        
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = ufunc(random1.table().to_array(),
                      random2.table().to_array())
        res2 = module.table().to_array()
        #print(res1)
        #print("=============================")
        #print(res2)
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

def add_other_bin_tst(c, k, ufunc):
    cls = func2class_name(k)
    mod_name = k+'_1'
    def _f(self_):
        c._t_impl(self_, arr.__dict__[cls], ufunc, mod_name)
    setattr(c, 'test_'+k, _f)
    
for k, ufunc in binary_dict_int_tst.items():
    if k == 'ldexp':
        continue
    add_other_bin_tst(TestOtherBinaries, k, ufunc)

#@skip
class TestReduce(ProgressiveTest):
    def test_reduce(self):
        s = self.scheduler()
        random = RandomTable(10, rows=100_000, scheduler=s)
        module = Reduce(np.add, scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.add.reduce(random.table().to_array())
        res2 = np.array(list(module.table().values()))
        self.assertEqual(module.name, "reduce_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))
    def test_reduce2(self):
        s = self.scheduler()
        random = RandomTable(10,  rows=100_000, scheduler=s)
        module = Reduce(np.add, columns=['_3', '_5', '_7'], scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.add.reduce(random.table().to_array()[:, [2, 4, 6]])
        res2 = np.array(list(module.table().values()))
        self.assertEqual(module.name, "reduce_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))
    def _t_impl(self, cls, ufunc, mod_name):
        print("Testing", mod_name)
        s = self.scheduler()
        random = RandomTable(10, rows=10_000, scheduler=s)
        module = cls(scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = getattr(ufunc, 'reduce')(random.table().to_array())
        res2 = np.array(list(module.table().values()))
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))


def add_reduce_tst(c, k, ufunc):
    cls = f"{func2class_name(k)}Reduce"
    mod_name = f'{k}_reduce_1'
    def _f(self_):
        c._t_impl(self_, arr.__dict__[cls], ufunc, mod_name)
    setattr(c, f'test_{k}', _f)
    
for k, ufunc in binary_dict_gen_tst.items():
    add_reduce_tst(TestReduce, k, ufunc)

#@skip
class TestCustomFunctions(ProgressiveTest):

    def test_custom_unary(self):
        def custom_unary(x):
            return (x+np.sin(x))/(x+np.cos(x))
        CustomUnary = make_unary(custom_unary)
        s = self.scheduler()
        random = RandomTable(10, rows=100_000, scheduler=s)
        module = CustomUnary(scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.array(module._ufunc(random.table().to_array()), dtype='float64')
        res2 = module.table().to_array()
        self.assertEqual(module.name, "custom_unary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))
    
    def test_custom_binary(self):
        def custom_binary(x, y):
            return (x+np.sin(y))/(x+np.cos(y))
        CustomBinary = make_binary(custom_binary)
        s = self.scheduler()
        random1 = RandomTable(3, rows=100_000, scheduler=s)
        random2 = RandomTable(3, rows=100_000, scheduler=s)
        module = CustomBinary(scheduler=s)
        module.input.first = random1.output.table
        module.input.second = random2.output.table        
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.array(module._ufunc(random1.table().to_array(),
                      random2.table().to_array()), dtype='float64')
        res2 = module.table().to_array()
        self.assertEqual(module.name, "custom_binary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_custom_reduce(self):
        def custom_binary(x, y):
            return (x+np.sin(y))/(x+np.cos(y))
        CustomBinaryReduce = make_reduce(custom_binary)
        s = self.scheduler()
        random = RandomTable(10, rows=100_000, scheduler=s)
        module = CustomBinaryReduce(scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.array(module._ufunc(random.table().to_array()), dtype='float64')
        res2 = np.array(list(module.table().values()))
        self.assertEqual(module.name, "custom_binary_reduce_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

from progressivis.linalg import Arccosh, Invert, BitwiseNot



#@skip
class TestOtherReduces(ProgressiveTest):
    def _t_impl(self, cls, ufunc, mod_name):
        print("Testing", mod_name)
        s = self.scheduler()
        random = RandomTable(3, rows=10_000, scheduler=s, random=lambda x: np.random.randint(10, size=x),
                             dtype='int64')
        module = cls(scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = getattr(ufunc, 'reduce')(random.table().to_array())
        res2 = np.array(list(module.table().values()))
        #print(res1)
        #print("=============================")
        #print(res2)
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))
        self.assertEqual(module.name, mod_name)
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

def add_other_reduce_tst(c, k, ufunc):
    cls = f"{func2class_name(k)}Reduce"
    mod_name = f'{k}_reduce_1'
    def _f(self_):
        c._t_impl(self_, arr.__dict__[cls], ufunc, mod_name)
    setattr(c, f'test_{k}', _f)
    
for k, ufunc in binary_dict_int_tst.items():
    if k == 'ldexp':
        continue
    add_other_reduce_tst(TestOtherReduces, k, ufunc)

#for c in ["TestUnary", "TestBinary", "TestBinaryTD",
#          "TestReduce", "TestCustomFunctions",
#          "TestOtherUnaries", "TestOtherBinaries", "TestOtherReduces"]: del globals()[c]
#@skip
class TestDecorators(ProgressiveTest):

    def test_decorator_unary(self):
        @unary_module
        def CustomUnary(x):
            return (x+np.sin(x))/(x+np.cos(x))
        s = self.scheduler()
        random = RandomTable(10, rows=100_000, scheduler=s)
        module = CustomUnary(scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.array(module._ufunc(random.table().to_array()), dtype='float64')
        res2 = module.table().to_array()
        self.assertEqual(module.name, "custom_unary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_decorator_binary(self):
        @binary_module
        def CustomBinary(x, y):
            return (x+np.sin(y))/(x+np.cos(y))
        s = self.scheduler()
        random1 = RandomTable(3, rows=100_000, scheduler=s)
        random2 = RandomTable(3, rows=100_000, scheduler=s)
        module = CustomBinary(scheduler=s)
        module.input.first = random1.output.table
        module.input.second = random2.output.table        
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.array(module._ufunc(random1.table().to_array(),
                      random2.table().to_array()), dtype='float64')
        res2 = module.table().to_array()
        self.assertEqual(module.name, "custom_binary_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))

    def test_decorator_reduce(self):
        @reduce_module
        def CustomBinaryReduce(x, y):
            return (x+np.sin(y))/(x+np.cos(y))
        s = self.scheduler()
        random = RandomTable(10, rows=100_000, scheduler=s)
        module = CustomBinaryReduce(scheduler=s)
        module.input.table = random.output.table
        pr=Print(proc=self.terse, scheduler=s)
        pr.input.df = module.output.table
        aio.run(s.start())
        res1 = np.array(module._ufunc(random.table().to_array()), dtype='float64')
        res2 = np.array(list(module.table().values()))
        self.assertEqual(module.name, "custom_binary_reduce_1")
        self.assertTrue(np.allclose(res1, res2, equal_nan=True))
