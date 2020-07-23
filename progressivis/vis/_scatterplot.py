"""Visualize DataFrame columns x,y on the notebook, allowing refreshing."""

import logging

import numpy as np

from progressivis.utils.errors import ProgressiveError
from progressivis.core import SlotDescriptor
from progressivis.table import Table
from progressivis.table.module import TableModule

from progressivis.stats import Histogram2D, Sample
from ..table.range_query_2d import RangeQuery2d
from ..table.bisectmod import _get_physical_table
from ..table import TableSelectedView
from ..core.bitmap import bitmap
from ..io import Variable

logger = logging.getLogger(__name__)


class ScatterPlot(TableModule):
    parameters = [('xmin', np.dtype(float), 0),
                  ('xmax', np.dtype(float), 1),
                  ('ymin', np.dtype(float), 0),
                  ('ymax', np.dtype(float), 1)]
    inputs = [
        # SlotDescriptor('heatmap', type=Table),
        SlotDescriptor('table', type=Table),
        SlotDescriptor('select', type=Table)
    ]

    def __init__(self, x_column, y_column, approximate=False, **kwds):
        super(ScatterPlot, self).__init__(quantum=0.1, **kwds)
        self.x_column = x_column
        self.y_column = y_column
        self._approximate = approximate
        self.input_module = None
        self.input_slot = None
        self.min = None
        self.max = None
        self.histogram2d = None
        self.heatmap = None
        self._json_digest = None
        self.min_value = None
        self.max_value = None
        self.sample = None
        self.select = None
        self.range_query_2d = None

#    def get_data(self, name):
#        return self.get_input_slot(name).data()
#    return super(ScatterPlot, self).get_data(name)

    def table(self):
        return self.get_input_slot('table').data()

    def is_visualization(self):
        return True

    def get_visualization(self):
        return "scatterplot"

    def create_dependent_modules(self, input_module, input_slot,
                                 histogram2d=None, heatmap=None,
                                 sample=True, select=None, **kwds):
        if self.input_module is not None:
            return self
        scheduler = self.scheduler()
        self.input_module = input_module
        self.input_slot = input_slot
        range_query_2d = RangeQuery2d(column_x=self.x_column,
                                      column_y=self.y_column,
                                      group=self.name, scheduler=scheduler,
                                      approximate=self._approximate)
        range_query_2d.create_dependent_modules(input_module,
                                                input_slot,
                                                min_value=False,
                                                max_value=False)
        self.min_value = Variable(group=self.name, scheduler=scheduler)
        self.min_value.input.like = range_query_2d.min.output.table
        range_query_2d.input.lower = self.min_value.output.table
        self.max_value = Variable(group=self.name, scheduler=scheduler)
        self.max_value.input.like = range_query_2d.max.output.table
        range_query_2d.input.upper = self.max_value.output.table
        if histogram2d is None:
            histogram2d = Histogram2D(self.x_column, self.y_column,
                                      group=self.name, scheduler=scheduler)
        histogram2d.input.table = range_query_2d.output.table
        histogram2d.input.min = range_query_2d.output.min
        histogram2d.input.max = range_query_2d.output.max
        # if heatmap is None:
        #    heatmap = Heatmap(group=self.name, # filename='heatmap%d.png',
        #                      history=100, scheduler=scheduler)
        # heatmap.input.array = histogram2d.output.table
        if sample is True:
            sample = Sample(samples=100, group=self.name, scheduler=scheduler)
        elif sample is None and select is None:
            raise ProgressiveError("Scatterplot needs a select module")
        if sample is not None:
            sample.input.table = range_query_2d.output.table
        scatterplot = self
        # scatterplot.input.heatmap = heatmap.output.heatmap
        scatterplot.input.table = input_module.output[input_slot]
        scatterplot.input.select = sample.output.table
        self.histogram2d = histogram2d
        # self.heatmap = heatmap
        self.sample = sample
        self.select = select
        self.min = range_query_2d.min.output.table
        self.max = range_query_2d.max.output.table
        self.range_query_2d = range_query_2d
        self.histogram2d = histogram2d
        # self.heatmap = heatmap
        return scatterplot

    def predict_step_size(self, duration):
        return 1

    def run_step(self, run_number, step_size, howlong):
        return self._return_run_step(self.state_blocked, steps_run=1,
                                     reads=1, updates=1)

    def run(self, run_number):
        super(ScatterPlot, self).run(run_number)
        self._json_digest = self._to_json_impl()

    def to_json(self, short=False):
        if self._json_digest:
            return self._json_digest
        return self._to_json_impl(short)

    def _to_json_impl(self, short=False):
        json = super(ScatterPlot, self).to_json(short, with_speed=False)
        if short:
            return json
        return self.scatterplot_to_json(json, short)

    def _cleanup(self, tsv):
        pht = _get_physical_table(tsv)
        clean_index = [i for i in tsv.index if i in pht.index]
        return TableSelectedView(pht, bitmap(clean_index))

    def scatterplot_to_json(self, json, short):
        with self.lock:
            select = self.get_input_slot('select').data()
            if select is not None:
                # select = self._cleanup(select)
                json['scatterplot'] = select.to_json(orient='split',
                                                     columns=[self.x_column,
                                                              self.y_column])
            else:
                logger.debug('Select data not found')

        # heatmap = self.get_input_module('heatmap')
        return self.histogram2d.heatmap_to_json(json, short)

    def get_image(self, run_number=None):
        heatmap = self.get_input_module('heatmap')
        return heatmap.get_image(run_number)
