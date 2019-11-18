from flask import Flask, render_template
from flask_socketio import SocketIO
import datetime

## Command interface
import ctlcmd.cmdbase as cmdbase
import ctlcmd.motioncmd as motioncmd
import ctlcmd.getset as getset
import ctlcmd.digicmd as digicmd
import ctlcmd.viscmd as viscmd
import ctlcmd.picocmd as picocmd
import cmod.logger as logger
import sys
import copy

socketio = SocketIO(
  debug=False,
  async_mode='threading', )
  #cors_allow_origins='*' )
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

  ## Resetting the socket application stuff
  socketio.init_app(app)

  # Spawning cmdcontrol instance as a objected stored in the socketio object so
  # that every python function used for processing javascript input can use said
  # object.
  socketio.cmd = cmdbase.controlterm([
      motioncmd.moveto,
      motioncmd.movespeed,
      motioncmd.sendhome,
      motioncmd.halign,
      motioncmd.zscan,
      motioncmd.timescan,
      motioncmd.showreadout,
      viscmd.visualset,
      viscmd.visualhscan,
      viscmd.visualzscan,
      viscmd.visualmaxsharp,
      viscmd.visualshowchip,
      viscmd.visualcenterchip,
      getset.set,
      getset.get,
      getset.getcoord,
      getset.savecalib,
      getset.loadcalib,
      getset.lighton,
      getset.lightoff,
      getset.promptaction,
      digicmd.pulse,
      picocmd.picoset,
      picocmd.picorunblock,
      picocmd.picorange,
  ])
  # Duplicating the session to allow for default override.
  prog_parser = copy.deepcopy(socketio.cmd.set.parser)
  # Augmenting help messages
  prog_parser.prog = "control.py"
  prog_parser.add_argument('-h',
                           '--help',
                           action='store_true',
                           help='print help message and exit')

  ## Using map to store Default values:
  default_overide = {
      '-printerdev': '/dev/ttyUSB0',
      '-camdev': '/dev/video0',
      #'-boardtype': 'cfg/static_calib.json',
      '-action': 'cfg/useractions.json',
      '-picodevice': 'MYSERIAL',  #Cannot actually set. Just dummy for now
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
    socketio.cmd.set.run(args)
    socketio.cmd.gpio.init()
  except Exception as err:
    logger.printerr(str(err))
    logger.printwarn(
        'There was error in the setup process, program will '
        'continue but will most likely misbehave! Use at your own risk!')


  return app

