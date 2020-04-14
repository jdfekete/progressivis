"use strict";
var widgets = require('@jupyter-widgets/base');
var _ = require('lodash');
var html_  = require('./sc_template');
var mc2d = require('./multiclass2d');
var er = require('./es6-element-ready');
var mg = require('./module_graph');
var dt = require('./data_table');
require('../css/module-graph.css');
require('datatables/media/css/jquery.dataTables.css');
var sch = require('./sensitive_html');
// See example.py for the kernel counterpart to this file.


// Custom Model. Custom widgets models must at least provide default values
// for model attributes, including
//
//  - `_view_name`
//  - `_view_module`
//  - `_view_module_version`
//
//  - `_model_name`
//  - `_model_module`
//  - `_model_module_version`
//
//  when different from the base class.

// When serialiazing the entire widget state for embedding, only values that
// differ from the defaults will be specified.
var ScatterplotModel = widgets.DOMWidgetModel.extend({
    defaults: _.extend(widgets.DOMWidgetModel.prototype.defaults(), {
        _model_name : 'ScatterplotModel',
        _view_name : 'ScatterplotView',
        _model_module : 'progressivis-nb-widgets',
        _view_module : 'progressivis-nb-widgets',
        _model_module_version : '0.1.0',
        _view_module_version : '0.1.0',
        data : 'Hello Scatterplot!',
	value: '{0}'
    })
});


// Custom View. Renders the widget model.
var ScatterplotView = widgets.DOMWidgetView.extend({
    // Defines how the widget gets rendered into the DOM
    render: function() {
	this.el.innerHTML = html_;
	let that = this;	
	er.elementReady("#prevImages").then((_)=>{
	    mc2d.ready_(that);
	});
        // Observe changes in the value traitlet in Python, and define
        // a custom callback.
        this.model.on('change:data', this.data_changed, this);

    },

    data_changed: function() {
	let val = this.model.get('data');
	mc2d.update_vis(JSON.parse(val));
    }
});


// When serialiazing the entire widget state for embedding, only values that
// differ from the defaults will be specified.
var ModuleGraphModel = widgets.DOMWidgetModel.extend({
    defaults: _.extend(widgets.DOMWidgetModel.prototype.defaults(), {
        _model_name : 'ModuleGraphModel',
        _view_name : 'ModuleGraphView',
        _model_module : 'progressivis-nb-widgets',
        _view_module : 'progressivis-nb-widgets',
        _model_module_version : '0.1.0',
        _view_module_version : '0.1.0',
        data : 'Hello ModuleGraph!'
	//value: '{0}'
    })
});


// Custom View. Renders the widget model.
var ModuleGraphView = widgets.DOMWidgetView.extend({
    // Defines how the widget gets rendered into the DOM
    render: function() {
	this.el.innerHTML = '<svg id="module-graph" width="960" height="500"></svg>';      var that = this;
	er.elementReady("#module-graph").then((_)=>{
	    mg.graph_setup();
	    that.data_changed();
	});
	console.log("REnder ModuleGraphView");
        // Observe changes in the value traitlet in Python, and define
        // a custom callback.
        this.model.on('change:data', this.data_changed, this);

    },

    data_changed: function() {
	console.log("Data changed ModuleGraphView");
	let val = this.model.get('data');
	if(val=='{}') return;
	mg.graph_update(JSON.parse(val));	
	
    }
});

var SensitiveHTMLModel = widgets.DOMWidgetModel.extend({
    defaults: _.extend(widgets.DOMWidgetModel.prototype.defaults(), {
        _model_name : 'SensitiveHTMLModel',
        _view_name : 'SensitiveHTMLView',
        _model_module : 'progressivis-nb-widgets',
        _view_module : 'progressivis-nb-widgets',
        _model_module_version : '0.1.0',
        _view_module_version : '0.1.0',
        data : 'Hello SensitiveHTML!',
	value: '{0}',
	sensitive_css_class: 'aCssClass'
    })
});


// Custom View. Renders the widget model.
var SensitiveHTMLView = widgets.DOMWidgetView.extend({
    // Defines how the widget gets rendered into the DOM
    render: function() {
	this.data_changed();
        // Observe changes in the value traitlet in Python, and define
        // a custom callback.
        this.model.on('change:data', this.data_changed, this);

    },

    data_changed: function() {
	this.el.innerHTML = this.model.get('data');
	let that = this;
	let sensitive = this.model.get('sensitive_css_class');
	er.elementReady('.'+sensitive).then((_)=>{
	    sch.update_cb(that);
	});
    }
});

var DataTableModel = widgets.DOMWidgetModel.extend({
    defaults: _.extend(widgets.DOMWidgetModel.prototype.defaults(), {
        _model_name : 'DataTableModel',
        _view_name : 'DataTableView',
        _model_module : 'progressivis-nb-widgets',
        _view_module : 'progressivis-nb-widgets',
        _model_module_version : '0.1.0',
        _view_module_version : '0.1.0',
        columns: '[a, b, c]',
        data: 'Hello DataTable!',	
	page: '{0}',
	dt_id: 'aDtId'
    })
});


// Custom View. Renders the widget model.
var DataTableView = widgets.DOMWidgetView.extend({
    // Defines how the widget gets rendered into the DOM
    render: function() {
	this.data_changed();
        // Observe changes in the value traitlet in Python, and define
        // a custom callback.
        this.model.on('change:data', this.data_changed, this);

    },

    data_changed: function() {
	let dt_id = this.model.get('dt_id');
	if(document.getElementById(dt_id)==null){
	    this.el.innerHTML = "<table id='"+dt_id+"' class='display' style='width:100%'>";
	}
	let that = this;
	er.elementReady('#'+dt_id).then((_)=>{
	    dt.update_table(that, dt_id);
	});
    }
});



module.exports = {
    ScatterplotModel: ScatterplotModel,
    ScatterplotView: ScatterplotView,
    ModuleGraphModel: ModuleGraphModel,
    ModuleGraphView: ModuleGraphView,
    SensitiveHTMLModel: SensitiveHTMLModel,
    SensitiveHTMLView: SensitiveHTMLView,
    DataTableModel: DataTableModel,
    DataTableView: DataTableView
    };
