from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import numpy as np
import threading
import time
import datetime

from server import create_server_flask, socketio, start_time

if __name__ == '__main__':
  start_time = datetime.datetime.now()
  app = create_server_flask()
  socketio.run(app, host='0.0.0.0', port=9100)
