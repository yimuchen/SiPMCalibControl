#!/usr/bin/env python3
import datetime
from server import create_server_flask, socketio

if __name__ == '__main__':
  app = create_server_flask()
  socketio.run(app, host='0.0.0.0', port=9100)


