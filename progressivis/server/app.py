"""
Flask server for ProgressiVis.

The server provides the main user interface for progressivis.
It serves pages related to the scheduler and modules.
For all the modules, it provides access to their internal state and
to the tables it maintains.

When the scheduler is running, the server implements a simple protocol.
Each web page shown on a browser also opens a socketio connection.
The server sends one message "tick" throught the socketio when the served entity is been changed.
When the client/browser receives it, it sends a request to get the data from the module. This
request is made through the socketio directly, and the value is returned, allowing the next tick
to be sent by the server. This mechansim is meant to get a responsive browser with asynchronous
updates.  Between the time the "tick" is received by the browser and the value is sent back by
the server, many iterations may have been run.  The browser receives data as fast as it can, and
the server sends a simple notification and serves the data as fast as it can.
"""
from __future__ import absolute_import, division, print_function

import time
import logging
import six
from functools import partial

from six import StringIO

import numpy as np

from flask import Flask, Blueprint, request, json as flask_json
from flask.json import JSONEncoder
from flask_socketio import SocketIO, join_room, rooms, send
import eventlet

from progressivis import Scheduler, Module


logger = logging.getLogger(__name__)

# pylint: disable=invalid-name
socketio = None

class JSONEncoder4Numpy(JSONEncoder):
    "Encode numpy objects"
    def default(self, o):
        "Handle default encoding."
        if isinstance(o, float) and np.isnan(o):
            return None
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return JSONEncoder.default(self, o)

class ProgressivisBlueprint(Blueprint):
    "Blueprint for ProgressiVis"
    def __init__(self, *args, **kwargs):
        super(ProgressivisBlueprint, self).__init__(*args, **kwargs)
        self._sids_for_path = {}
        self._run_number_for_sid = {}
        self.scheduler = None
        self.start_logging()

    def start_logging(self):
        "Start logging out"
        out = self._log_stream = StringIO()
        out.write("<html><body><table>"
                  "<tr><th>Time</th><th>Name</th><th>Level</th><th>Message</th></tr>\n")
        streamhandler = logging.StreamHandler(stream=self._log_stream)
        streamhandler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('<tr><td>%(asctime)s</td>'
                                      '<td>%(name)s</td>'
                                      '<td>%(levelname)s</td>'
                                      '<td>%(message)s</td></tr>\n')
        streamhandler.setFormatter(formatter)
        logging.getLogger("progressivis").addHandler(streamhandler)
        logging.getLogger("progressivis").setLevel(logging.DEBUG)

    def setup(self, scheduler):
        "Setup the connection with the scheduler"
        self.scheduler = scheduler
        # pylint: disable=protected-access
        self.scheduler._tick_proc = self.tick_scheduler

    def register_module(self, path, sid):
        "Register a module with a specified path"
        if sid in self._run_number_for_sid:
            self._run_number_for_sid[sid] = 0
            return
        print('Register module:', path, 'sid:', sid)
        self._run_number_for_sid[sid] = 0
        if path in self._sids_for_path:
            sids = self._sids_for_path[path]
            sids.add(sid)
        else:
            self._sids_for_path[path] = set([sid])

    def unregister_module(self, sid):
        "Unregister a specified path"
        if sid in self._run_number_for_sid:
            del self._run_number_for_sid[sid]
        for sids in self._sids_for_path.values():
            if sid in sids:
                sids.remove(sid)
                return

    def sids_for_path(self, path):
        "Get the sid list from a path"
        return self._sids_for_path.get(path, set())

    def sid_run_number(self, sid):
        "Return the last run_number sent for the specified sid"
        return self._run_number_for_sid.get(sid, 0)

    def _prevent_tick(self, sid, run_number, ack):
        if ack:
            self._run_number_for_sid[sid] = run_number
        else:
            logging.debug('Ack not well received')

    def reset_sid(self, sid):
        "Resets the sid to 0 to stop sending ticks for that sid"
        #print('Reseting sid', sid)
        self._run_number_for_sid[sid] = 0

    def emit_tick(self, path, run_number):
        "Emit a tick unless it has not been acknowledged"
        sids = self.sids_for_path(path)
        for sid in sids:
            if self._run_number_for_sid[sid] == 0:
                #print('Emiting tick for', sid, 'in path', path)
                socketio.emit('tick', {'run_number': run_number}, room=sid,
                              callback=partial(self._prevent_tick, sid, run_number))
            #else:
            #    #print('No tick for', sid, 'in path', path)
        time.sleep(0) # yield thread

    def tick_scheduler(self, scheduler, run_number):
        "Run at each tick"
        # pylint: disable=unused-argument
        self.emit_tick('scheduler', run_number)

    def step_tick_scheduler(self, scheduler, run_number):
        "Run at each step"
        scheduler.stop()
        self.emit_tick('scheduler', run_number)

    def step_once(self):
        "Run once"
        self.scheduler.start(tick_proc=self.step_tick_scheduler) # i.e. step+write_to_path

    def start(self):
        "Run when the scheduler starts"
        self.scheduler.start(tick_proc=self.tick_scheduler)

    def tick_module(self, module, run_number):
        "Run when a module has run"
        # pylint: disable=no-self-use
        self.emit_tick(module.id, run_number)

    def get_log(self):
        "Return the log"
        self._log_stream.flush()
        return self._log_stream.getvalue().replace("\n", '<br>')


progressivis_bp = ProgressivisBlueprint('progressivis.server',
                                        'progressivis.server',
                                        static_folder='static',
                                        static_url_path='/progressivis/static',
                                        template_folder='templates')


