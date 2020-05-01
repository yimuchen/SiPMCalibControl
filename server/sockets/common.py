## Commonly used functions

from . import session

from time import sleep
import random
import numpy as np

def MessageUserAction(socketio,msg):
  socketio.emit('useraction', msg, namespace='/action', broadcast=True)


def WaitUserAction(socketio, msg):
  print('Sending user action stuff',msg)
  MessageUserAction(socketio,msg)
  session.state = session.STATE_WAIT_USER
  session.waiting_msg = msg
  while (session.state == session.STATE_WAIT_USER):
      sleep(0.1) ## Updating every 0.1 seconds

def CompleteUserAction(socketio):
  print('User action completed')
  session.state = session.STATE_RUN_PROCESS
  session.waiting_msg = ""

def gen_cmdline_options(data, options_list):
  cmdline = [
      '--{0} {1}'.format(opt, data[opt]) for opt in options_list if opt in data
  ]
  cmdline = ' '.join(cmdline)
  return cmdline

def ReturnTileboardLayout(socketio):
  ans = {
      'orig_x': {a: b[0]
                 for a, b in session.cmd.board.orig_coord.items()},
      'orig_y': {a: b[1]
                 for a, b in session.cmd.board.orig_coord.items()},
      'lumi_x': {a: b[0]
                 for a, b in session.cmd.board.orig_coord.items()},
      'lumi_y': {a: b[1]
                 for a, b in session.cmd.board.orig_coord.items()},
      'vis_x': {a: b[0]
                for a, b in session.cmd.board.orig_coord.items()},
      'vis_y': {a: b[1]
                for a, b in session.cmd.board.orig_coord.items()},
  }

  for chip in ans['orig_x']:

    ## Modifying the original x coordinates to allow for data point selection
    # In web interface
    all_x = [x for d, x in ans['orig_x'].items()]
    if all_x.count(ans['orig_x'][chip]) > 1:
      ans['orig_x'][chip] = ans['orig_x'][chip] + 0.05 * random.random()

    ## Updating the visual coordinates if they exists
    if any(session.cmd.board.vis_coord[chip]):
      ## The reference z value would be the one at closest calibration distance
      z = min(session.cmd.board.vis_coord[chip].keys())
      ans['vis_x'][chip] = session.cmd.board.vis_coord[chip][z]
      ans['vis_y'][chip] = session.cmd.board.vis_coord[chip][z]
    else:
      ans['vis_x'][chip] = -100
      ans['vis_y'][chip] = -100

    ## Updating the lumi calibrated coordinates if they exists
    if any(session.cmd.board.lumi_coord[chip]):
      ## The reference z value would be the one at closest calibration distance
      z = min(session.cmd.board.lumi_coord[chip].keys())
      ans['lumi_x'][chip] = session.cmd.board.lumi_coord[chip][z]
      ans['lumi_y'][chip] = session.cmd.board.lumi_coord[chip][z]
    else:
      ans['lumi_x'][chip] = -100
      ans['lumi_y'][chip] = -100

  socketio.emit('tileboard-layout',
                str(ans).replace('\'', '"'),
                broadcast=True,
                namespace='/monitor')

