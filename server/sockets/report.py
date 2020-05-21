"""
report.py

This files documents the generation of status and data reporting functions.
"""
import datetime

# Importing global objects
from . import session


def ReportSystemStatus(socketio):
  current_time = (datetime.datetime.now() - session.start_time).total_seconds()
  socketio.emit('report-status', {
      'time':
      int(current_time),
      ## Constant monitor variables
      'temp1':
      session.cmd.gpio.ntc_read(0),
      'temp2':
      session.cmd.gpio.rtd_read(1),
      'volt1':
      session.cmd.gpio.adc_read(2),
      'volt2':
      session.cmd.gpio.adc_read(3),
      'coord':
      [session.cmd.gcoder.opx, session.cmd.gcoder.opy, session.cmd.gcoder.opz],
      'state':
      session.state
  },
                broadcast=True,
                namespace='/sessionsocket')


def ReportTileboardLayout(socketio):
  ans = {
      detid: {
          'orig': session.cmd.board.orig_coord[detid],
          'lumi': session.cmd.board.orig_coord[detid],
          'vis': session.cmd.board.orig_coord[detid]
      }
      for detid in session.cmd.board.orig_coord.keys()
  }

  for det in ans:
    ## Updating the visual coordinates if they exists
    if any(session.cmd.board.vis_coord[det]):
      ## The reference z value would be the one at closest calibration distance
      z = min(session.cmd.board.vis_coord[det].keys())
      ans[det]['vis'] = session.cmd.board.vis_coord[det][z]
    else:
      ans[det]['vis'] = [-100, -100]

    ## Updating the lumi calibrated coordinates if they exists
    if any(session.cmd.board.lumi_coord[det]):
      ## The reference z value would be the one at closest calibration distance
      z = min(session.cmd.board.lumi_coord[det].keys())
      ans[det]['lumi'] = [
          session.cmd.board.lumi_coord[det][z][0],
          session.cmd.board.lumi_coord[det][z][2]
      ]
    else:
      ans[det]['lumi'] = [-100, -100]

  socketio.emit('tileboard-layout',
                str(ans).replace('\'', '"'),
                broadcast=True,
                namespace='/sessionsocket')


def ReportProgress(socketio):
  socketio.emit('progress-update',
                session.progress_check,
                broadcast=True,
                namespace='/sessionsocket')


def ReportReadout(socketio):
  if session.state == session.STATE_IDLE:
    """
    In the case that the session state is idle, and there are no additional
    update store in the system. Do not return anything.
    """
    if (len(session.zscan_updates) == 0 and len(session.lowlight_updates) == 0
        and len(session.lumialign_updates) == 0):
      return

  try:
    socketio.emit('update-readout-results', {
        'zscan': {
            detid: session.zscan_cache[detid]
            for detid in session.zscan_updates
            if len(session.zscan_cache[detid]) > 0
        },
        'lowlight': {
            detid: [
                session.lowlight_cache[detid][0].tolist(),
                session.lowlight_cache[detid][1].tolist()
            ]
            for detid in session.lowlight_updates
            if len(session.lowlight_cache[detid]) > 0
        },
        'lumialign': {
            detid: session.lumialign_cache[detid]
            for detid in session.lumialign_updates
            if len(session.lumialign_cache[detid]) > 0
        }
    },
                  broadcast=True,
                  namespace='/sessionsocket')
  except:
    pass

  ## Wiping the list after the update has been performed
  session.zscan_updates = []
  session.lowlight_updates = []
  session.lumialign_updates = []


def PrepareReportAllCache():
  session.zscan_updates = [
      detid for detid in session.zscan_cache
      if len(session.zscan_cache[detid]) > 0
  ]
  session.lowlight_updates = [
      detid for detid in session.lowlight_cache
      if len(session.lowlight_cache[detid]) > 0
  ]
  session.lumialign_updates = [
      detid for detid in session.lumialign_cache
      if len(session.lumialign_cache[detid]) > 0
  ]


def ReportValidReference(socketio):
  socketio.emit('report-valid-reference',
                session.valid_reference_list,
                boardcast=True,
                namespace='/sessionsocket')


def ReportSignoffType(socketio):
  if len(session.cmd.board.dets()) == 0:
    return

  if any(int(det) >= 0 for det in session.cmd.board.dets()):
    socketio.emit('report-sign-off',
                  'standard',
                  boardcast=True,
                  namespace='/sessionsocket')
  else:
    socketio.emit('report-sign-off',
                  'system',
                  boardcast=True,
                  namespace='/sessionsocket')
