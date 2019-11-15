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
def RunAction(msg):
  print('received action signal')
  emit('action-received', '', namespace='/action', boardcast=True)
  if msg['id'] == 'raw-cmd-input':
    RunCmdInput(msg['data'])
  else:
    print(msg)
    time.sleep(5)
  emit('action-complete', '', namespace='/action', broadcast=True)


def RunCmdInput(msg):
  execute_cmd = msg['input']
  socketio.cmd.onecmd( execute_cmd )