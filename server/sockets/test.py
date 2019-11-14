from flask_socketio import emit
import threading
import datetime
import time
import numpy as np
import np.random

from .. import socketio, start_time

realtime_thread = threading.Thread()


@socketio.on('connect')
def test_connect():
  print('New client connected')
  emit('confirm', {'start': start_time.strftime('%Y/%m/%d/ %H:%M:%S')}, broadcast=True)
  global realtime_thread
  if not realtime_thread.isAlive():
    print("Starting Thread")
    realtime_thread = threading.Thread(target=monitor_update)
    realtime_thread.start()


def monitor_update():
  while (True):
    central = 5 * np.random.random()
    for _ in range(10):
      timestamp = datetime.datetime.now()
      val1 = central+15 + 0.5 * np.random.random()
      val2 = central+15 + 0.2 * np.random.random()
      val3 = central + 6 + 0.1 * np.random.random()
      val4 = central + 7 + 0.2 * np.random.random()
      print('update')
      socketio.emit('monitor-update', {
          # Striping to seconds only
          'time': str(int((timestamp - start_time).total_seconds())),
          'temp1': str(val1),
          'temp2': str(val2),
          'volt1': str(val3),
          'volt2': str(val4)
      },
                    broadcast=True)
      time.sleep(1)

