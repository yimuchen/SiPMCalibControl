#!/usr/bin/env python3
"""
Script used to initiate the GUI server instance. The main documentation will be
given in the files of the server/ directory
"""
from server import create_server_flask, socketio
import sys

if __name__ == '__main__':
  print('Created app')
  app = create_server_flask()
  print('socketio.run')
  socketio.run(app, host='0.0.0.0', port=9100)
  print('stoping socketio')
  sys.exit(0)
