import threading
import datetime
import time

from . import session
from .calibration import *
from .report import *
from .singleaction import *
"""
Functions here are directly called by the socketio object via the decorated
methods. The functions then call the required function split across the various
files for the sake of clarity.
"""


def SocketConnect(socketio):
  """
  Process to execute when client first connects.
  """
  print('Socket connected')
  time.sleep(0.5)
  if session.state == session.STATE_IDLE:
    print('Session is idle')
    ActionComplete(socketio)
  elif session.state == session.STATE_WAIT_USER:
    print("Waiting user with message!")
    MessageUserAction(socketio, session.waiting_msg)

  # Regardless of sever state, emit the confirm message containing the start time
  # of the server
  socketio.emit('confirm',
                {'start': session.start_time.strftime('%Y/%m/%d/ %H:%M:%S')},
                broadcast=True,
                namespace='/sessionsocket')

  ## Update session to treat all cached data as having just updated
  PrepareReportAllCache()  ## In Report

  ## Updating the list of valid session in the system
  update_reference_list()


def ActionComplete(socketio):
  """
  Sending complete signal to client for client to release controls.
  """
  if session.state == session.STATE_IDLE:
    socketio.emit('action-complete',
                  '',
                  namespace='/sessionsocket',
                  broadcast=True)


def RunAction(socketio, msg):
  """
  Processing of user action input
  """
  print('received action signal')
  socketio.emit('action-received',
                '',
                namespace='/sessionsocket',
                boardcast=True)
  session.state = session.STATE_RUN_PROCESS
  if msg['id'] == 'raw-cmd-input':
    RunCmdInput(msg['data'])
  #elif msg['id'] in ['image-setting-clear', 'image-setting-update']:
  #  visual_settings_update(socketio, msg['data'])
  elif msg['id'] == 'run-std-calibration':
    StandardCalibration(socketio, msg['data'])
  elif msg['id'] == 'run-system-calibration':
    SystemCalibration(socketio, msg['data'])
  elif msg['id'] == 'system-calibration-signoff':
    SystemCalibrationSignoff(socketio, msg['data'])
  elif msg['id'] == 'standard-calibration-signoff':
    StandardCalibrationSignoff(socketio, msg['data'])
  elif msg['id'] == 'rerun-single':
    RerunCalibration(socketio, msg['data']['action'], msg['data']['detid'])
  else:
    """
    Defaulting to printing a messeage and leaving
    """
    print(msg)
    time.sleep(5)

  session.state = session.STATE_IDLE
  ActionComplete(socketio)


def RunReport(socketio, msg):
  if msg == 'tileboard-layout':
    ReportTileboardLayout(socketio)
  elif msg == 'readout':
    ReportReadout(socketio)
  elif msg == 'progress':
    ReportProgress(socketio)
  elif msg == 'status':
    ReportSystemStatus(socketio)
  elif msg == 'valid-reference':
    ReportValidReference(socketio)
  elif msg == 'sign-off':
    ReportSignoffType(socketio)
