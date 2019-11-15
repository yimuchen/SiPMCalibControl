## Python process for receving actions to execute.
from flask_socketio import emit
import threading
import datetime
import time
import numpy as np

from .. import socketio


@socketio.on('connect', namespace='/action')
def action_connect():
  print('Action socket connected')
  if True:
    emit('action-complete', '', namespace='/action', broadcast=True)


@socketio.on('run-action-cmd', namespace='/action')
def run_standard_d8(msg):
  print('recieved action signal')
  print(msg)
  time.sleep(5)
  emit('action-complete', '', namespace='/action', broadcast=True)
