"""
  action.py

  This function defines the functions required to complete user actions.
  Highlevel functions that are called by the parsing function will always start
  with the prefix `run_`. Other helper functions are also defined in this file.

  Notice that this file should not not have to handle the sending the signals to
  signal the completion of various signals. This should be handled in the sync.py
  file.
"""
import threading
import time
import json
import re
import os
import sys
import datetime
import subprocess
import paramiko
import traceback
import numpy as np

## Importing the global objects as well as the various server helper function.
from . import session
from .sync import *
from .report import *
from .format import *

## For redirecting logging output
from ..cmod.logger import *


def run_image_settings(socketio, data):
  """
  Updating the settings for image parsing.
  """
  session.cmd.visual.threshold = float(data['threshold'])
  session.cmd.visual.blur_range = int(data['blur'])
  session.cmd.visual.lumi_cutoff = int(data['lumi'])
  session.cmd.visual.size_cutoff = int(data['size'])
  session.cmd.visual.ratio_cutoff = float(data['ratio'])
  session.cmd.visual.poly_range = float(data['poly'])
  sync_calibration_settings()


def run_zscan_settings(socketio, data):
  """
  Updating the setting related to the zscan commands for calibration processes.
  """
  session.zscan_samples = int(data['samples'])
  session.zscan_power_list = [float(x) for x in data['pwm']]
  session.zscan_zlist_dense = [float(z) for z in data['zlist_dense']]
  session.zscan_zlist_sparse = [float(z) for x in data['zlist_sparse']]
  sync_calibration_settings()


def run_lowlight_settings(socketio, data):
  """
  Updating the settings related to the lowlight calibration process.
  """
  session.lowlight_samples = int(data['samples'])
  session.lowlight_pwm = float(data['pwm'])
  session.lowlight_zval = float(data['zval'])
  sync_calibration_settings()


def run_lumialign_settings(socketio, data):
  """
  Updating the settings related to the luminosity alignment calibration process.
  """
  session.lumialign_samples = int(data['samples'])
  session.lumialign_pwm = float(data['pwm'])
  session.lumialign_zval = float(data['zval'])
  session.lumialign_range = float(data['range'])
  session.lumialign_distance = float(data['distance'])
  sync_calibration_settings()


def run_picoscope_settings(socketio, data):
  """
  Updating the settings related to the picoscope readout settings.
  """
  try:
    session.cmd.pico.setrange(0, int(data['channel-a-range']))
    session.cmd.pico.setrange(1, int(data['channel-b-range']))
    session.cmd.pico.settrigger(int(data['trigger-channel']),
                                int(data['trigger-direction']),
                                float(data['trigger-level']),
                                int(data['trigger-delay']), 0)
    session.cmd.pico.setblocknums(int(data['blocksize']), int(
        data['postsample']), int(data['presample']))
    time.sleep(1)
    # Forcing a sleep to make sure commands have been properly processed.
  except Exception as err:
    pass  ## Since the picoscope might not exists
  sync_calibration_settings()


def run_cmd_input(socketio, msg):
  """
  Running a single command provided by the client input.
  """
  exec_command_with_log(socketio, msg['input'])


def run_standard_calibration(socketio, msg):
  """
  Running a standard calibration sequence on an entire board.

  Notice that this assumes that a reference calibration already exists. For each
  detector on the board the standard calibration sequence is as such:
  1. A visual alignment is performed, the transformation matrix is based on the
     reference calibration session.
  2. The sharpness measure is maximized and the corresponding z is recorded.
  3. A intensity v.s. z is measure
  4. The low light performance at a high z is collected.

  Step 3 and 4 will the automatically alternated to minimize the motion time of
  the overall calibration process.
  """
  ## Syning the session type
  sync_session_type(socketio, session.SESSION_TYPE_STANDARD)
  ## Resetting the cache
  status = prepare_calibration_session(socketio, msg['boardtype'],
                                       msg['boardid'], msg['reference'])
  if status: return  ## Early exit on setup failure.

  ## Defining the expected list of processes.
  prepare_progress_check({
      'visalign': session.cmd.board.dets(),
      'zscan': session.cmd.board.dets(),
      'lowlight': session.cmd.board.dets(),
  })

  wait_user_action(socketio, __std_calibration_lighton_msg)

  # The visual alignment stuff.
  set_light('on')
  for detid in session.order_dets:
    line = make_cmd_visualalign(detid)
    exec_cmd_simple(socketio, line, 'visalign', detid)
    session.visual_cache[detid] = session.cmd.visual.save_image(
        'server/static/temporary/visual_{detid}.jpg'.format(detid=detid))
  set_light('off')

  wait_user_action(socketio, __std_calibration_lightoff_msg)

  ## Running the luminosity part.
  for index, detid in enumerate(reversed(session.order_dets)):
    even_line = bool((index % 2) == 0)
    zscan_line = make_cmd_zscan(detid=detid, dense=False, rev=~even_line)
    lowlight_line = make_cmd_lowlight(detid)
    if even_line:
      exec_cmd_monitor(socketio, zscan_line, 'zscan', detid)
      exec_cmd_monitor(socketio, lowlight_line, 'lowlight', detid)
    else:
      exec_cmd_monitor(socketio, lowlight_line, 'lowlight', detid)
      exec_cmd_monitor(socketio, zscan_line, 'zscan', detid)

  # At the end of the calibration command, send a signal that tells the client to
  # display the sign off window
  # sync_start_signoff(socketio, 'standard')


