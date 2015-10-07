from __future__ import absolute_import

import logging
log = logging.getLogger(__name__)

from flask import (
    render_template, request, send_from_directory,
    abort, jsonify, Response, redirect, url_for
)

import sys
from os.path import join, dirname, abspath, normpath, realpath, isdir

from .app import progressivis_bp

SERVER_DIR = dirname(dirname(abspath(__file__)))
JS_DIR = join(SERVER_DIR, 'server/static')

@progressivis_bp.route('/progressivis/ping')
def ping():
    return "pong"

@progressivis_bp.route('/progressivis/static/<path:filename>')
def progressivis_file(filename):
    return flask.send_from_directory(JS_DIR, filename)

@progressivis_bp.route('/')
@progressivis_bp.route('/progressivis/')
def index(*unused_all, **kwargs):
    return render_template('progressivis.html',
                           title="ProgressiVis Modules")

@progressivis_bp.route('/favicon.ico')
@progressivis_bp.route('/progressivis/favicon.ico')
def favicon():
    return send_from_directory(JS_DIR, 'favicon.ico', mimetype='image/x-icon')

@progressivis_bp.route('/progressivis/about.html')
def about(*unused_all, **kwargs):
    return render_template('about.html')

@progressivis_bp.route('/progressivis/contact.html')
def contact(*unused_all, **kwargs):
    return render_template('contact.html')