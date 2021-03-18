from flask import Flask, render_template, Response, jsonify
from flask_socketio import SocketIO
import datetime
import logging  ## System logging that is used by the application

## Command interface
import ctlcmd.cmdbase as cmdbase
import ctlcmd.motioncmd as motioncmd
import ctlcmd.getset as getset
import ctlcmd.digicmd as digicmd
import ctlcmd.viscmd as viscmd
import ctlcmd.picocmd as picocmd
import cmod.logger as logger
import sys, copy, io, json, os, re

socketio = SocketIO(debug=False, async_mode='threading', )
#cors_allow_origins='*' )

from .sockets import session
from .sockets.parsing import *


def create_server_flask(debug=False):
  """
  Generating the server instance, keeping the app instance as a member of the
  global socketio object so other members can use this.
  """
  socketio.app = Flask(__name__)
  socketio.app.debug = debug

  @socketio.app.route('/')
  def index():
    """
    This is the main page the is to be rendered to the front user. The
    corresponding file can be found in the server/static/template/index.html
    path.
    """
    return render_template('index.html')

  @socketio.app.route('/debug')
  def expert():
    """
    This is the page containing the debugging GUI, mainly used for the fast data
    turn around and a simple interface for saving single commands and display the
    output in a simplified data format. This corresponding file is found in the
    server/static/template/debug.html path.
    """
    return render_template('debug.html')

  @socketio.app.route('/playground')
  def playground():
    """
    This URL is for testing display functions only.
    """
    return render_template('playground.html')

  """
  URLs used for local file exposure. In this framework, local file exposures are
  performed using AJAX requests. The following functions returns the requested
  URLS.
  """

  @socketio.app.route('/geometry/<boardtype>')
  def geometry(boardtype):
    """
    The geometry json files. These files correspond directly to the json files in
    the cfg/geometry/ directory if they exists.
    """
    if os.path.exists('cfg/geometry/' + boardtype + '.json'):
      with open('cfg/geometry/' + boardtype + '.json', 'r') as f:
        x = json.load(f)
        return jsonify(x)
    else:
      return {}, 404  # Return an empty json file with a error 404

  @socketio.app.route('/report/<reporttype>')
  def status(reporttype):
    """
    Instead of report via a socket command, display updates are performed using
    the call to a pseudo JSON file that contains the current status of the
    calibration session. This "file" is generated using a python dictionary. To
    reduced the required libraries in the various files. The jsonify routine is
    called here. The various report function should ensure that the return is
    json compliant.
    """
    return jsonify(session_report(reporttype))  #define in parsing.py

  @socketio.app.route('/data/<process>/<detid>')
  def data(process, detid):
    """
    Returning the data of a certain calibration process on a detector elements in
    json format. This aims to minimized the amount of time the same piece of data
    needs to be transported over the network.
    """
    return jsonify(get_cached_data(process, detid))  # Defined in parsing.py

  @socketio.app.route('/debug_data/<process>')
  def debugdata(process):
    """
    Returning the data of some debug session in json format.
    """
    return jsonify(get_debug_data(process)) # Defined in parsing.py

  @socketio.app.route('/visual')
  def visual():
    """
    This is a pseudo URL, which responds with the current camera image stored in
    the session memory, as a byte stream of a JPEG image file. The format of the
    Response object is found from reference:
    https://medium.com/datadriveninvestor/
    video-streaming-using-flask-and-opencv-c464bf8473d6
    """
    return Response(current_image_bytes(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

  @socketio.on('connect', namespace='/sessionsocket')
  def establish_connection():
    print('Connection established')
    socket_connect(socketio)

  @socketio.on('run-action-cmd', namespace='/sessionsocket')
  def run_action_cmd_socket(msg):
    run_action(socketio, msg)

  @socketio.on('complete-user-action', namespace='/sessionsocket')
  def complete_user_action_socket(msg):
    complete_user_action(socketio)

  ## Resetting the socket application stuff
  socketio.init_app(socketio.app)

  # Duplicating the session to allow for default override.
  prog_parser = copy.deepcopy(session.cmd.set.parser)
  # Augmenting help messages
  prog_parser.prog = "gui_control.py"
  prog_parser.add_argument('-h',
                           '--help',
                           action='store_true',
                           help='print help message and exit')

  ## Using map to store Default values:
  default_overide = {
      '--printerdev': '/dev/ttyUSB0',
      '--camdev': '/dev/video0',
      #'-boardtype': 'cfg/static_calib.json',
      '--action': 'cfg/useractions.json',
      '--picodevice': 'MYSERIAL',  #Cannot actually set. Just dummy for now
      #'-remotehost' : ['hepcms.umd.edu', '']
  }

  for action in prog_parser._actions:
    for option, default in default_overide.items():
      if option in action.option_strings:
        action.default = default

  args = prog_parser.parse_args()

  if args.help:
    prog_parser.print_help()
    sys.exit(0)

  try:
    session.cmd.set.run(args)
    session.cmd.gpio.init()
  except Exception as err:
    logger.printerr(str(err))
    logger.printwarn(
        'There was error in the setup process, program will '
        'continue but will most likely misbehave! Use at your own risk!')

  return socketio.app
