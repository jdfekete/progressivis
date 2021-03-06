import logging
import numpy as np
import copy
from ..core.utils import indices_len, fix_loc, filter_cols
from ..core.bitmap import bitmap
from ..table.module import TableModule
from ..table import Table, TableSelectedView
from ..table.dshape import dshape_projection
from ..core.decorators import *
from .. import ProgressiveError, SlotDescriptor
from ..utils.psdict import PsDict
from . import Sample
import pandas as pd
from sklearn.decomposition import IncrementalPCA
from scipy.spatial import distance as dist
import numexpr as ne

logger = logging.getLogger(__name__)

class PPCA(TableModule):
    parameters = [('n_components',  np.dtype(int), 2)]    
    inputs = [SlotDescriptor('table', type=Table, required=True)]
    outputs = [SlotDescriptor('transformer', type=PsDict, required=False)]

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.inc_pca = None # IncrementalPCA(n_components=self.params.n_components)
        self.inc_pca_wtn = None
        self._transformer = PsDict()
        #self.default_step_size = 10000

    def predict_step_size(self, duration):
        p = super().predict_step_size(duration)
        return max(p, self.params.n_components+1)

    def reset(self):
        print("RESET PPCA")
        self.inc_pca = IncrementalPCA(n_components=self.params.n_components)
        self.inc_pca_wtn = None
        if self._table is not None:
            self._table.selection = bitmap()

    def get_data(self, name):
        if name == 'transformer':
            return self._transformer
        return super().get_data(name)

    @process_slot("table", reset_cb="reset")
    @run_if_any
    def run_step(self, run_number, step_size, howlong):
        """
        """    
        with self.context as ctx:
            #import pdb;pdb.set_trace()
            table = ctx.table.data()
            indices = ctx.table.created.next(step_size) # returns a slice
            steps = indices_len(indices)
            if steps < self.params.n_components:
                return self._return_run_step(self.state_blocked, steps_run=0)

            vs = self.filter_columns(table, fix_loc(indices))
            vs = vs.to_array()
            if self.inc_pca is None:
                self.inc_pca = IncrementalPCA(n_components=self.params.n_components)
                self._transformer['inc_pca'] = self.inc_pca
            self.inc_pca.partial_fit(vs)
            if self._table is None:
                self._table = TableSelectedView(table, bitmap(indices))
            else:
                self._table.selection |= bitmap(indices)
            return self._return_run_step(self.next_state(ctx.table), steps_run=steps)

    def create_dependent_modules_buggy(self, atol=0.0, rtol=0.001,
                                 trace=False, threshold=None, resetter=None,
                                 resetter_slot='table'):
        scheduler = self.scheduler()
        with scheduler:
            self.reduced = PPCATransformer(scheduler=scheduler,
                                           atol=atol, rtol=rtol,
                                           trace=trace,
                                           threshold=threshold,
                                           group=self.name)
            self.reduced.input.table = self.output.table
            self.reduced.input.transformer = self.output.transformer
            if resetter is not None:
                resetter = resetter(scheduler=scheduler)
                resetter.input.table = self.output.table
                self.reduced.input.resetter = resetter.output[resetter_slot]
            self.reduced.create_dependent_modules(self.output.table)
    def create_dependent_modules(self, atol=0.0, rtol=0.001,
                                 trace=False, threshold=None, resetter=None,
                                 resetter_slot='table', resetter_func=None):
        s = self.scheduler()
        self.reduced = PPCATransformer(scheduler=s,
                                       atol=atol, rtol=rtol,
                                       trace=trace,
                                       threshold=threshold,
                                       resetter_func=resetter_func,
                                       group=self.name)
        self.reduced.input.table = self.output.table
        self.reduced.input.transformer = self.output.transformer
        if resetter is not None:
            assert callable(resetter_func)
            self.reduced.input.resetter = resetter.output[resetter_slot]
        self.reduced.create_dependent_modules(self.output.table)