## Long message strings are disruptive to code reading are placed here.
__std_calibration_lighton_msg = reduce_cmd_whitespace("""
Starting visual calibration sequences, please make sure the <b>HIGH VOLTAGE
POWER</b> on the SiPM is <b>OFF</b> before continuing!
""")

__std_calibration_lightoff_msg = reduce_cmd_whitespace("""
Starting luminosity calibration sequences, please make sure <b>HIGH VOLTAGE
POWER</b> on the SiPM is <b>ON</b> before continuing!
""")


def run_system_calibration(socketio, msg):
  """
  System calibration with a specified calibration board.

  The processes consists of the the following steps:
  1. The visual calibration matrix is constructed on the first detector in the
     session.
  2. The visual calibration is performed on all detectors in the session.
  3. The light are requested to be turned off and the luminosity alignment is
     performed for all detectors in the session.
  4. For each linear detectors, a luminosity vs. z profile of obtained.
  5. For each counting detector, a low light profile is obtained.

  For system calibration where we expect only a small number of detector
  elements, we will not be optimizing the motion path.
  """
  sync_session_type(socketio, session.SESSION_TYPE_SYSTEM)
  status = prepare_calibration_session(socketio, msg['boardtype'])
  if status: return

  ## Defining the expected list of process
  prepare_progress_check({
      'vhscan': [session.order_dets[0]],
      'visalign':
      session.order_dets,
      'lumialign':
      session.order_dets,
      'zscan': [d for d in session.order_dets if (int(d) % 2 == 1)],
      'lowlight': [d for d in session.order_dets if (int(d) % 2 == 0)],
  })

  wait_user_action(socketio, __sys_calibration_lighton_message)

  # Running the visual align stuff.
  set_light('on')
  cmd = make_cmd_visualscan(session.order_dets[0])
  exec_cmd_monitor(socketio, cmd, 'vhscan', session.order_dets[0])
  for detid in session.cmd.board.dets():
    cmd = make_cmd_visualalign(detid)
    exec_cmd_simple(socketio, cmd, 'visalign', detid)
    session.visual_cache[detid] = session.cmd.visual.save_image(
        'server/static/temporary/visual_{detid}.jpg'.format(detid=detid))
  set_light('off')

  wait_user_action(socketio, __sys_calibration_lightoff_message)

  ## Running the luminosity alignment
  for detid in session.order_dets:
    cmd = make_cmd_lumialign(detid=detid)
    exec_cmd_monitor(socketio, cmd, 'lumialign', detid)

  # Generating a luminosity profile from the photo diode on the reference board
  # Otherwise generate a low light profile for a relative efficiency reference.
  for detid in session.order_dets:
    if (int(detid) % 2 == 1):
      cmd = make_cmd_zscan(detid=detid, dense=True, rev=False)
      exec_cmd_monitor(socketio, cmd, 'zscan', detid)
    else:
      cmd = make_cmd_lowlight(detid=detid)
      exec_cmd_monitor(socketio, cmd, 'lowlight', detid)

  # At the end of the calibration command, send a signal that tells the client to
  # display the sign off window
  # sync_start_signoff(socketio, 'system')


## Long message strings are disruptive to code reading are placed here.
__sys_calibration_lighton_message = reduce_cmd_whitespace("""
Starting a system calibration process.<br/> Please make sure the reference board
is placed in the correct position, and that the <b>HIGH VOLTAGE POWER</b> for
photo detectors is <b>OFF</b> before continuing!
""")

__sys_calibration_lightoff_message = reduce_cmd_whitespace("""
Starting luminosity scan part of system calibration process, please make sure the
<b>HIGH VOLTAGE POWER</b> for photo detectors is <b>ON</b> before continuing!
""")


