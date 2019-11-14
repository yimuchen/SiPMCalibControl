from flask import Flask, render_template
from flask_socketio import SocketIO
import datetime

socketio = SocketIO(async_mode='threading')
start_time = datetime.datetime.now()

## importing local socket functions after socketio declaration
from .sockets import __dummy__

def create_server_flask(debug=False):
  """
  Generating the server instance
  """
  app = Flask(__name__)
  app.debug = debug

  # Since this is a single paged document
  @app.route('/')
  def index():
    return render_template('index.html')

  ## Resetting the socket
  socketio.debug = debug
  socketio.init_app(app)

  return app

