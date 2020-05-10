import threading
import time
import json
import re
import numpy as np
from io import StringIO
from contextlib import redirect_stdout

from . import session
from .common import *
from ..cmod.logger import *


def init_cache():
  """
  Initializing data cache to store calibration results
  """
  session.zscan_cache = {chipid: [] for chipid in session.cmd.board.chips()}
  session.lowlight_cache = {chipid: [] for chipid in session.cmd.board.chips()}
  session.zscan_updates = []
  session.lowlight_updates = []
  """
  Creating the empty figures if it doesn't already exits
  """


def init_calib_progress_check():
  session.progress_check = {
      'vis_align': {chipid: 1
                    for chipid in session.cmd.board.chips()},
      'zscan': {chipid: 1
                for chipid in session.cmd.board.chips()},
      'lowlight': {chipid: 1
                   for chipid in session.cmd.board.chips()}
  }


def update_cache():
  """
  Updating the files from the readfile results
  """

  if not session.cmd.sshfiler.readfile:
    """
    Early exit on file not being open yet.
    """
    return

  lines = session.cmd.sshfiler.readfile.read().split('\n')
  for line in lines:
    tokens = line.split()
    if len(tokens) < 9:
      ## Ignoring lines that are not of standard format
      continue
    chipid = str(tokens[1])
    if not chipid in session.cmd.board.orig_coord:
      # Ignoring lines where the data is wrongly parsed
      # And the result chip id turn out to be garbage.
      continue

    z = float(tokens[4])
    bias = float(tokens[5])
    lumi_data = [float(token) for token in tokens[8:]]

    if len(lumi_data) == 2:
      ## Scan type data
      session.zscan_updates.append(chipid)
      session.zscan_cache[chipid].append((z, lumi_data[0]))
    elif len(lumi_data) > 2:
      ## Scan type data
      session.lowlight_updates.append(chipid)
      try:  ## Occassionally crashes here.
        if len(session.lowlight_cache[chipid]) == 0:
          session.lowlight_cache[chipid] = np.histogram(lumi_data, 40)
        else:
          ## Appending a histogram!
          session.lowlight_cache[chipid][0] += np.histogram(
              lumi_data, bins=session.lowlight_cache[chipid][1])[0]
      except:
        pass

  ## Sorting to unique.
  session.zscan_updates = sorted(set(session.zscan_updates))
  session.lowlight_updates = sorted(set(session.lowlight_updates))


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


def GetSortedChips():
  """
  Very Naive algorithm for finding the shortest path within the list of chips.
  Starting from the 0th chip, keep finding the closest unvisited neighbor until
  the list is exhausted.
  """
  chip_sort_list = []

  chip_sort_list.append(list(session.cmd.board.chips())[0])

  while len(chip_sort_list) < len(session.cmd.board.chips()):
    x0, y0 = session.cmd.board.orig_coord[chip_sort_list[-1]]

    distance = [{
        'id': chipid,
        'dist': [abs(c[0] - x0), abs(c[1] - y0)]
    }
                for chipid, c in session.cmd.board.orig_coord.items()
                if chipid not in chip_sort_list]

    def compare(a):
      return ((a['dist'][0]**2 + a['dist'][1]**2) * 1000 * 1000 +
              a['dist'][0] * 1000 + a['dist'][1])

    next_chip = min(distance, key=compare)
    chip_sort_list.append(next_chip['id'])

  return chip_sort_list


def RunLineInThread(line, progress_tag, chipid):
  """
  Running a single line in a separate thread to allow for parallel monitoring
  """
  def run_with_save(line):
    session.run_results = session.cmd.onecmd(line)

  with open('/tmp/logging_temp', 'w') as logfile:
    set_logging_descriptor(logfile.fileno())
    session.progress_check[progress_tag][chipid] = 2

    ## Strange syntax to avoid string splitting  :/
    cmdthread = threading.Thread(target=run_with_save, args=(line, ))
    cmdthread.start()

    ## Waiting for command to update
    while cmdthread.is_alive():
      time.sleep(0.1)  # Update every 0.1 second max
      update_cache()
      session.progress_check[progress_tag][chipid] = 2
      update_progress()

  set_logging_descriptor(1)  ## Setting back to STDOUT
  session.progress_check[progress_tag][chipid] = session.run_results
  update_cache()
  update_progress()
  print('Finished: ', line)


def RunLineNoMonitor(line, progress_tag, chipid):
  """
  Running single command without thread. Meant for fast commands such as visual
  calibration.
  """
  with open('/tmp/logging_temp', 'w') as logfile:
    set_logging_descriptor(logfile.fileno())
    session.progress_check[progress_tag][chipid] = session.cmd.onecmd(line)
    update_progress()
  set_logging_descriptor(1)  # MOVING BACK TO STDOUT
  print('Finished: ', line)


