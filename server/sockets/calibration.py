import threading
import time
import json
import numpy as np
from matplotlib.figure import Figure

from . import session
from .common import *


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
      continue
      ## Ignoring lines that are not of standard format
    chipid = str(tokens[1])
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


def StandardCalibration(socketio, msg):
  """
  Running a standard calibration sequence
  """
  print(msg)

  ## Resetting the cache
  status = session.cmd.onecmd(
      'set --boardtype cfg/{type}.json --boardid {id}'.format(
          type=msg['boardtype'], id=msg['boardid']))
  init_cache()

  dofile = 'dofiles/calibrate_{type}.txt'.format(type=msg['boardtype'])
  dofile = open(dofile)
  lines = dofile.read().split('\n')
  dofile.close()

  ReturnTileboardLayout(socketio)

  vis_action = [line for line in lines if line.startswith('visualcenterchip')]
  lumi_action = [
      line for line in lines if not line.startswith('visualcenterchip')
  ]

  WaitUserAction(socketio,
                 ('Starting visual calibration run, please make sure the '
                  'high-power on the SiPM is closed before continuing!'))
  for line in vis_action:
    session.cmd.onecmd(line)
    ReturnTileboardLayout(socketio)
    ## Returning tileboard layout after visual calibration

  WaitUserAction(socketio,
                 ('Starting luminosity scan, please make sure the high-power '
                  'is turned back on before continuing!'))

  ReturnReadoutUpdate(socketio)

  for line in lumi_action:
    ## Strange syntax to avoid string splitting  :/
    cmdthread = threading.Thread(target=session.cmd.onecmd, args=(line, ))
    cmdthread.start()
    while cmdthread.is_alive():
      time.sleep(0.7)  # Update every 0.1 second max
      update_cache()
    update_cache()
    print('Finished: ', line)
    ## Updating again after command has finished to get all the final results


def ReturnReadoutUpdate(socketio):
  if session.state == session.STATE_RUN_PROCESS:
    """
    Only update if the session is currently not idle
    """

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
                    namespace='/monitor')
    except:
      print( session.zscan_updates )
      print( session.lowlight_updates )
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


def StartReadoutMonitor(socketio):
  if session.state == session.STATE_RUN_PROCESS:
    session.zscan_updates.extend(session.zscan_cache.keys())
    session.lowlight_updates.extend(session.lowlight_cache.keys())
