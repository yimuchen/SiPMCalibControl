"""
  sync.py

  This file contains the functions that handles sending information to the
  clients that should be initiated from the server side: Things like the changing
  of the state of the calibration session, message to be passed to the user for
  display, the calibration parameter settings and such. All such function to
  start with the prefix `sync_` to help distinguish function types.

  A second type of soft, sync message initiated from the server would be the
  `send_` type. While this is sent to the client, it doesn't affect code
  functionality, and can be safely ignore by the client if needed.

  Additional helper function are help with common sync function.

  For information sent to client-side by client request, see the file report.
"""
## Commonly used functions
from . import session
from .report import *

import time


def send_sync_signal(socketio, sync_id, msg):
  """
  All sync signals will use the same namespace and will **always** be
  broadcasted. This helper function helps enforce this behavior, and help with
  reducing the verbosity of function calls.
  """
  socketio.emit(sync_id, msg, namespace='/sessionsocket', boardcast=True)


def sync_system_state(socketio, new_state):
  """
  Updating the system state of the current calibration session. The various
  action function should all call this function when making changes to the
  system states.
  """
  session.state = new_state
  send_sync_signal(socketio, 'sync-system-state', session.state)


def sync_session_type(socketio, new_type):
  """
  Updating the system session type of the on-going calibration session. This
  should be the method used by the various action method.
  """
  session.session_type = new_type
  send_sync_signal(socketio, 'sync-session-type', session.session_type)


def sync_calibration_settings(socketio):
  """
  Sending a sync signal to update all clients that the system settings has
  changed. This should be call at the end of every run_*_settings function. Here
  we are borrowing the report_settings function to reduce code verbosity.
  """
  send_sync_signal(socketio, 'sync-settings', report_settings())


def wait_user_action(socketio, msg):
  """
  Setting to system state to waiting for user action with an accompanying
  message. The message is not sent directly, instead relying of client side for
  display. This is what should be used by the high level functions if one need to
  halt the system for user input.
  """
  sync_system_state(socketio, session.STATE_WAIT_USER)
  session.waiting_msg = msg
  while (session.state == session.STATE_WAIT_USER):
    time.sleep(0.1)  ## Updating every 0.1 seconds


def complete_user_action(socketio):
  """
  Basically terminating the wait user state. Function should be called when the
  server receives the complete user actin signal. It also wipes the message that
  is stored in session memory.
  """
  print('User action completed')
  sync_system_state(socketio, session.STATE_RUN_PROCESS)
  session.waiting_msg = ""


def ReturnClearExisting(socketio):
  socketio.emit('clear-display', '', broadcast=True, namespace='/sessionsocket')


def send_display_message(socketio, msg):
  """
  Sending a single string to handled by the client to be displayed. Notice that
  these strings are not messages stored server side.
  """
  socketio.emit('display-message',
                msg,
                broadcast=True,
                namespace='/sessionsocket')


def send_command_message(socketio, msg):
  """
  Sending the clients the string of the current command that is being run.
  """
  socketio.emit('command-message',
                msg,
                broadcast=True,
                namespace='/sessionsocket')

