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
        motioncmd.zscan, motioncmd.lowlightcollect, viscmd.visualset,
        viscmd.visualhscan, viscmd.visualzscan, viscmd.visualmaxsharp,
        viscmd.visualshowchip, viscmd.visualcenterchip, getset.set, getset.get,
        getset.getcoord, getset.savecalib, getset.loadcalib, getset.lighton,
        getset.lightoff, getset.promptaction, digicmd.pulse, picocmd.picoset,
        picocmd.picorunblock, picocmd.picorange,
    ])

    ## Allowing for the socket to receive commands immediately on start up
    self.state = self.STATE_IDLE

    ## Self monitoring thread
    self.start_time = datetime.datetime.now()

    ## Self
    self.monitor_thread = None

    ## Data caching
    self.zscan_cache = {}
    self.lowlight_cache = {}
    self.zscan_updates = []
    self.lowlight_updates = []


## declaration of global object
session = Session()