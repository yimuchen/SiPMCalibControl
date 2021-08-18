# List of all socket functions in various files
import ctlcmd.cmdbase as cmdbase
import ctlcmd.motioncmd as motioncmd
import ctlcmd.getset as getset
import ctlcmd.digicmd as digicmd
import ctlcmd.viscmd as viscmd
import ctlcmd.picocmd as picocmd
import ctlcmd.drscmd as drscmd

import cmod.logger as log
## Additional python libraries
import datetime, time


class Session(object):
  """
  Session object that contains all of the session parameters. Since a bunch of
  the manipulation of the data member is heavily tied with the calibration
  processes, this fill will only contain a list the data members. The actual
  manipulation of the data members will be written in the action.py file behind
  the calibration part.

  In addition, so pass the full functionality of the underlying cmd class to the
  GUI terminal, we will be using the following file descriptors to interact with
  the cmd class. Two descriptors will be opened for each of the file input output
  sessions as reading and writing will need two different descriptor values. For
  the sake of having semi-servicable terminal interactions, a string buffer and
  buffer index is also used to keep track of the current line.

  This class is strictly a container class, with minimal amounts of data
  manipulation. All manipulations of the global container instance 'session' is
  handled by the various function methods in the .py files.
  """

  STATE_IDLE = 0
  STATE_RUN_PROCESS = 1
  STATE_EXEC_CMD = 2
  STATE_WAIT_USER = 3

  CMD_PENDING = 1
  CMD_RUNNING = 2
  CMD_COMPLETE = 0

  SESSION_TYPE_NONE = 0
  SESSION_TYPE_SYSTEM = 1
  SESSION_TYPE_STANDARD = 2

  def __init__(self):
    # Overwriting the system stdin with new pipe
    self.session_output = open('session_output.txt', 'w')
    self.session_output_monitor = open('session_output.txt', 'r')
    self.input_buffer = ''  # Using a string to store
    self.input_buffer_index = 0  # Used to store where the cursor currently is.

    self.cmd = cmdbase.controlterm([
        motioncmd.moveto,  #
        motioncmd.movespeed,  #
        motioncmd.sendhome,  #
        motioncmd.zscan,  #
        motioncmd.lowlightcollect,  #
        motioncmd.halign,  #
        motioncmd.getcoord,  #
        viscmd.visualset,  #
        viscmd.visualhscan,  #
        viscmd.visualzscan,  #
        viscmd.visualmaxsharp,  #
        #viscmd.visualshowdet,
        viscmd.visualcenterdet,  #
        # getset.exit,  #
        getset.set,  #
        getset.get,  #
        getset.wait,  #
        getset.savecalib,  #
        getset.loadcalib,  #
        # getset.promptaction,  #
        getset.runfile,  #
        digicmd.pulse,  #
        digicmd.pwm,  #
        digicmd.setadcref,  #
        digicmd.showadc,  #
        digicmd.lighton,  #
        digicmd.lightoff,  #
        picocmd.picoset,  #
        picocmd.picorunblock,  #
        picocmd.picorange,  #
        drscmd.drsset,  #
        drscmd.drscalib,  #
        drscmd.drsrun  #
    ],
                                   stdout=self.session_output)
    log.set_logging_descriptor(self.session_output.fileno())

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
    self.zscan_zlist_dense = [10, 12, 14, 16, 18, 20, 30]
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

  def __del__(self):
    """
    Closing the IO session file
    """
    self.session_output.close()
    self.session_output_monitor.close()

  def run_single_cmd(self, cmd):
    """
    Running a single command via for the underlying session with return value.
    """
    print('running a single cmd:', cmd, '|||')
    cmd = self.cmd.precmd(cmd)
    sig = self.cmd.onecmd(cmd)
    sig = self.cmd.postcmd(sig, cmd)
    self.cmd.stdout.flush()
    return sig

  def is_running_cmd(self):
    return (self.cmd.last_cmd_start == self.cmd.last_cmd_stop
            and self.cmd.last_cmd_start != None)


## declaration of global object
session = Session()
