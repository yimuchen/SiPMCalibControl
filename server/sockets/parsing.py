import threading
import datetime
import time
import cv2
import io

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
  socketio.emit('action-received',
                '',
                namespace='/sessionsocket',
                boardcast=True)
  session.state = session.STATE_RUN_PROCESS

  ## Standardized calibration sequences. Functions are defined in calibration.py
  if msg['id'] == 'raw-cmd-input':
    RunCmdInput(msg['data'])
  elif msg['id'] == 'run-std-calibration':
    StandardCalibration(socketio, msg['data'])
  elif msg['id'] == 'run-system-calibration':
    SystemCalibration(socketio, msg['data'])
  elif msg['id'].endswith('calibration-signoff'):
    CalibrationSignoff(socketio, msg['data'], msg['id'].startswith('system'))
  elif msg['id'] == 'rerun-single':
    RerunCalibration(socketio, msg['data'])

  ## Algorithm tuning parameters, Functions defined in singleaction.py
  elif msg['id'] == 'image-settings':
    RunImageSettings(socketio, msg['data'])
  elif msg['id'] == 'zscan-settings':
    RunZScanSettings(socketio, msg['data'])
  elif msg['id'] == 'lowlight-settings':
    RunLowlightSettings(socketio, msg['data'])
  elif msg['id'] == 'lumialign-settings':
    RunLumiAlignSettings(socketio, msg['data'])
  elif msg['id'] == 'picoscope-settings':
    RunPicoscopeSettings(socketio, msg['data'])

  ## Defaulting to printing a message and exiting.
  else:
    print(msg)
    time.sleep(5)

  session.state = session.STATE_IDLE
  ActionComplete(socketio)


def RunReport(socketio, msg):

  ## Cache requests, mainly defined in calibration.py
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

  ## Setting request, mainly defined in singleaction.py
  elif msg == 'image-settings':
    ReportImageSettings(socketio)
  elif msg == 'zscan-settings':
    ReportZScanSettings(socketio)
  elif msg == 'lowlight-settings':
    ReportLowlightSettings(socketio)
  elif msg == 'lumialign-settings':
    ReportLumiAlignSettings(socketio)
  elif msg == 'picoscope-settings':
    ReportPicoscopeSettings(socketio)

  ## Defaults to printing a message an exiting.
  else:
    print(msg)
    time.sleep(5)


__default_image_io = io.BytesIO( cv2.imencode('.jpg',
                            cv2.imread('server/static/icon/notdone.jpg', 0 ) )[1] )

def GetCurrentImage():
  while True:
    frame = session.cmd.visual.get_image_bytes()
    yield (b'--frame\r\n'
           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    time.sleep(0.3)


def GetDetectorImage(detid):
  while True:
    if detid in session.visual_cache and len(session.visual_cache[detid]) > 0:
      try:
        frame = session.visual_cache[detid]
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
      except:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + __default_image_io.read() + b'\r\n')
    else:
      yield (b'--frame\r\n'
             b'Content-Type: image/jpeg\r\n\r\n' + __default_image_io.read() + b'\r\n')

    time.sleep(2)  # Update once every 2 second at most
