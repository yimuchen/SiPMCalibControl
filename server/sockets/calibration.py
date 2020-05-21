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

from . import session
from .singleaction import *
from .report import *
from .format import *

## For redirecting logging output
from ..cmod.logger import *


def clear_cache():
  session.zscan_cache = {}
  session.lumialign_cache = {}
  session.lowlight_cache = {}
  session.zscan_updates = []
  session.lowlight_updates = []
  session.lumialign_updates = []
  session.progress_check = {}
  session.calib_session_time = None
  session.cmd.board.clear()


def init_cache():
  """
  Initializing data cache to store calibration results
  """
  session.zscan_cache = {detid: [] for detid in session.cmd.board.dets()}
  session.lumialign_cache = {detid: [] for detid in session.cmd.board.dets()}
  session.lowlight_cache = {detid: [] for detid in session.cmd.board.dets()}
  session.zscan_updates = []
  session.lowlight_updates = []
  session.lumialign_updates = []
  session.calib_session_time = datetime.datetime.now()


def init_calib_progress_check():
  session.progress_check = {
      'visalign': {detid: 1
                   for detid in session.cmd.board.dets()},
      'zscan': {detid: 1
                for detid in session.cmd.board.dets()},
      'lowlight': {detid: 1
                   for detid in session.cmd.board.dets()}
  }


def update_cache(progress_tag):
  """
  Updating the files from the readfile results
  """

  if not session.cmd.sshfiler.readfile:
    """
    Early exit on file not being open yet.
    """
    return

  def update_zscan(detid, tokens):
    z = float(tokens[4])
    bias = float(tokens[5])
    lumi = [float(token) for token in tokens[8:]]
    if len(lumi) == 2:  # Must satisfy standard format
      session.zscan_updates.append(detid)
      session.zscan_cache[detid].append([z, lumi[0], bias])

  def update_lowlight(detid, tokens):
    lumi = [float(token) for token in tokens[8:]]
    if len(lumi) > 10:
      session.lowlight_updates.append(detid)
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
      session.lumialign_updates.append(detid)
      session.lumialign_cache[detid].append([x, y, lumi[0]])

  lines = session.cmd.sshfiler.readfile.read().split('\n')
  for line in lines:
    tokens = line.split()
    if len(tokens) < 9:
      ## Ignoring lines that are not of standard format
      continue
    detid = str(tokens[1])
    if not detid in session.cmd.board.orig_coord:
      # Ignoring lines where the data is wrongly parsed
      # And the result det id turn out to be garbage.
      continue

    if progress_tag == 'zscan':
      update_zscan(detid, tokens)
    elif progress_tag == 'lowlight':
      update_lowlight(detid, tokens)
    elif progress_tag == 'lumialign':
      update_lumiscan(detid, tokens)

  ## Sorting to unique.
  session.zscan_updates = sorted(set(session.zscan_updates))
  session.lowlight_updates = sorted(set(session.lowlight_updates))
  session.lumialign_updates = sorted(set(session.lumialign_updates))


def update_progress():
  """
  Updating the current progress of the calibration process
  """
  read_log = open('/tmp/logging_temp', 'r')
  lines = re.split('[\\r\\n]', read_log.read())
  last_line = next((x for x in reversed(lines) if 'Progress' in x), '')
  read_log.close()

  if not 'Progress' in last_line:
    session.progress_check['current'] = []
  else:
    pattern = re.compile(r'.*Progress\s*\[\s*(\d+)\/\s*(\d+)\].*')
    match = pattern.match(last_line)
    if match and len(match.groups()) == 2:
      session.progress_check['current'] = [int(match[1]), int(match[2])]
    else:
      pass  ## Don't try to wipe or update


def set_light(state):
  try:
    if state == 'on':
      session.cmd.gpio.light_on()
    else:
      session.cmd.gpio.light_off()
  except:
    pass


def GetSortedDets():
  """
  Very Naive algorithm for finding the shortest path within the list of dets.
  Starting from the 0th det, keep finding the closest unvisited neighbor until
  the list is exhausted.
  """
  det_sort_list = []

  det_sort_list.append(list(session.cmd.board.dets())[0])

  while len(det_sort_list) < len(session.cmd.board.dets()):
    x0, y0 = session.cmd.board.orig_coord[det_sort_list[-1]]

    distance = [{
        'id': detid,
        'dist': [abs(c[0] - x0), abs(c[1] - y0)]
    }
                for detid, c in session.cmd.board.orig_coord.items()
                if detid not in det_sort_list]

    def compare(a):
      return ((a['dist'][0]**2 + a['dist'][1]**2) * 1000 * 1000 +
              a['dist'][0] * 1000 + a['dist'][1])

    next_det = min(distance, key=compare)
    det_sort_list.append(next_det['id'])

  return det_sort_list


