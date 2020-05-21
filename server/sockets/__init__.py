# List of all socket functions in various files
import ctlcmd.cmdbase as cmdbase
import ctlcmd.motioncmd as motioncmd
import ctlcmd.getset as getset
import ctlcmd.digicmd as digicmd
import ctlcmd.viscmd as viscmd
import ctlcmd.picocmd as picocmd

## Additional python libraries
import datetime


class Session(object):
  """
  Session object that contains all of the session parameters
  """

  STATE_IDLE = 0
  STATE_RUN_PROCESS = 1
  STATE_WAIT_USER = 2

  def __init__(self):
    self.cmd = cmdbase.controlterm([
        motioncmd.moveto, motioncmd.movespeed, motioncmd.sendhome,
        motioncmd.zscan, motioncmd.lowlightcollect, motioncmd.halign,
        viscmd.visualset, viscmd.visualhscan, viscmd.visualzscan,
        viscmd.visualmaxsharp, viscmd.visualshowdet, viscmd.visualcenterdet,
        getset.set, getset.get, getset.getcoord, getset.savecalib,
        getset.loadcalib, getset.lighton, getset.lightoff, getset.promptaction,
        digicmd.pulse, picocmd.picoset, picocmd.picorunblock, picocmd.picorange,
    ])

    ## Allowing for the socket to receive commands immediately on start up
    self.state = self.STATE_IDLE

    ## Self monitoring thread
    self.start_time = datetime.datetime.now()
    self.monitor_thread = None

    self.calib_session_time = datetime.datetime.now()

    ## Data caching
    self.zscan_cache = {}
    self.lowlight_cache = {}
    self.lumialign_cache = {}
    self.zscan_updates = []
    self.lowlight_updates = []
    self.lumialign_update = []

    ## Progress keeping stuff
    self.progress_check = {}
    self.valid_reference_list = []

    ## Stuff related to the generation of standard commands
    self.zscan_zlist_sparse = [10, 15, 20, 50, 70, 100, 150, 200, 250, 300]
    self.zscan_zlist_dense = [
        10, 12, 14, 16, 18, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, 250,
        300
    ]
    self.zscan_power_list = [0.1, 0.5, 0.8, 1.0]


## declaration of global object
session = Session()