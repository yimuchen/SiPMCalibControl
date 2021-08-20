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
import select
import threading
import ctlcmd.cmdbase as cmdbase


def send_sync_signal(socketio, sync_id, msg):
  """
  All sync signals will use the same namespace and will **always** be
  broadcasted. This helper function helps enforce this behavior, and help with
  reducing the verbosity of function calls.
  """
  socketio.emit(sync_id, msg, namespace='/sessionsocket', boardcast=True)


## Some basic method for handling running commands and such
def run_single_cmd(socketio, cmd):
  """
  Running a single command. First we make sure the that the system is not already
  running a command (wait indefinitely for the previous command to finish). After
  which we run the underlying CMD methods until the method has been properly
  processed. The return value of the command will be returned so that additional
  parsing can be performed.
  """
  while session.state == session.STATE_EXEC_CMD:
    time.sleep(1)  # Waiting indefinitely for the current command to finish

  # static variable to check if command finished.
  run_single_cmd.is_running = True

  def run_with_save(cmd):
    "A thin wrapper function for running the line."
    cmd = session.cmd.precmd(cmd)
    sig = session.cmd.onecmd(cmd)
    sig = session.cmd.postcmd(sig, cmd)
    session.cmd.stdout.flush()  # Flushing the output.
    session.run_results = session.cmd.last_cmd_status

  def update_loop():
    while run_single_cmd.is_running:
      time.sleep(0.05)
      sync_cmd_progress(socketio)

  ## Strange syntax to avoid string splitting  :/
  prev_state = session.state
  sync_system_state(socketio, session.STATE_EXEC_CMD)
  send_display_message(socketio, f'running command "{cmd}"')
  cmd_thread = threading.Thread(target=run_with_save, args=(cmd, ))
  cmd_thread.start()

  # Starting the monitor thread to update the current command progress
  update_thread = threading.Thread(target=update_loop)
  update_thread.start()

  ## Having the process finish
  cmd_thread.join()
  run_single_cmd.is_running = False
  update_thread.join()

  ## One last update to ensure that things have finished.
  sync_cmd_progress(socketio,
                    done=True,
                    error=session.run_results != cmdbase.controlcmd.EXIT_SUCCESS)
  sync_system_state(socketio, prev_state)
  return session.run_results


def sync_cmd_progress(socketio, done=False, error=False):
  """
  Returning a 2-tuple of numbers indicating the progress of the current command.
  to be displayed client side. In case done is set to True, then the command will
  always be return (1,1) or (-1,-1) used to indicate that the command has
  completed (or has erred), otherwise it will look at the current session output
  monitor file and find the string typically used to indicate the command
  progress.

  The code used for opening the output file and loop backward until the first new
  line character can be found here: https://stackoverflow.com/questions/46258499/
  how-to-read-the-last-line-of-a-file-in-python
  """
  pattern = re.compile(r'.*\[\s*(\d+)\/\s*(\d+)\]\[.....%\].*')

  def emit(x):
    send_sync_signal(socketio, 'sync-cmd-progress', x)

  if done:  # Early exists for if the command has be compelted
    if error:
      emit([-1, -1])
      return
    else:
      emit([1, 1])
      return

  if session.state != session.STATE_EXEC_CMD:
    emit([1,1])
    return

  line = ''
  with open(session.session_output_monitor.name, 'rb') as f:
    f.seek(-2, os.SEEK_END)
    char = f.read(1)
    while char != b'\n' and char != b'\r' and f.tell() != 0:
      f.seek(-2, os.SEEK_CUR)
      char = f.read(1)

    line = f.readline().decode()  # Getting the last line in the output.

  match = pattern.match(line)
  if match and len(match.groups()) == 2:
    emit([int(match[1]), int(match[2])])
  else:  # Bad matching, don't send new update signal.
    pass  ## Don't try to wipe or update


def sync_calib_progress(socketio):
  """
  Passing the signal to the client that the current calibration status has been
  updated.
  """
  print(session.progress_check)
  send_sync_signal(socketio, 'sync-calib-progress', session.progress_check)


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


def sync_tileboard_type(socketio, clear=False):
  """
  Sending the sync signal to indicate which tileboard is currently being stored
  in the calibration session. The client is responsible for generating the
  required HTML elements and additional queries regarding the display results.
  """
  if clear:
    send_sync_signal(socketio, 'sync-tileboard-type', '')
  else:
    send_sync_signal(socketio, 'sync-tileboard-type',
                     session.cmd.board.boardtype)


