from flask_socketio import emit
import threading
import datetime
import time
import numpy as np

from .. import socketio, start_time
from .common import gen_cmdline_options

realtime_thread = threading.Thread()


@socketio.on('connect', namespace='/monitor')
def test_connect():
  print('Monitor client connected')

  emit('confirm', {'start': start_time.strftime('%Y/%m/%d/ %H:%M:%S')},
       broadcast=True,
       namespace='/monitor')

  ## Systemsettings update
  visual_settings_update({})

  ## Starting the continuous monitoring thread.
  global realtime_thread
  if not realtime_thread.isAlive():
    print("Starting Thread")
    realtime_thread = threading.Thread(target=monitor_update)
    realtime_thread.start()


def monitor_update():
  """
  Real time update of system information.
  """
  counter = 0
  while (True):
    if counter % 10 == 0: central = 5 * np.random.random(0)

    ## Return variables are all from ADC monitors
    current_time = (datetime.datetime.now() - start_time).total_seconds()
    val0 = 0
    val1 = 0
    val2 = 0
    val3 = 0

    try:
      val0 = socketio.cmd.gpio.adc_read(0)
      val1 = socketio.cmd.gpio.adc_read(0)
      val2 = socketio.cmd.gpio.adc_read(0)
      val3 = socketio.cmd.gpio.adc_read(0)
    except:  ## For local testing
      val0 = central + 15 + 0.5 * np.random.random()
      val1 = central + 15 + 0.2 * np.random.random()
      val2 = central + 6 + 0.1 * np.random.random()
      val3 = central + 7 + 0.2 * np.random.random()

    socketio.emit('monitor-update', {
        'time': str(int(current_time)),
        'temp1': str(val0),
        'temp2': str(val1),
        'volt1': str(val2),
        'volt2': str(val3)
    },
                  broadcast=True,
                  namespace='/monitor')
    time.sleep(1)
    counter = counter + 1


def visual_settings_update(data):
  if len(data):
    data['ratio'] = float(data['ratio'])/100
    data['poly'] = float(data['poly'])/100
    cmdline = gen_cmdline_options(
      data, ['threshold', 'blur', 'lumi', 'size', 'ratio', 'poly'])
    socketio.cmd.onecmd('visualset ' +cmdline)

  socketio.emit('visual-settings-update', {
      'threshold': socketio.cmd.visual.threshold,
      'blur': socketio.cmd.visual.blur_range,
      'lumi': socketio.cmd.visual.lumi_cutoff,
      'size': socketio.cmd.visual.size_cutoff,
      'ratio': socketio.cmd.visual.ratio_cutoff * 100,
      'poly': socketio.cmd.visual.poly_range * 100,
  },
                namespace='/monitor')