def run_process_extend(socketio, msg):
  """
  Extending or remeasuring a certain calibration process for a single detector.
  This command also trigger the additional routines required for updating the
  cached data and the stored progress if needed.
  """
  action = msg['action']
  detid = msg['detid']
  extend = msg['extend']

  # Making the new command to run
  cmd = make_cmd_lumialign(detid) if action == 'lumialign' else \
        make_cmd_lowlight(detid) if action == 'lowlight' else \
        make_cmd_zscan(detid,dense=True,rev=False) if action =='zscan' else \
        make_cmd_visualalign(detid) if action == 'visalign' else \
        ''
  monitor = False if action == 'visalign' else \
            True
  if cmd == '': return  # Early exit if not correponding command is generated

  cmd = cmd.replace('--wipefile', '') if extend else cmd
  if not extend:  ## Manually wiping the data cache in the session
    if action == 'lumialign':
      session.lumialign_cache[detid] = []
    elif action == 'lowlight':
      session.lowlight_cache[detid] = []
    elif action == 'zscan':
      session.zscan_cache[detid] = []

  ## Updating the process tag initially which allow for trigger more stuff
  if action not in session.progress_check:
    session.progress_check[action] = {str(detid): 1}
  else:
    session.progress_check[action][str(detid)] = 1

  # Running the program. Monitor is requested
  if monitor: exec_cmd_monitor(socketio, cmd, action, detid)
  else: exec_cmd_simple(socketio, cmd, action, detid)

  # Updating the visual cache if the action performed is such
  if action == 'visalign':
    session.visual_cache[detid] = session.cmd.visual.save_image(
        'server/static/temporary/visual_{detid}.jpg'.format(detid=detid))


def run_calibration_signoff(socketio, data, store):
  """
  Running the process to signoff a calibration result to be saved to the central
  processing server. All data files, as well as the calibration summary, the user
  submitted comment will be packed into a single tar ball to be passed over to
  the central processing server.

  For system calibrations, all stored will be passed over to the calib/ directory
  for future reference.

  For standard calibration processes, an extra comment line is also generated to
  store the reference calibration session.
  """
  ## Saving the calibration results and comments
  exec_command_with_log(
      socketio,
      'savecalib -f={filename}'.format(filename=calibration_filename('summary')))

  ## Saving the comment as a json dump.
  comments = {key: data['comments'][key].split('\n') for key in data['comments']}
  if not store: comments['reference'] = session.reference_session
  comment_file = session.cmd.sshfiler.remotefile(calibration_filename('comment'),
                                                 wipefile=True)
  comment_file.write(json.dumps(comments))

  ## Generating tarball for file transmission
  tar_file = calibration_directory() + '.tar.gz'
  directory = calibration_directory()

  # Making a local copy for future reference
  if store and not os.path.isdir('calib/' + directory):
    subprocess.run(['cp', '-r', directory, 'calib/'])

  # Copying the calibration session over to the data display server over ssh
  subprocess.run(
      ['tar', 'zcvf',
       os.path.basename(tar_file),
       os.path.basename(directory)],
      cwd='results/')
  subprocess.run(['mv', tar_file, os.path.basename(tar_file)])
  tar_file = os.path.basename(tar_file)

  # Copying the data over scp using user login data using paramiko
  counter = 0
  while counter < 5:
    try:
      ssh = paramiko.SSHClient()
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      ssh.connect('hepcms-in2.umd.edu',
                  username=data['user'],
                  password=data['pwd'])
      sftp = ssh.open_sftp()
      sftp.banner_timeout = 200000
      sftp.chdir('/data/users/yichen/SiPMCalib/tar')
      print(tar_file, os.path.exists(tar_file))
      sftp.put(tar_file, tar_file)
      sftp.close()
      ssh.close()
      break
    except Exception as e:
      traceback.print_stack()
      send_display_message(socketio, 'Error in ssh connection, trying again...')
      send_display_message(socketio, str(e))
      counter = counter + 1
      time.sleep(2)

  if counter >= 5:
    send_display_message(
        socketio,
        'Failed to transmit file, calibration session is still stored locally')
    return

  ## Cleaning the file in the results directory
  subprocess.run(['rm', '-rf', tar_file])
  subprocess.run(['rm', '-rf', directory])

  clear_cache()
  sync_session_type(socketio, session.SESSION_TYPE_NONE)