def StandardCalibration(socketio, msg):
  """
  Running a standard calibration sequence
  """
  print(msg)

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

  ReturnProgress(socketio)
  ## Updating list of expected actions before giving a list of chips
  ReturnTileboardLayout(socketio)
  chip_list = GetSortedChips()

  WaitUserAction(socketio,
                 ('Starting visual calibration sequences, please make sure the '
                  '<b>HIGH VOLTAGE POWER</b> on the SiPM is <b>OFF</b> before '
                  'continuing!'))

  ## Turn lights on
  set_light('on')

  for chipid in chip_list:
    line = 'visualcenterchip --chipid {chipid} -z 10 --overwrite'.format(
        chipid=chipid)
    RunLineNoMonitor(line, 'vis_align', chipid)
    ReturnTileboardLayout(socketio)
    ## Returning tileboard layout after visual calibration

  set_light('off')

  WaitUserAction(socketio,
                 ('Starting luminosity calibration sequences, please make sure '
                  '<b>HIGH VOLTAGE POWER</b> on the SiPM is <b>ON</b> before '
                  'continuing!'))

  ReturnReadoutUpdate(socketio)

  std_zlist = [
      10, 12, 14, 16, 18, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, 250, 300
  ]
  std_zlist_str = [str(z) for z in std_zlist]

  for index, chipid in enumerate(reversed(chip_list)):

    even_line = bool((index % 2) == 0)

    zscan_line = (
        'zscan --chipid {chipid} '
        '      --zlist {zlist} '
        '      --sample 100 '
        '      --wipefile'
    ).format(
        chipid=chipid,
        zlist=' '.join(std_zlist_str if even_line else reversed(std_zlist_str)))
    lowlight_line = ('lowlightcollect --chipid {chipid} '
                     '                --sample 100000 '
                     '                -z {zmax} '
                     '                --wipefile').format(chipid=chipid,
                                                          zmax=max(std_zlist))
    if even_line:
      RunLineInThread(zscan_line, 'zscan', chipid)
      RunLineInThread(lowlight_line, 'lowlight', chipid)
    else:
      RunLineInThread(lowlight_line, 'lowlight', chipid)
      RunLineInThread(zscan_line, 'zscan', chipid)

    ## Updating again after command has finished to get all the final results


def SystemCalibration(socketio, msg):
  """
  System calibration with a specified calibration board.
  """
  ## Resetting the cache
  status = session.cmd.onecmd(
      'set --boardtype cfg/{type}.json'.format(type=msg['boardtype']))

  for i in range(10):
    print(status)
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

  WaitUserAction(
      socketio,
      ('Starting a system calibration process.<br/>'
       'Please make sure the reference '
       'board is placed in the correct position, and that the <b>HIGH VOLTAGE '
       'POWER</b> for photo detectors is <b>OFF</b> before continuing!'))

  # Use the first chip in the list to perform the list
  ReturnTileboardLayout(socketio)

  set_light('on')
  session.cmd.onecmd(
      'visualhscan --chipid={chipid} -z 10 --overwrite -f=/dev/null'.format(
          chipid=list(session.cmd.board.chips())[0]))
  for chipid in session.cmd.board.chips():
    session.cmd.onecmd(
        'visualcenterchip --chipid={chipid} -z 10 --overwrite '.format(
            chipid=chipid))
    ReturnTileboardLayout(socketio)

  set_light('off')

  ## Running the luminosity scan calibrations
  WaitUserAction(socketio, (
      'Starting luminosity scan part of system calibration process, please make '
      'sure the <b>HIGH VOLTAGE POWER</b> for photo detectors is <b>ON</b> '
      'before continuing!'))

  for chipid in session.cmd.board.chips():
    session.cmd.onecmd(
        ('halign --chipid={chipid} --channel={chipid} '
         '       --sample=100 -z 10  --overwrite '
         '       --range=10 --distance=2'
         '       -f=calib/halign_<BOARDTYPE>_<CHIPID>_<TIMESTAMP>.txt').format(
             chipid=chipid))
    ReturnTileboardLayout(socketio)

  # Generating a luminosity profile from the photo diode on the reference board
  for chipid in session.cmd.board.chips():
    if (int(chipid) % 2 == 1):
      session.cmd.onecmd(
          ('zscan --chipid={chipid} --channel={chipid}'
           '      --sample=100 --wipefile '
           '      -f=calib/zprofile_<BOARDTYPE>_<CHIPID>_<TIMESTAMP>.txt'
           '      -z 10 12 14 16 18 20 30 40 50 60 70 80 90 100 150 200 250 300'
           ).format(chipid=chipid))

  session.cmd.onecmd('savecalib -f=calib/calib_<BOARDTYPE>_<TIMESTAMP>.json')

  ## Saving the calibration results.
  pass


def ReturnReadoutUpdate(socketio):
  if session.state != session.STATE_RUN_PROCESS:
    """
    Only update if the session is currently not idle
    """
    return

  try:
    socketio.emit('update-readout-results', {
        'zscan': {
            chipid: session.zscan_cache[chipid]
            for chipid in session.zscan_updates
            if len(session.zscan_cache[chipid]) > 0
        },
        'lowlight': {
            chipid: [
                session.lowlight_cache[chipid][0].tolist(),
                session.lowlight_cache[chipid][1].tolist()
            ]
            for chipid in session.lowlight_updates
            if len(session.lowlight_cache[chipid]) > 0
        }
    },
                  broadcast=True,
                  namespace='/sessionsocket')
  except:
    print(session.zscan_updates)
    print(session.lowlight_updates)
    print({
        'zscan': {
            chipid: session.zscan_cache[chipid]
            for chipid in session.zscan_updates
            if len(session.zscan_cache[chipid]) > 0
        },
        'lowlight': {
            chipid: [
                session.lowlight_cache[chipid][0].tolist(),
                session.lowlight_cache[chipid][1].tolist()
            ]
            for chipid in session.lowlight_updates
            if len(session.lowlight_cache[chipid]) > 0
        }
    })

  ## Wiping the list after the update has been performed
  session.zscan_updates = []
  session.lowlight_updates = []


def ReturnProgress(socketio):
  socketio.emit('progress-update',
                session.progress_check,
                broadcast=True,
                namespace='/sessionsocket')


def StartReadoutMonitor(socketio):
  if session.state == session.STATE_RUN_PROCESS:
    session.zscan_updates.extend(session.zscan_cache.keys())
    session.lowlight_updates.extend(session.lowlight_cache.keys())