def RunLineInThread(line, progress_tag, detid):
  """
  Running a single line in a separate thread to allow for parallel monitoring
  """
  def run_with_save(line):
    session.run_results = session.cmd.onecmd(line)

  if progress_tag not in session.progress_check:
    session.progress_check[progress_tag] = {str(detid): 1}

  with open('/tmp/logging_temp', 'w') as logfile:
    set_logging_descriptor(logfile.fileno())
    session.progress_check[progress_tag][detid] = 2

    ## Strange syntax to avoid string splitting  :/
    cmdthread = threading.Thread(target=run_with_save, args=(line, ))
    cmdthread.start()

    ## Waiting for command to update
    while cmdthread.is_alive():
      time.sleep(0.1)  # Update every 0.1 second max
      update_cache(progress_tag)
      session.progress_check[progress_tag][detid] = 2
      update_progress()

  set_logging_descriptor(1)  ## Setting back to STDOUT
  session.progress_check[progress_tag][detid] = session.run_results
  update_cache(progress_tag)
  update_progress()

  ## Forcing 100% Completion on command exit
  if 'current' in session.progress_check:
    session.progress_check['current'][0] = session.progress_check['current'][1]
  print('Finished: ', line)


def RunLineNoMonitor(line, progress_tag, detid):
  """
  Running single command without thread. Meant for fast commands such as visual
  calibration.
  """
  with open('/tmp/logging_temp', 'w') as logfile:
    set_logging_descriptor(logfile.fileno())
    session.progress_check[progress_tag][detid] = session.cmd.onecmd(line)
    update_progress()
  set_logging_descriptor(1)  # MOVING BACK TO STDOUT
  print('Finished: ', line)


def StandardCalibration(socketio, msg):
  """
  Running a standard calibration sequence
  """
  clear_cache()

  ## Resetting the cache
  status = session.cmd.onecmd(
      'set --boardtype cfg/{type}.json --boardid {id}'.format(
          type=msg['boardtype'], id=msg['boardid']))
  if status != 0:
    """
    Early exit on not being able to load file status
    """

    return

  init_cache()
  init_calib_progress_check()
  ReturnClearExisting(socketio)

  ## Updating list of expected actions before giving a list of dets
  ReportProgress(socketio)
  ReportTileboardLayout(socketio)
  det_list = GetSortedDets()

  WaitUserAction(socketio,
                 ('Starting visual calibration sequences, please make sure the '
                  '<b>HIGH VOLTAGE POWER</b> on the SiPM is <b>OFF</b> before '
                  'continuing!'))

  ## Turn lights on
  set_light('on')

  for detid in det_list:
    line = ('visualcenterdet --detid {detid}'
            '                -z 10 '
            '                --overwrite').format(detid=detid)
    RunLineNoMonitor(line, 'visalign', detid)
    ReportTileboardLayout(socketio)
    ## Returning tileboard layout after visual calibration

  set_light('off')

  WaitUserAction(socketio,
                 ('Starting luminosity calibration sequences, please make sure '
                  '<b>HIGH VOLTAGE POWER</b> on the SiPM is <b>ON</b> before '
                  'continuing!'))

  ReportReadout(socketio)

  for index, detid in enumerate(reversed(det_list)):
    even_line = bool((index % 2) == 0)
    zscan_line = CmdZScan(detid=detid,
                          dense=False,
                          rev=False if even_line else True)
    lowlight_line = CmdLowLightCollect(detid)
    if even_line:
      RunLineInThread(zscan_line, 'zscan', detid)
      RunLineInThread(lowlight_line, 'lowlight', detid)
    else:
      RunLineInThread(lowlight_line, 'lowlight', detid)
      RunLineInThread(zscan_line, 'zscan', detid)
    ## Updating again after command has finished to get all the final results


def init_sys_progress_check():
  session.progress_check = {
      'vhscan': {
          list(session.cmd.board.dets())[0]: 1
      },
      'visalign': {detid: 1
                   for detid in session.cmd.board.dets()},
      'lumialign': {detid: 1
                    for detid in session.cmd.board.dets()},
      'zscan':
      {detid: 1
       for detid in session.cmd.board.dets()
       if int(detid) % 2 == 1},
      'lowlight':
      {detid: 1
       for detid in session.cmd.board.dets()
       if int(detid) % 2 == 0}
  }


