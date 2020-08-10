import numpy as np
from ..core.utils import indices_len, fix_loc
from ..table.module import TableModule
from ..table.table import Table
from ..table.dshape import dshape_projection
from ..core.decorators import *
from .. import ProgressiveError, SlotDescriptor
from ..utils.psdict import PsDict
from collections import OrderedDict

unary_except = ('arccosh', 'invert', 'isnat', 'modf', 'frexp', 'bitwise_not')
binary_except = ('bitwise_and', 'bitwise_or', 'bitwise_xor', 'divmod', 'gcd',
                 'lcm', 'ldexp', 'left_shift', 'matmul', 'right_shift')

unary_dict = {k:v for(k, v) in np.__dict__.items()
           if k not in unary_except and isinstance(v, np.ufunc) and v.nin==1}
binary_dict = {k:v for(k, v) in np.__dict__.items()
            if k not in binary_except and isinstance(v, np.ufunc) and v.nin==2}
def info():
    print("unary dict", unary_dict)
    print("*************************************************")
    print("binary dict", binary_dict)

class Unary(TableModule):
    inputs = [SlotDescriptor('table', type=Table, required=True)]

    def __init__(self, ufunc, columns=None, **kwds):
        super().__init__(**kwds)
        self._ufunc = ufunc
        self._columns = columns
        self._kwds = {} #self._filter_kwds(kwds, ufunc)

    def reset(self):
        if self._table is not None:
            self._table.resize(0)

    @process_slot("table", reset_cb="reset")
    @run_if_any
    def run_step(self, run_number, step_size, howlong):
        with self.context as ctx:
            data_in = ctx.table.data()
            if self._table is None:
                dshape_ = dshape_projection(data_in, self._columns)
                self._table = Table(self.generate_table_name(f'unary_{self._ufunc.__name__}'),
                                    dshape=dshape_, create=True)
            cols = self.get_columns(data_in)
            if len(cols) == 0:
                return self._return_run_step(self.state_blocked, steps_run=0)
            indices = ctx.table.created.next(step_size)
            steps = indices_len(indices)
            vec = self.filter_columns(data_in, fix_loc(indices)).raw_unary(self._ufunc, **self._kwds)
            self._table.append(vec)
            return self._return_run_step(self.next_state(ctx.table), steps_run=steps)

def make_subclass(super_, cname, ufunc):
    def _init_func(self_, *args, **kwds):
        super_.__init__(self_, ufunc, *args, **kwds)
    cls = type(cname, (super_,), {})
    cls.__init__ = _init_func
    return cls

_g = globals()

for k, v in unary_dict.items():
    name = k.capitalize()
    _g[name] = make_subclass(Unary, name, v)

def _filter_cols(df, columns=None, indices=None):
    """
    Return the specified table filtered by the specified indices and
    limited to the columns of interest.
    """
    if columns is None:
        if indices is None:
            return df
        return df.loc[indices]
    cols = columns
    if cols is None:
        return None
    if indices is None:
        return df[cols]
    return df.loc[indices, cols]

def _binary(tbl, op, other, other_cols=None, **kwargs):
    if other_cols is None:
        other_cols = tbl.columns
    axis = kwargs.pop('axis', 0)
    assert axis == 0
    res = OrderedDict()
    isscalar = (np.isscalar(other) or isinstance(other, np.ndarray))
    for i, col in enumerate(tbl._columns):
        name = col.name
        if isscalar:
            value = op(col, other)
        else:
            name2 = other_cols[i]
            value = op(col, other[name2])
        res[name] = value
    return res

class Binary(TableModule):
    inputs = [SlotDescriptor('first', type=Table, required=True),
              SlotDescriptor('second', type=(Table, PsDict), required=True)]

    def __init__(self, ufunc, columns=None, columns2=None, **kwds):
        super().__init__(**kwds)
        self._ufunc = ufunc
        self._columns = columns 
        self._columns2 = columns2
        self._kwds = {} #self._filter_kwds(kwds, ufunc)

    def reset(self):
        if self._table is not None:
            self._table.resize(0)

    @process_slot("first", "second", reset_cb="reset")
    @run_if_any
    def run_step(self, run_number, step_size, howlong):
        with self.context as ctx:
            data = ctx.first.data()
            data2 = ctx.second.data()
            _t2t = isinstance(data2, Table)
            if _t2t:
                step_size = min(ctx.first.created.length(), ctx.second.created.length(), step_size)
            else:
                step_size = min(ctx.first.created.length(), step_size)
            indices = indices2 = ctx.first.created.next(step_size)
            steps = steps2 = indices_len(indices)
            if _t2t:    
                indices2 = ctx.second.created.next(step_size)
                steps2 = indices_len(indices2)
            else:
                ctx.second.created.next()
            assert steps == steps2
            if steps == 0:
                return self._return_run_step(self.state_blocked, steps_run=0)
            other = _filter_cols(data2, self._columns2, fix_loc(indices2)) if _t2t else data2
            vec = _binary(self.filter_columns(data, fix_loc(indices)), self._ufunc, other, self._columns2, **self._kwds)
            if self._table is None:
                dshape_ = dshape_projection(data, self._columns)
                self._table = Table(self.generate_table_name(f'binary_{self._ufunc.__name__}'),
                                    dshape=dshape_, create=True)            
            self._table.append(vec)
            return self._return_run_step(self.next_state(ctx.first), steps_run=steps)

for k, v in binary_dict.items():
    name = k.capitalize()
    _g[name] = make_subclass(Binary, name, v)

def _reduce(tbl, op, initial, **kwargs):
    res = {}
    for col in tbl._columns:
        cn =  col.name
        res[cn] = op(col.values, initial=initial.get(cn), **kwargs)
    return res


class Reduce(TableModule):
    inputs = [SlotDescriptor('table', type=Table, required=True)]

    def __init__(self, ufunc, columns=None, **kwds):
        assert ufunc.nin == 2
        super().__init__(**kwds)
        self._ufunc = getattr(ufunc, 'reduce')
        self._columns = columns
        self._kwds = {} #self._filter_kwds(kwds, ufunc)

    def reset(self):
        if self._table is not None:
            self._table.clear() # is a PsDict

    @process_slot("table", reset_cb="reset")
    @run_if_any
    def run_step(self, run_number, step_size, howlong):
        with self.context as ctx:
            data_in = ctx.table.data()
            if self._table is None:
                self._table = PsDict()
            cols = self.get_columns(data_in)
            if len(cols) == 0:
                return self._return_run_step(self.state_blocked, steps_run=0)
            indices = ctx.table.created.next(step_size)
            steps = indices_len(indices)
            #import pdb;pdb.set_trace()
            rdict = _reduce(self.filter_columns(data_in, fix_loc(indices)), self._ufunc, self._table, **self._kwds)
            self._table.update(rdict)
            return self._return_run_step(self.next_state(ctx.table), steps_run=steps)

for k, v in binary_dict.items():
    name = f"{k.capitalize()}Reduce"
    _g[name] = make_subclass(Reduce, name, v)
