from ..core.utils import indices_len, fix_loc
from ..core.bitmap import bitmap
from ..table.module import TableModule
from ..table.table import Table
from ..core.slot import SlotDescriptor
from ..utils.psdict import PsDict
from ..core.decorators import *
import numpy as np

import logging
logger = logging.getLogger(__name__)


class Max(TableModule):
    parameters = [('history', np.dtype(int), 3)]
    inputs = [SlotDescriptor('table', type=Table, required=True)]

    def __init__(self, columns=None, **kwds):
        super(Max, self).__init__(**kwds)
        self._columns = columns
        self.default_step_size = 10000

    def is_ready(self):
        if self.get_input_slot('table').created.any():
            return True
        return super(Max, self).is_ready()

    def reset(self):
        if self._table is not None:
            self._table.fill(-np.inf)

    @process_slot("table", reset_cb="reset")
    @run_if_any
    def run_step(self, run_number, step_size, howlong):
        with self.context as ctx:
            indices = ctx.table.created.next(step_size) # returns a slice
            steps = indices_len(indices)
            input_df = ctx.table.data()
            op = self.filter_columns(input_df, fix_loc(indices)).max(keepdims=False)
            if self._table is None:
                self._table = PsDict(op)
            else:
                for k, v in self._table.items():
                    self._table[k] = np.maximum(op[k], v)
            return self._return_run_step(self.next_state(ctx.table), steps_run=steps)

def maximum_val_id(candidate_val, candidate_id, current_val, current_id):
    if candidate_val > current_val:
        return candidate_val, candidate_id, True
    return current_val, current_id, False

class ScalarMax(TableModule):
    inputs = [SlotDescriptor('table', type=Table, required=True)]

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.default_step_size = 10000
        self._sensitive_ids = {}

    def is_ready(self):
        if self.get_input_slot('table').created.any():
            return True
        return super().is_ready()

    def reset(self):
        if self._table is not None:
            self._table.fill(-np.inf)

    def reset_all(self, slot, run_number):
        slot.reset()
        self.reset()
        slot.update(run_number)

    def are_critical(self, updated_ids, data):
        """
        check if updates invalidate the current max
        """
        for col, id in self._sensitive_ids.items():
            if id not in updated_ids:
                continue
            if data.loc[id, col] < self._table[col]:
                return True
        return False

    def run_step(self, run_number, step_size, howlong):
        slot = self.get_input_slot('table')
        # slot.update(run_number)
        indices = None
        sensitive_ids_bm = bitmap(self._sensitive_ids.values())
        if slot.deleted.any():
            del_ids = slot.deleted.next(as_slice=False)
            if del_ids & sensitive_ids_bm:
                self.reset_all(slot, run_number)
            # else : deletes are not sensitive, just ignore them
        if slot.updated.any():
            sensitive_update_ids = slot.updated.changes & sensitive_ids_bm
            if sensitive_update_ids and self.are_critical(
                    sensitive_update_ids, slot.data()):
                self.reset_all(slot, run_number)
            else:
                # updates are not critical BUT some values
                # might become greater than the current MAX
                # so we will process these updates as creations
                # and we avoid a reset
                indices = slot.updated.next(step_size, as_slice=False)
        if indices is None:
            if not slot.created.any():
                return self._return_run_step(self.state_blocked, steps_run=0)
            indices = slot.created.next(step_size) # returns a slice
        steps = indices_len(indices)
        input_df = slot.data()
        idxop = self.filter_columns(input_df, fix_loc(indices)).idxmax()
        if not self._sensitive_ids:
            self._sensitive_ids.update(idxop)
        if self._table is None:
            op = {k:input_df.loc[i, k] for (k, i) in idxop.items()}    
            self._table = PsDict(op)
        else:
            rich_op = {k:(input_df.loc[i, k], i) for (k, i) in idxop.items()}
            for k, v in self._table.items():
                candidate_val, candidate_id = rich_op[k]
                current_val = self._table[k]
                current_id = self._sensitive_ids[k]
                new_val, new_id, tst = maximum_val_id(candidate_val, candidate_id,
                                                      current_val, current_id)
                if tst:
                    self._table[k] = new_val
                    self._sensitive_ids[k] = new_id
        return self._return_run_step(self.next_state(slot), steps_run=steps)