def path_to_module(path):
    """
    Return a module given its path, or None if not found.
    A path is the module id alone, or the toplevel module module id
    followed by modules stored inside it.

    For example 'scatterplot/range_query' will return the range_query
    module used as dependent module of scatterplot.
    """
    scheduler = progressivis_bp.scheduler
    #print('module_path(%s)'%(path))
    ids = path.split('/')
    module = scheduler.module[ids[0]]
    if module is None:
        return None
    for subid in ids[1:]:
        if not hasattr(module, subid):
            return None
        module = getattr(module, subid)
        if not isinstance(module, Module):
            return None
    return module

def _on_join(json):
    if json.get("type") != "ping":
        logging.error("Expected a ping message")
    path = json["path"]
    print('socketio join received for "%s"'% path)
    join_room(path)
    #print('socketio Roomlist:', rooms())
    return {'type': 'pong'}

def _on_connect():
    print('socketio connect ', request.sid)

def _on_disconnect():
    progressivis_bp.unregister_module(request.sid)
    print('socketio disconnect ', request.sid)

def _on_start():
    scheduler = progressivis_bp.scheduler
    if scheduler.is_running():
        return {'status': 'failed',
                'reason': 'scheduler is already running'}
    progressivis_bp.start()
    return {'status': 'success'}

def _on_stop():
    scheduler = progressivis_bp.scheduler
    if not scheduler.is_running():
        return {'status': 'failed',
                'reason': 'scheduler is not is_running'}
    scheduler.stop()
    return {'status': 'success'}

def _on_step():
    scheduler = progressivis_bp.scheduler
    if scheduler.is_running():
        send({'status': 'failed',
              'reason': 'scheduler is is_running'})
    progressivis_bp.step_once()
    send({'status': 'success'})

def _on_scheduler(short=False):
    scheduler = progressivis_bp.scheduler
    #print('socketio scheduler called')
    progressivis_bp.register_module('scheduler', request.sid)
    #print(progressivis_bp._sids_for_path)
    assert request.sid in progressivis_bp.sids_for_path('scheduler')
    return scheduler.to_json(short)

def _on_module(path):
    #print('on_module', path)
    module = path_to_module(path)
    if module is None:
        return {'status': 'failed',
                'reason': 'unknown module %s'%path}
    progressivis_bp.register_module(module.id, request.sid)
    module.set_end_run(progressivis_bp.tick_module) # setting it multiple time is ok
    return module.to_json()

def _on_df(path):
    (mid, slot) = path.split('/')
    #print('socketio Getting module', mid, 'slot "'+slot+'"')
    module = path_to_module(mid)
    if module is None:
        return {'status': 'failed',
                'reason': 'invalid module'}
    df = module.get_data(slot)
    if df is None:
        return {'status': 'failed',
                'reason': 'invalid data'}
    return {'columns':['index']+df.columns}

def _on_quality(mid):
    #print('socketio quality for', mid)
    module = path_to_module(mid)
    if module is None:
        return {'status': 'failed',
                'reason': 'invalid module'}
    slot = '_trace'
    #print('socketio Getting slot "'+slot+'"')
    df = module.get_data(slot)
    if df is None:
        return {'status': 'failed',
                'reason': 'invalid data'}
    qual = df['quality'].values
    return {'index':df.index.values, 'quality': qual}

def _on_logger():
    managers = logging.Logger.manager.loggerDict
    ret = []
    for (module, log) in six.iteritems(managers):
        if isinstance(log, logging.Logger):
            ret.append({'module': module,
                        'level': logging.getLevelName(log.getEffectiveLevel())})
    def _key_log(a):
        return a['module'].lower()
    ret.sort(key=_key_log)
    return {'loggers': ret}


def app_create(config="settings.py", scheduler=None):
    "Create the application"
    if scheduler is None:
        scheduler = Scheduler.default
    app = Flask('progressivis.server')
    if isinstance(config, str):
        app.config.from_pyfile(config)
    elif isinstance(config, dict):
        app.config.update(config)
    app.json_encoder = JSONEncoder4Numpy
    app.register_blueprint(progressivis_bp)
    progressivis_bp.setup(scheduler)
    return app

def start_server(scheduler=None, debug=False):
    "Start the server"
    # pylint: disable=global-statement
    global socketio
    eventlet.monkey_patch() # see https://github.com/miguelgrinberg/Flask-SocketIO/issues/357

    if scheduler is None:
        scheduler = Scheduler.default
    print('Scheduler %s has %d modules' % (scheduler.__class__.__name__, len(scheduler)))
    app = app_create(scheduler)
    app.debug = debug
    socketio = SocketIO(app, json=flask_json)
    socketio.on_event('connect', _on_connect)
    socketio.on_event('disconnect', _on_disconnect)
    socketio.on_event('join', _on_join)
    socketio.on_event('/progressivis/scheduler/start', _on_start)
    socketio.on_event('/progressivis/scheduler/step', _on_step)
    socketio.on_event('/progressivis/scheduler/stop', _on_stop)
    socketio.on_event('/progressivis/scheduler', _on_scheduler)
    socketio.on_event('/progressivis/module/get', _on_module)
    socketio.on_event('/progressivis/module/df', _on_df)
    socketio.on_event('/progressivis/module/quality', _on_quality)
    socketio.on_event('/progressivis/logger', _on_logger)
    socketio.run(app)

def stop_server():
    "Stop the server"
    socketio.stop()