def prepare_calibration_session(socketio,
                                boardtype,
                                boardid=None,
                                reference=None):
  """
  Preparing the data members of the global session object for a calibration
  session. This includes:

  1. Loading the boardtype and reference board.
  2. The construction of the data cache map.
  3. Construction of the "ordered list of detectors", this is a very naive
     algorithm aimed to reduce the horizontal motion path required to visit all
     detector. Starting from the 0th detector listed on the board, kee finding
     the closest unvisited neighbor all detectors have been visited.

  If any of the steps fail, the function will return false.
  """
  # Setting up the board
  cmd = 'set --boardtype cfg/{dir}/{type}.json'.format(
      dir='standard' if boardid else 'system', type=boardtype)
  cmd += '  --boardid {id}'.format(id=boardid) if boardid else ''
  status = exec_command_with_log(socketio, cmd)
  if (status != 0): return status

  # Initializing the data cache.
  session.zscan_cache = {detid: [] for detid in session.cmd.board.dets()}
  session.lumialign_cache = {detid: [] for detid in session.cmd.board.dets()}
  session.lowlight_cache = {detid: [] for detid in session.cmd.board.dets()}
  session.visual_cache = {detid: False for detid in session.cmd.board.dets()}
  session.calib_session_time = datetime.datetime.now()

  # Construction of the ordered list.
  session.order_dets = [list(session.cmd.board.dets())[0]]

  while len(session.order_dets) < len(session.cmd.board.dets()):
    x0, y0 = session.cmd.board.get_det(session.order_dets[-1]).orig_coord
    distance = [{
        'id':
        detid,
        'dist': [
            abs(session.cmd.board.get_det(detid).orig_coord[0] - x0),
            abs(session.cmd.board.get_det(detid).orig_coord[1] - y0)
        ]
    } for detid in session.cmd.board.dets() if detid not in session.order_dets]

    def compare(a):
      return ((a['dist'][0]**2 + a['dist'][1]**2) * 1000 * 1000 +
              a['dist'][0] * 1000 + a['dist'][1])

    next_det = min(distance, key=compare)
    session.order_dets.append(next_det['id'])

  # Since the reference board will contain detectors that doesn't actually exist
  # on the running board, we will run the load calib command last to make sure
  # the board settings doesn't bleed into the file generation.
  if reference:
    session.reference_session = reference
    cmd = 'loadcalib -f calib/{reference}/summary.json'.format(
        reference=reference)
    exec_command_with_log(socketio, cmd)
  else:
    session.reference_session = ''

  return 0


def prepare_progress_check(progress_detid):
  """
  Making the progress check map. The input format should be a dictionary in the
  format of:
    { process_tag: detid_list }
  This aims to reduce the verbosity of construction
  """
  session.progress_check = {}
  for tag, id_list in progress_detid.items():
    session.progress_check[tag] = {
        detid: session.CMD_PENDING
        for detid in id_list
    }


def exec_cmd_monitor(socketio, line, process_tag, detid):
  """
  Running a calibration command in a separate thread to allow for parallel
  monitoring. While the command is running the rough percentage of the
  calibration command is monitored by piping the cmd output to the temporary
  file, the overall session progress is also automatically update.
  """
  # static variable to check if command finished.
  exec_cmd_monitor.is_running = False

  def run_with_save(line):
    "A tine wrapper function for creating a thread."
    session.run_results = exec_command_with_log(socketio, line)

  def update_loop(process_tag):
    while exec_cmd_monitor.is_running:
      time.sleep(0.1)
      update_data_cache(process_tag)
      update_current_progress()

  if process_tag not in session.progress_check:
    session.progress_check[process_tag] = {str(detid): 1}

  with open('/tmp/logging_temp', 'w') as logfile:
    set_logging_descriptor(logfile.fileno())
    session.progress_check[process_tag][detid] = 2

    ## Strange syntax to avoid string splitting  :/
    cmd_thread = threading.Thread(target=run_with_save, args=(line, ))
    cmd_thread.start()
    exec_cmd_monitor.is_running = True

    update_thread = threading.Thread(target=update_loop, args=(process_tag, ))
    update_thread.start()

    ## Having the process finish
    cmd_thread.join()
    exec_cmd_monitor.is_running = False
    session.progress_check[process_tag][detid] = session.run_results
    update_thread.join()

  ## One last update to ensure that things have finished.
  set_logging_descriptor(1)  ## Setting back to STDOUT
  update_data_cache(process_tag)
  update_current_progress()