class PPCATransformer(TableModule):
    inputs = [SlotDescriptor('table', type=Table, required=True),
              SlotDescriptor('samples', type=Table, required=True),
              SlotDescriptor('transformer', type=PsDict, required=True),
              SlotDescriptor('resetter', type=PsDict, required=False)]    
    outputs = [SlotDescriptor('samples', type=Table, required=False),
               SlotDescriptor('prev_samples', type=Table, required=False)]

    def __init__(self, atol=0.0, rtol=0.001, trace=False, threshold=None,
                 resetter_func=None, **kwds):
        super().__init__(**kwds)
        self._atol = atol
        self._rtol = rtol
        self._trace = trace
        self._trace_df = None
        self._threshold = threshold
        self._resetter_func = resetter_func
        self.inc_pca_wtn = None
        self._table = None
        self._samples = None
        self._samples_flag = False
        self._prev_samples = None
        self._prev_samples_flag = False

    def create_dependent_modules(self, input_slot):
        scheduler = self.scheduler()
        with scheduler:
            self.sample = Sample(samples=100, group=self.name,
                                     scheduler=scheduler)
            self.sample.input.table = input_slot
            self.input.samples = self.sample.output.select

    def trace_if(self, ret, mean, max_, len_):
        if self._trace:
            row = dict(Action="RESET" if ret else "PASS",
                       Mean=mean, Max=max_, Length=len_)
            if self._trace_df is None:
                self._trace_df = pd.DataFrame(row, index=[0])
            else:
                self._trace_df = self._trace_df.append(row, ignore_index=True)
            if self._trace == "verbose":
                print(row)
        return ret

    def needs_reset(self, inc_pca, inc_pca_wtn, input_table, samples):
        resetter = self.get_input_slot('resetter')
        if resetter:
            resetter.clear_buffers()
            if not self._resetter_func(resetter):
                return self.trace_if(False, 0.0, -1.0, len(input_table))
        if self._threshold is not None and len(input_table)>=self._threshold:
            return self.trace_if(False, 0.0, 0.0, len(input_table))
        data = self.filter_columns(input_table, samples).to_array()
        transf_wtn = inc_pca_wtn.transform(data)
        self.maintain_prev_samples(transf_wtn)
        transf_now = inc_pca.transform(data)
        self.maintain_samples(transf_now)
        explained_variance = inc_pca.explained_variance_
        dist = np.sqrt(ne.evaluate("((transf_wtn-transf_now)**2)/explained_variance").sum(axis=1))
        mean = np.mean(dist)
        max_ = np.max(dist)
        ret = mean > self._rtol
        return self.trace_if(ret, mean, max_, len(input_table))
            
    def reset(self):
        if self._table is not None:
            self._table.resize(0)

    def starting(self):
        super().starting()
        samples_slot = self.get_output_slot('samples')
        if samples_slot:
            logger.debug('Maintaining samples')
            self._samples_flag = True
        else:
            logger.debug('Not maintaining samples')
            self._samples_flag = False
        prev_samples_slot = self.get_output_slot('prev_samples')
        if prev_samples_slot:
            logger.debug('Maintaining prev samples')
            self._prev_samples_flag = True
        else:
            logger.debug('Not maintaining prev samples')
            self._prev_samples_flag = False

    def maintain_samples(self, vec):
        if not self._samples_flag:
            return
        if isinstance(self._samples, Table):
            self._samples.loc[:,:] = vec
        else:
            df = self._make_df(vec)
            self._samples = Table(self.generate_table_name('s_ppca'),
                                data=df, create=True)
            
    def maintain_prev_samples(self, vec):
        if not self._prev_samples_flag:
            return
        if isinstance(self._prev_samples, Table):
            self._prev_samples.loc[:,:] = vec
        else:
            df = self._make_df(vec)
            self._prev_samples = Table(self.generate_table_name('ps_ppca'),
                                data=df, create=True)

    def get_data(self, name):
        if name == 'samples':
            return self._samples
        if name == 'prev_samples':
            return self._prev_samples
        return super().get_data(name)

    def _make_df(self, data):
        cols = [f"_pc{i}" for i in range(data.shape[1])]
        return pd.DataFrame(data, columns=cols)

    @process_slot("table", reset_cb="reset")
    @process_slot("samples", reset_if=False)
    @process_slot("transformer", reset_if=False)    
    @run_if_any
    def run_step(self, run_number, step_size, howlong):
        """
        """    
        with self.context as ctx:
            input_table = ctx.table.data()
            indices = ctx.table.created.next(step_size) # returns a slice
            steps = indices_len(indices)
            if steps == 0:
                return self._return_run_step(self.state_blocked, steps_run=0)
            transformer = ctx.transformer.data()
            ctx.transformer.clear_buffers()
            inc_pca = transformer.get('inc_pca')
            ctx.samples.clear_buffers()
            if self.inc_pca_wtn is not None:
                samples = ctx.samples.data()
                if self.needs_reset(inc_pca, self.inc_pca_wtn, input_table, samples):
                    self.inc_pca_wtn = None
                    ctx.table.reset()
                    ctx.table.update(run_number)
                    self.reset()
                    indices = ctx.table.created.next(step_size)
                    steps = indices_len(indices)
                    if steps == 0:
                        return self._return_run_step(self.state_blocked, steps_run=0)
            else:
                self.inc_pca_wtn = copy.deepcopy(inc_pca)
            data = self.filter_columns(input_table, fix_loc(indices)).to_array()
            reduced = inc_pca.transform(data)
            if self._table is None:
                df = self._make_df(reduced)
                self._table = Table(self.generate_table_name('ppca'),
                                    data=df, create=True)
            else:
                self._table.append(reduced)
            return self._return_run_step(self.next_state(ctx.table), steps_run=steps)
