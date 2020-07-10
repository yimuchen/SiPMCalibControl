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
          'orig': session.cmd.board.get_det(detid).orig_coord,
          'lumi': session.cmd.board.get_det(detid).orig_coord,
          'vis': session.cmd.board.get_det(detid).orig_coord
      }
      for detid in session.cmd.board.dets()
  }

  for detid in ans:
    det = session.cmd.board.get_det(detid)
    ## Updating the visual coordinates if they exists
    if any(det.vis_coord):
      ## The reference z value would be the one at closest calibration distance
      z = min(det.vis_coord.keys())
      ans[detid]['vis'] = det.vis_coord[z]
    else:
      ans[detid]['vis'] = [-100, -100]

    ## Updating the lumi calibrated coordinates if they exists
    if any(det.lumi_coord):
      ## The reference z value would be the one at closest calibration distance
      z = min(det.lumi_coord.keys())
      ans[detid]['lumi'] = [det.lumi_coord[z][0], det.lumi_coord[z][2]]
    else:
      ans[detid]['lumi'] = [-100, -100]

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
    report = {
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
    }

    print("Reporting readout")
    print(report)
    socketio.emit('update-readout-results',
                  report,
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
