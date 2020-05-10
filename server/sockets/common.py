## Commonly used functions

from . import session

from time import sleep
import random
import numpy as np


def MessageUserAction(socketio, msg):
  socketio.emit('useraction', msg, namespace='/sessionsocket', broadcast=True)


def WaitUserAction(socketio, msg):
  print('Sending user action stuff', msg)
  MessageUserAction(socketio, msg)
  session.state = session.STATE_WAIT_USER
  session.waiting_msg = msg
  while (session.state == session.STATE_WAIT_USER):
    sleep(0.1)  ## Updating every 0.1 seconds


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
      chipid: {
          'orig': session.cmd.board.orig_coord[chipid],
          'lumi': session.cmd.board.orig_coord[chipid],
          'vis': session.cmd.board.orig_coord[chipid]
      }
      for chipid in session.cmd.board.orig_coord.keys()
  }

  for chip in ans:
    ## Updating the visual coordinates if they exists
    if any(session.cmd.board.vis_coord[chip]):
      ## The reference z value would be the one at closest calibration distance
      z = min(session.cmd.board.vis_coord[chip].keys())
      ans[chip]['vis'] = session.cmd.board.vis_coord[chip][z]
    else:
      ans[chip]['vis'] = [-100, -100]

    ## Updating the lumi calibrated coordinates if they exists
    if any(session.cmd.board.lumi_coord[chip]):
      ## The reference z value would be the one at closest calibration distance
      z = min(session.cmd.board.lumi_coord[chip].keys())
      ans[chip]['lumi'] = session.cmd.board.lumi_coord[chip][z]
    else:
      ans[chip]['lumi'] = [-100, -100]

  socketio.emit('tileboard-layout',
                str(ans).replace('\'', '"'),
                broadcast=True,
                namespace='/sessionsocket')


def ReturnClearExisting(socketio):
  socketio.emit('clear-display', '', broadcast=True, namespace='/sessionsocket')

def DisplayMessage(socketio, msg):
  socketio.emit('display-message', msg, boardcast=True, namespace='/sessionsocket')
