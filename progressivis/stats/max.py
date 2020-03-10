
from progressivis.utils.synchronized import synchronized
from progressivis.core.utils import indices_len, fix_loc
from progressivis.table.module import TableModule
from progressivis.table.table import Table
from progressivis.core.slot import SlotDescriptor
from ..utils.psdict import PsDict
import numpy as np

import logging
logger = logging.getLogger(__name__)


class Max(TableModule):
    parameters = [('history', np.dtype(int), 3)]

    def __init__(self, columns=None, **kwds):
        self._add_slots(kwds,'input_descriptors',
                        [SlotDescriptor('table', type=Table, required=True)])
        super(Max, self).__init__(**kwds)
        self._columns = columns
        self.default_step_size = 10000

    def is_ready(self):
        if self.get_input_slot('table').created.any():
            return True
        return super(Max, self).is_ready()


    async def run_step(self,run_number,step_size,howlong):
        dfslot = self.get_input_slot('table')
        dfslot.update(run_number)
        if dfslot.updated.any() or dfslot.deleted.any():
            dfslot.reset()
            if self._table is not None:
                self._table.fill(-np.inf)
            dfslot.update(run_number)
        indices = dfslot.created.next(step_size) # returns a slice
        steps = indices_len(indices)
        if steps==0:
            return self._return_run_step(self.state_blocked, steps_run=0)
        input_df = dfslot.data()
        op = self.filter_columns(input_df, fix_loc(indices)).max(keepdims=True)
        if self._table is None:
            self._table = PsDict(op)
        else:
            for k, v in self._table.items():
                self._table[k] = np.maximum(op[k], v)
        return self._return_run_step(self.next_state(dfslot), steps_run=steps)