def wait_user_action(socketio, msg):
  """
  Setting to system state to waiting for user action with an accompanying
  message. The message is not sent directly, instead relying of client side for
  display. This is what should be used by the high level functions if one need to
  halt the system for user input.
  """
  sync_system_state(socketio, session.STATE_WAIT_USER)
  session.waiting_msg = msg
  time.sleep(0.1)  # Sleep first to system to stabilize
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


def send_display_message(socketio, msg):
  """
  Sending a single string to handled by the client to be displayed. Notice that
  these strings are not messages stored server side.
  """
  socketio.emit('display-message',
                msg,
                broadcast=True,
                namespace='/sessionsocket')


def send_error_message(socketio, msg):
  """
  Sending a single string to handled by the client to be displayed. Notice that
  these strings are not messages stored server side.
  """
  socketio.emit('display-error', msg, broadcast=True, namespace='/sessionsocket')


def terminal_passthrough_output(socketio):
  """
  Passing though any updates in the terminal io to the client side. The main
  reference for using this method can be found in the pyxtermjs package [1]:
  [1] https://github.com/cs01/pyxtermjs
  """
  __max_read_length = 1024 * 20
  __timeout_sec = 0
  while True:
    socketio.sleep(0.01)  # Updating every 10ms
    # Checking that the output is ready for reading
    (data_ready, _, _) = select.select([session.session_output_monitor.fileno()],
                                       [], [], __timeout_sec)
    if data_ready:
      output = os.read(session.session_output_monitor.fileno(),
                       __max_read_length).decode()
      if output:  # Only sending non-trivial outputs
        socketio.emit("xtermoutput", {"output": output.replace('\n', '\n\r')},
                      namespace="/sessionsocket")


"""
SYNCING REQUIRED FOR TERMINAL INPUT
"""


def __shift_left():  # Shifing the cursor to the left
  session.input_buffer_index = max([session.input_buffer_index - 1, 0])


def __shift_right():
  m = len(session.input_buffer)
  session.input_buffer_index = min([session.input_buffer_index + 1, m])


def __buffer_string():
  """
  Returning a line that clears the index
  """
  line = '\x1b[2K\r'  # Clearing the line and returning to beginning
  line += session.cmd.prompt  # Always print the prompt
  line += session.input_buffer  # Flush the current buffer to the input
  if len(
      session.input_buffer) > session.input_buffer_index:  # Returning the base
    line += '\b' * (len(session.input_buffer) - session.input_buffer_index)
  return line


def __insert_char(x):
  """Inserting string at current index position"""
  buff = session.input_buffer
  idx = session.input_buffer_index
  session.input_buffer = buff[:idx] + x + buff[idx:]
  session.input_buffer_index = idx + 1
  print(session.input_buffer)


def __clear_buffer():
  """clearing the input buffer in the system"""
  session.input_buffer = ''
  session.input_buffer_index = 0


def terminal_passthrough_input(socketio, msg):
  """
  Parsing the user input character to the main input and output file descriptors.

  This function will modify the session line buffer according to the input key
  stroke, and send a corrected string to the client side to correctly display the
  results. Notice that the currently line will NOT be committed to the session
  input buffer until a '\r' return carriage has been detected.

  The input will be locked until while the session is actively working on a
  command, interupt signals will not be handled through the dummy terminal
  interface.
  """
  if session.state != session.STATE_IDLE:
    return  # Do nothing.

  char = msg['input']

  def emit_str(s):
    socketio.emit('xtermoutput', {'output': s}, namespace='/sessionsocket')

  # Shorter alias
  buff = session.input_buffer
  idx = session.input_buffer_index
  if char == '\b':
    session.input_buffer = buff[:idx - 1] + buff[idx:]
    __shift_left()
  elif char == '\r':  # Handling the return carriage
    emit_str('\n\r')  # New line and return to front of the terminal
    cmd = session.input_buffer
    __clear_buffer()
    run_single_cmd(socketio, cmd)  # Running until the session
    # small wait longer than the output update window to ensure that prompt
    # doesn't appear before the main command output
    time.sleep(0.1)
  elif len(char) == 3:  ## Potential arrow key
    if ord(char[0]) == 27 and ord(char[1]) == 91 and ord(char[2]) == 68:
      __shift_left()  # Left arrow key
    elif ord(char[0]) == 27 and ord(char[1]) == 91 and ord(char[2]) == 67:
      __shift_right()  # Right arrow key
    else:
      pass
  elif char == chr(21):  # Ctl+u
    __clear_buffer()
  elif char == '\t':  # Treating tab as single whitespace for now
    __insert_char(' ')
  elif len(char) == 1 and char.isprintable():  # Single character input.
    __insert_char(char)
  else:  # Unknown key stroke ignore.
    pass

  emit_str(__buffer_string())
