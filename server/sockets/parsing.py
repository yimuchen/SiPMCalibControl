import threading
import datetime
import time

from . import session
from .settings import *
from .calibration import *
"""
Functions here are directly called by the socketio object via the decorated
methods. The functions then call the required function split across the various
files for the sake of clarity.
"""


def ActionComplete(socketio):
  if session.state == session.STATE_IDLE:
    socketio.emit('action-complete', '', namespace='/action', broadcast=True)


def ActionConnect(socketio):
  print('Action socket connected')
  time.sleep(0.5)
  if session.state == session.STATE_IDLE:
    print('Session is idle')
    ActionComplete(socketio)
  elif session.state == session.STATE_WAIT_USER:
    print("Waiting user with message!");
    MessageUserAction(socketio, session.waiting_msg)


def RunAction(socketio, msg):
  print('received action signal')
  socketio.emit('action-received', '', namespace='/action', boardcast=True)
  session.state = session.STATE_RUN_PROCESS
  if msg['id'] == 'raw-cmd-input':
    RunCmdInput(msg['data'])
  elif msg['id'] in ['image-setting-clear', 'image-setting-update']:
    visual_settings_update(socketio, msg['data'])
  elif msg['id'] == 'std-calibration':
    StandardCalibration(socketio, msg['data'])

  else:
    print(msg)
    time.sleep(5)

  session.state = STATE_IDLE
  ActionComplete(socketio)


def MonitorConnect(socketio):
  print('Monitor client connected')

  socketio.emit('confirm',
                {'start': session.start_time.strftime('%Y/%m/%d/ %H:%M:%S')},
                broadcast=True,
                namespace='/monitor')

  ## Getting system settings
  visual_settings_update(socketio, {})

  ## Updating the existing cache
  StartReadoutMonitor(socketio);

  ## Starting the continuous monitoring thread.
  if not session.monitor_thread:
    print("Starting Thread")
    session.monitor_thread = threading.Thread(target=monitor_update,
                                              args=[socketio])
    session.monitor_thread.start()


def RunMonitor(socketio, msg):
  print('received request signal')
  if msg == 'tileboard-layout':
    ReturnTileboardLayout(socketio)
  elif msg == 'readout':
    ReturnReadoutUpdate(socketio)


def RunCmdInput(msg):
  execute_cmd = msg['input']
  session.cmd.onecmd(execute_cmd)
