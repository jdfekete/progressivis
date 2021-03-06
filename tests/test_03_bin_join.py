from progressivis.table.bin_join import BinJoin
from progressivis import Print
from progressivis.stats import RandomTable, Min
from progressivis.table.dict2table import Dict2Table
from progressivis.core import aio

from . import ProgressiveTest

class TestBinJoin(ProgressiveTest):
    def test_bin_join(self):
        s = self.scheduler()
        random = RandomTable(10, rows=10000, scheduler=s)
        min_1 = Min(name='min_1'+str(hash(random)), columns=['_1'],
                    scheduler=s)
        min_1.input.table = random.output.table
        d2t_1 = Dict2Table(scheduler=s)
        d2t_1.input.dict_ = min_1.output.table
        min_2 = Min(name='min_2'+str(hash(random)), columns=['_2'],
                    scheduler=s)
        min_2.input.table = random.output.table
        d2t_2 = Dict2Table(scheduler=s)
        d2t_2.input.dict_ = min_2.output.table
        bj = BinJoin(scheduler=s)
        bj.input.first = d2t_1.output.table
        bj.input.second = d2t_2.output.table
        pr = Print(proc=self.terse, scheduler=s)
        pr.input.df = bj.output.table
        aio.run(s.start())
        res1 = random.table().min()
        res2 = bj.table().last().to_dict()
        self.assertAlmostEqual(res1['_1'], res2['_1'])
        self.assertAlmostEqual(res1['_2'], res2['_2'])
