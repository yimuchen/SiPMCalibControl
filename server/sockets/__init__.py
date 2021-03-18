# List of all socket functions in various files
import ctlcmd.cmdbase as cmdbase
import ctlcmd.motioncmd as motioncmd
import ctlcmd.getset as getset
import ctlcmd.digicmd as digicmd
import ctlcmd.viscmd as viscmd
import ctlcmd.picocmd as picocmd
import ctlcmd.drscmd as drscmd

## Additional python libraries
import datetime


class Session(object):
  """
  Session object that contains all of the session parameters. Since a bunch of
  the manipulation of the data member is heavily tied with the calibration
  processes, this fill will only contain a list the data members. The actual
  manipulation of the data members will be written in the action.py file behind
  the calibration part.
  """

  STATE_IDLE = 0
  STATE_RUN_PROCESS = 1
  STATE_WAIT_USER = 2

  CMD_PENDING = 1
  CMD_RUNNING = 2
  CMD_COMPLETE = 0

  SESSION_TYPE_NONE = 0
  SESSION_TYPE_SYSTEM = 1
  SESSION_TYPE_STANDARD = 2

  def __init__(self):
    self.cmd = cmdbase.controlterm([
        motioncmd.moveto,
        motioncmd.movespeed,
        motioncmd.sendhome,
        motioncmd.zscan,
        motioncmd.lowlightcollect,
        motioncmd.halign,
        viscmd.visualset,
        viscmd.visualhscan,
        viscmd.visualzscan,
        viscmd.visualmaxsharp,
        #viscmd.visualshowdet,
        viscmd.visualcenterdet,
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
        drscmd.drsset,
        drscmd.drscalib,
        drscmd.drsrun,
    ])

    ## Allowing for the socket to receive commands immediately on start up
    self.state = self.STATE_IDLE
    self.session_type = self.SESSION_TYPE_NONE
    self.run_results = 0

    ## Self monitoring thread
    self.start_time = datetime.datetime.now()
    self.monitor_thread = None
    self.calib_session_time = datetime.datetime.now()
    self.reference_session = ''

    # Ordered list of detectors
    self.order_dets = []

    ## Data caching
    self.zscan_cache = {}
    self.lowlight_cache = {}
    self.lumialign_cache = {}
    self.visual_cache = {}

    ## Progress keeping stuff
    self.progress_check = {}

    ## Stuff related to the generation of standard commands
    self.zscan_samples = 100
    self.zscan_zlist_sparse = [10, 15, 20, 50]
    self.zscan_zlist_dense = [ 10, 12, 14, 16, 18, 20, 30 ]
    self.zscan_power_list = [0.1, 0.5, 0.8, 1.0]

    self.lowlight_samples = 1000
    self.lowlight_pwm = 0.5
    self.lowlight_zval = 30

    self.lumialign_zval = 10
    self.lumialign_pwm = 0.5
    self.lumialign_range = 6
    self.lumialign_distance = 2
    self.lumialign_samples = 100

    self.visual_zval = 5


## declaration of global object
session = Session()
