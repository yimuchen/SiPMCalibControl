"""
  parsing.py

  Functions here are directly called by the socketio object via the decorated
  methods in the __init__.py file. The parses the socketio data stream, then call
  the required function split across the various files for the sake of clarity.
"""
import threading
import datetime
import time
import cv2
import io

from . import session
from .action import *
from .report import *
from .sync import *


def socket_connect(socketio):
  """
  Process to execute when client first connects. Immediately the system state is
  updated to all clients. All other information will be handled by client
  request. This will also start the socket session for passing through the
  terminal session via the xterm.js socketio interface. The terminal_passthrough
  methods is defined in the sync method
  """
  print('Socket connected')
  sync_system_state(socketio, session.state)
  sync_session_type(socketio, session.session_type)
  sync_cmd_progress(socketio)
  sync_calib_progress(socketio)
  sync_tileboard_type(socketio)

  # Before starting the first instance, we will be resetting the session file
  # descriptor used to monitor the session back to 0 so that the full history
  # will be flushed to the terminal session
  session.session_output_monitor.seek(0)
  print('Starting the terminal background task')
  socketio.start_background_task(terminal_passthrough_output, *[socketio])


def terminal_input(socketio, msg):
  """
  Receiving the user input for the client side terminal session. This is defined in the sync.py file.
  """
  terminal_passthrough_input(socketio, msg)


def resend_sync(socketio, msg):
  """
  Request for resending a sync signal
  """
  if msg == 'state':
    sync_system_state(socketio, session.state)
  elif msg == 'tileboard':
    sync_tileboard_type(socketio)
  elif msg == 'progress':
    sync_calib_progress(socketio)
  else:
    print('Unrecognized request')


def run_action(socketio, msg):
  """
  Processing of user action input. The whole action will wrapped in a try
  statement. In case any exception is raised, the function will still return the
  session into a user useable state, the exception message is passed back to the
  user session for the client to determine how the message should be handled.
  """
  if session.state != session.STATE_IDLE:
    send_error_message(socketio, 'CANNOT RUN ACTION, REQUEST ALREADY IN PLACE')
    return

  sync_system_state(socketio, session.STATE_RUN_PROCESS)

  try:
    ## Standardized calibration sequences. Functions are defined in action.py
    if msg['id'] == 'run-std-calibration':
      run_standard_calibration(socketio, msg['data'])
    elif msg['id'] == 'run-system-calibration':
      run_system_calibration(socketio, msg['data'])
    elif msg['id'].endswith('calibration-signoff'):
      run_calibration_signoff(socketio, msg['data'],
                              msg['id'].startswith('system'))
    elif msg['id'] == 'rerun-single':
      run_process_extend(socketio, msg['data'])
    elif msg['id'] == 'image-settings':
      run_image_settings(socketio, msg['data'])
    elif msg['id'] == 'zscan-settings':
      run_zscan_settings(socketio, msg['data'])
    elif msg['id'] == 'lowlight-settings':
      run_lowlight_settings(socketio, msg['data'])
    elif msg['id'] == 'lumialign-settings':
      run_lumialign_settings(socketio, msg['data'])
    elif msg['id'] == 'picoscope-settings':
      run_picoscope_settings(socketio, msg['data'])
    elif msg['id'] == 'drs-settings':
      run_drs_settings(socketio, msg['data'])
    elif msg['id'] == 'drs-calib':
      run_drs_calib(socketio)  ## Data less command.
    else:
      send_error_message(socketio, f'Unsupported action item {msg["id"]}')
      print(msg)
      time.sleep(5)
  except Exception as e:
    send_error_message(socketio, str(e))

  sync_system_state(socketio, session.STATE_IDLE)


def send_interrupt(socketio):
  """
  Sending effectively the interupt signal to the underlying command line object.
  """
  session_interrupt(socketio)  # action.py


def session_report(msg):
  """
  The handling of report of session data. Most of the data will be handled by the
  report.py file.
  """
  if msg == 'tileboard_layout': return report_tileboard_layout()
  elif msg == 'status': return report_system_status()
  elif msg == 'validreference': return report_valid_reference()
  elif msg == 'useraction': return report_useraction()
  elif msg == 'systemboards': return report_system_boards()
  elif msg == 'standardboards': return report_standard_boards()
  elif msg == 'settings': return report_settings()
  else:
    ## Defaults to printing a message and returning an empty message.
    print(msg)
    return {}


def get_file_data(process, filename):
  """
  Returning the cached data of the a the given process defined by the process. To
  help with code structure uniformity. This function will just be a thin wrapper
  around the report_cached_data method defined in the report.py file (since the
  function formatting is similar to a typical reporting process)
  """
  return report_file_data(process, filename.replace('@', '/'))


def get_detid_data(process, detid):
  """
  Returning the cached data of the a the given process defined by the process. To
  help with code structure uniformity. This function will just be a thin wrapper
  around the report_cached_data method defined in the report.py file (since the
  function formatting is similar to a typical reporting process)
  """
  return report_detid_data(process, detid)


def make_jpeg_image_byte(image):
  """
  Helper function to make the a byte stream as a string representing an image
  object.
  """
  return (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + image + b'\r\n')


"""
Definition of static images to return if image is not available.
"""
__default_image_io = io.BytesIO(
    cv2.imencode('.jpg', cv2.imread('server/static/icon/notdone.jpg', 0))[1])
__default_yield = make_jpeg_image_byte(__default_image_io.read())


def current_image_bytes():
  """
  Returning the byte string of the current image stored in the visual system's
  buffer. The formatting code is borrowed from here: Notice that the framerate
  of how fast the image is updated is defined here.

  Reference: https://medium.com/datadriveninvestor/
  video-streaming-using-flask-and-opencv-c464bf8473d6
  """
  while True:  ## This function will always generate a return
    try:
      yield make_jpeg_image_byte(session.cmd.visual.get_image_bytes())
    except Exception as e:
      yield __default_yield

    time.sleep(0.1)


#def get_visual_bytes(detid):
#  """
#  Getting the detector image used for visual alignment. The calibration session
#  should store a jpeg byte stream each time a visual alignment is performed. In
#  case the image doesn't exists, either because the visual alignment failed or
#  the visual alignment hasn't been performed. Return the default image of a not
#  found status.
#  """
#  while True:
#    if detid in session.visual_cache and len(session.visual_cache[detid]) > 0:
#      try:
#        yield make_jpeg_image_byte(session.visual_cache[detid])
#      except:
#        yield __default_yield
#    else:
#      yield __default_yield
#    time.sleep(0.1)
#
#def default_image_bytes():
#  return __default_yield
