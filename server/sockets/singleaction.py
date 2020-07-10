## Commonly used functions

from . import session

from time import sleep


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


def ReturnClearExisting(socketio):
  socketio.emit('clear-display', '', broadcast=True, namespace='/sessionsocket')


def DisplayMessage(socketio, msg):
  socketio.emit('display-message',
                msg,
                broadcast=True,
                namespace='/sessionsocket')


def SignoffComplete(socketio):
  socketio.emit('signoff-complete',
                '',
                broadcast=True,
                namespace='/sessionsocket')


def RunCmdInput(msg):
  print(msg)
  print(msg)
  print(msg)
  print(msg)
  execute_cmd = msg['input']
  session.cmd.onecmd(execute_cmd)


def RunImageSettings(socketio, data):
  print(session)
  print(session.cmd)
  print(session.cmd.visual)
  session.cmd.visual.threshold = float(data['threshold'])
  session.cmd.visual.blur_range = int(data['blur'])
  session.cmd.visual.lumi_cutoff = int(data['lumi'])
  session.cmd.visual.size_cutoff = int(data['size'])
  session.cmd.visual.ratio_cutoff = float(data['ratio'])
  session.cmd.visual.poly_range = float(data['poly'])
  ReportImageSettings(socketio)


def ReportImageSettings(socketio):
  socketio.emit('report-image-settings', {
      'threshold': session.cmd.visual.threshold,
      'blur': session.cmd.visual.blur_range,
      'lumi': session.cmd.visual.lumi_cutoff,
      'size': session.cmd.visual.size_cutoff,
      'ratio': session.cmd.visual.ratio_cutoff,
      'poly': session.cmd.visual.poly_range,
  },
                broadcast=True,
                namespace='/sessionsocket')


def RunZScanSettings(socketio, data):
  session.zscan_samples = int(data['samples'])
  session.zscan_power_list = [float(x) for x in data['pwm']]
  session.zscan_zlist_dense = [float(z) for z in data['zlist_dense']]
  session.zscan_zlist_sparse = [float(z) for x in data['zlist_sparse']]
  ReportZscanSettings(socketio)


def ReportZScanSettings(socketio):
  socketio.emit('report-zscan-settings', {
      'samples': session.zscan_samples,
      'pwm': session.zscan_power_list,
      'zlist-dense': session.zscan_zlist_dense,
      'zlist-sparse': session.zscan_zlist_sparse,
  },
                broadcast=True,
                namespace='/sessionsocket')


def RunLowlightSettings(socketio, data):
  session.lowlight_samples = int(data['samples'])
  session.lowlight_pwm = float(data['pwm'])
  session.lowlight_zval = float(data['zval'])
  ReportLowlightSettings(socketio)


def ReportLowlightSettings(socketio):
  socketio.emit('report-lowlight-settings', {
      'samples': session.lowlight_samples,
      'pwm': session.lowlight_pwm,
      'zval': session.lowlight_zval,
  },
                broadcast=True,
                namespace='/sessionsocket')


def RunLumiAlignSettings(socketio, data):
  session.lumialign_samples = int(data['samples'])
  session.lumialign_pwm = float(data['pwm'])
  session.lumialign_zval = float(data['zval'])
  session.lumialign_range = float(data['range'])
  session.lumialign_distance = float(data['distance'])
  ReportLumiAlignSettings(socketio)


def ReportLumiAlignSettings(socketio):
  socketio.emit('report-lumialign-settings', {
      'samples': session.lowlight_samples,
      'pwm': session.lowlight_pwm,
      'zval': session.lowlight_zval,
      'range': session.lumialign_range,
      'distance': session.lumialign_distance
  },
                broadcast=True,
                namespace='/sessionsocket')


def RunPicoscopeSettings(socketio, data):
  try:
    print("Running picoscope commands")
    session.cmd.pico.setrange(0, int(data['channel-a-range']))
    session.cmd.pico.setrange(1, int(data['channel-b-range']))

    session.cmd.pico.settrigger(int(data['trigger-channel']),
                                int(data['trigger-direction']),
                                float(data['trigger-level']),
                                int(data['trigger-delay']), 0)
    session.cmd.pico.setblocknums(int(data['blocksize']), int(
        data['postsample']), int(data['presample']))
    sleep(1)
  except Exception as err:
    pass  ## Since the picosope might not be there

  ReportPicoscopeSettings(socketio)


def ReportPicoscopeSettings(socketio):
  socketio.emit('report-picoscope-settings', {
      'channel-a-range': session.cmd.pico.rangeA(),
      'channel-b-range': session.cmd.pico.rangeB(),
      'trigger-channel': session.cmd.pico.triggerchannel,
      'trigger-value': session.cmd.pico.triggerlevel,
      'trigger-direction': session.cmd.pico.triggerdirection,
      'trigger-delay': session.cmd.pico.triggerdelay,
      'trigger-presample': session.cmd.pico.presamples,
      'trigger-postsample': session.cmd.pico.postsamples,
      'blocksize': session.cmd.pico.ncaptures
  },
                broadcast=True,
                namespace='/sessionsocket')