def SystemCalibration(socketio, msg):
  """
  System calibration with a specified calibration board.
  """
  clear_cache()
  ## Resetting the cache
  status = session.cmd.onecmd(
      'set --boardtype cfg/{type}.json'.format(type=msg['boardtype']))

  if status != 0:
    """
    Early exit on not being able to setup board status
    """
    DisplayMessage(
        socketio,
        ('Unable to setup boardtype [{0}]. Contact the system administrator to '
         'make sure the correct calbration files are included.').format(
             msg['boardtype']))
    return

  init_cache()
  init_sys_progress_check()
  ReturnClearExisting(socketio)
  ## Triggering the first layout update
  ReportProgress(socketio)
  ReportTileboardLayout(socketio)

  WaitUserAction(
      socketio,
      ('Starting a system calibration process.<br/>'
       'Please make sure the reference '
       'board is placed in the correct position, and that the <b>HIGH VOLTAGE '
       'POWER</b> for photo detectors is <b>OFF</b> before continuing!'))

  # Use the first det in the list to perform the transformation matrix
  # generation
  set_light('on')

  first_det = list(session.cmd.board.dets())[0]

  vishscan_line = ('visualhscan --detid={detid} '
                   '            -z 10           '
                   '            --overwrite -f=/dev/null').format(
                       detid=first_det)
  RunLineNoMonitor(vishscan_line, 'vhscan', first_det)
  for detid in session.cmd.board.dets():
    line = 'visualcenterdet --detid={detid} -z 10 --overwrite '.format(
        detid=detid)
    RunLineNoMonitor(line, 'visalign', detid)
    ReportTileboardLayout(socketio)

  set_light('off')
  ReportReadout(socketio)

  ## Running the luminosity scan calibrations
  WaitUserAction(socketio, (
      'Starting luminosity scan part of system calibration process, please make '
      'sure the <b>HIGH VOLTAGE POWER</b> for photo detectors is <b>ON</b> '
      'before continuing!'))

  for detid in session.cmd.board.dets():
    line = CmdLumiAlign(detid=detid)
    RunLineInThread(line, 'lumialign', detid)
    ReportTileboardLayout(socketio)

  # Generating a luminosity profile from the photo diode on the reference board
  # Otherwise generate a low light profile for a relative efficiency reference.
  for detid in session.cmd.board.dets():
    if (int(detid) % 2 == 1):
      line = CmdZScan(detid=detid, dense=True, rev=False)
      RunLineInThread(line, 'zscan', detid)
    else:
      line = CmdLowLightCollect(detid=detid)
      RunLineInThread(line, 'lowlight', detid)


def RerunCalibration(socketio, msg):
  action = msg['action']
  detid = msg['detid']
  extend = msg['extend']

  line = ''
  update_progress = False
  if action == 'lumialign':
    line = CmdLumiAlign(detid)
    update_progress = True
  elif action == 'lowlight':
    line = CmdLowLightCollect(detid)
    update_progress = True
  elif action == 'zscan':
    line = CmdZScan(detid, dense=True if int(detid) < 0 else False, rev=False)
    update_progress = True

  ## Manually removing the `wipefile` options if the extend flag is available
  if extend:
    line = line.replace('--wipefile', '')
  else:
    ## Manually wiping the data cache in the session
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

  ## Running the progress
  if line != '':
    if update_progress == True:
      ## Rerunning the report stack
      ReportProgress(socketio)
      ReportTileboardLayout(socketio)
      ReportReadout(socketio)
      RunLineInThread(line, action, detid)
      ReportTileboardLayout(socketio)
    else:
      ReportProgress(socketio)
      RunLineNoMonitor(line, action, detid)
      ReportTileboardLayout(socketio)


def CalibrationSignoff(socketio, data, store):
  ## Saving the calibration results and comments
  session.cmd.onecmd(
      'savecalib -f={filename}'.format(filename=CalibFilename('summary')))

  comment_file = session.cmd.sshfiler.remotefile(CalibFilename('comment'),
                                                 wipefile=True)

  comments = {key: data['comments'][key].split('\n') for key in data['comments']}
  comment_file.write(json.dumps(comments))

  ## Generating tarball for file transmission
  tar_file = CalibDirectory() + '.tar.gz'
  directory = CalibDirectory()

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
      print( tar_file , os.path.exists(tar_file) )
      sftp.put(tar_file, tar_file)
      sftp.close()
      ssh.close()
      break
    except Exception as e:
      traceback.print_stack()
      DisplayMessage(socketio, str(e))
      counter = counter + 1
      time.sleep(2)

  if counter >= 5:
    DisplayMessage(socketio, "Failed to transfer file")
    return

  ## Cleaning the file in the results directory
  subprocess.run(['rm', '-rf', tar_file])
  subprocess.run(['rm', '-rf', directory])

  update_reference_list()
  clear_cache()
  SignoffComplete(socketio)


def update_reference_list():
  calib_fmt = re.compile(r'[a-zA-Z\_]+_\d{8}-\d{4}$')
  filelist = [f for f in os.listdir('calib') if calib_fmt.match(f)]

  time_now = datetime.datetime.now()

  def time_of_file(f):
    return datetime.datetime.strptime(f[-13:], '%Y%m%d-%H%M')

  for f in filelist:
    time_then = time_of_file(f)
    if (time_now - time_then).days < 1:  ## Calibrations are valid for a day
      session.valid_reference_list.append(f)

  ## Getting unique and sort according to date
  session.valid_reference_list = sorted(set(session.valid_reference_list),
                                        key=time_of_file)
  session.valid_reference_list.reverse()  ## Making newest file appear first
