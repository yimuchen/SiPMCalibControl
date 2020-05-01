import datetime
import time

from . import session

def monitor_update(socketio):
  """
  Real time update of system information.
  """
  counter = 0
  while (True):
    current_time = (datetime.datetime.now() - session.start_time).total_seconds()
    socketio.emit('monitor-update', {
        'time': str(int(current_time)),
        'temp1': str(session.cmd.gpio.ntc_read(0)),
        'temp2': str(session.cmd.gpio.rtd_read(1)),
        'volt1': str(session.cmd.gpio.adc_read(2)),
        'volt2': str(session.cmd.gpio.adc_read(3))
    },
                  broadcast=True,
                  namespace='/monitor')
    time.sleep(1)

def visual_settings_update(socketio, data):
  if len(data):
    data['ratio'] = float(data['ratio']) / 100
    data['poly'] = float(data['poly']) / 100
    cmdline = gen_cmdline_options(
        data, ['threshold', 'blur', 'lumi', 'size', 'ratio', 'poly'])
    session.cmd.onecmd('visualset ' + cmdline)

  socketio.emit('visual-settings-update', {
      'threshold': session.cmd.visual.threshold,
      'blur': session.cmd.visual.blur_range,
      'lumi': session.cmd.visual.lumi_cutoff,
      'size': session.cmd.visual.size_cutoff,
      'ratio': session.cmd.visual.ratio_cutoff * 100,
      'poly': session.cmd.visual.poly_range * 100,
  },
                namespace='/monitor')