def exec_cmd_simple(socketio, cmd, process_tag, detid):
  """
  Running single command without thread. Meant for fast commands such as visual
  calibration. Here the data will not be included.
  """
  session.progress_check[process_tag][detid] = 2
  with open('/tmp/logging_temp', 'w') as logfile:
    set_logging_descriptor(logfile.fileno())
    session.progress_check[process_tag][detid] = exec_command_with_log(
        socketio, cmd)
    update_current_progress()
  set_logging_descriptor(1)  # MOVING BACK TO STDOUT
  update_current_progress()
  # print('Finished: ', cmd)


def exec_command_with_log(socketio, cmd):
  """
  Running a single command, returning the results of the command execution
  status, as well as the calling the send message function so that the commands
  executed can be logged client side.
  """
  send_command_message(socketio, cmd)
  return session.cmd.onecmd(cmd)


def clear_cache():
  session.zscan_cache = {}
  session.lumialign_cache = {}
  session.lowlight_cache = {}
  session.visual_cache = {}
  session.progress_check = {}
  session.calib_session_time = None
  session.cmd.board.clear()


def update_data_cache(process_tag):
  """
  Updating a cached version of the data if by reading from the file that is
  currently being written to by the underlying cmd instance. This function
  assumes the standard data format of:
  ```
  timestamp detID x y z led_bias led_temp sipm_temp readout1 readout2...
  ```
  How the data should be interpreted (a.k.a. which cache the data should be
  passed to), will be determined by the input parameter. Notice that the cached
  data of the calibration monitor will not attempt to perform any corrections.
  That will only be processes by the server side with the full fits.
  """

  # Early exit if file is not yet open
  if not session.cmd.sshfiler.readfile: return

  def update_zscan(detid, tokens):
    z = float(tokens[4])
    bias = float(tokens[5])
    lumi = [float(token) for token in tokens[8:]]
    if len(lumi) == 2:  # Must satisfy standard format
      session.zscan_cache[detid].append([z, lumi[0], bias])

  def update_lowlight(detid, tokens):
    lumi = [float(token) for token in tokens[8:]]
    if len(lumi) <= 10: return  # realy exist for all form
    if len(session.lowlight_cache[detid]) == 0:
      content, bins = np.histogram(lumi, 40)
      session.lowlight_cache[detid] = [content, bins]
    else:  ## Appending a histogram!
      session.lowlight_cache[detid][0] += np.histogram(
          lumi, bins=session.lowlight_cache[detid][1])[0]

  def update_lumiscan(detid, tokens):
    x = float(tokens[2])
    y = float(tokens[3])
    lumi = [float(token) for token in tokens[8:]]
    if len(lumi) == 2:
      session.lumialign_cache[detid].append([x, y, lumi[0]])

  try:
    lines = session.cmd.sshfiler.readfile.read().split('\n')
    for line in lines:
      tokens = line.split()
      if len(tokens) < 9: continue  # skipping malformed lines
      detid = str(tokens[1])
      if not detid in session.cmd.board.dets(): continue  # ignore missing detid
      # Running the main update
      if process_tag == 'zscan':
        update_zscan(detid, tokens)
      elif process_tag == 'lowlight':
        update_lowlight(detid, tokens)
      elif process_tag == 'lumialign':
        update_lumiscan(detid, tokens)
  except:  ## In the unlikely case that the file is not open. Skip everything
    pass


def update_current_progress():
  """
  Updating the progress of the calibration process that is currently running.
  This function works by monitoring the cmd logging output (which has been piped
  to '/tmp/logging_temp', And reading the last two numbers, which usually
  indicates the steps performed and the expected total steps.)
  """
  read_log = open('/tmp/logging_temp', 'r')
  lines = re.split('[\\r\\n]', read_log.read())
  last_line = next((x for x in reversed(lines) if 'Progress' in x), '')
  read_log.close()

  if not 'Progress' in last_line:
    session.progress_check['current'] = [0, 1]
    ## Initializating as a zero two point function
  else:
    pattern = re.compile(r'.*Progress\s*\[\s*(\d+)\/\s*(\d+)\].*')
    match = pattern.match(last_line)
    if match and len(match.groups()) == 2:
      session.progress_check['current'] = [int(match[1]), int(match[2])]
    else:
      pass  ## Don't try to wipe or update
  ## Forcing 100% Completion on command exit
  if 'current' in session.progress_check and session.state == session.STATE_IDLE:
    session.progress_check['current'][0] = session.progress_check['current'][1]


def set_light(state):
  """
  Thin wrapper around the gpio lights on/off method. This is for local testing on
  a machine that doesn't have real gpio control.
  """
  try:
    if state == 'on':
      session.cmd.gpio.light_on()
    else:
      session.cmd.gpio.light_off()
  except:
    pass
