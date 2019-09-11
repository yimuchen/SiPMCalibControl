import cmod.gcoder as gcoder
import cmod.board as board
import cmod.logger as log
import cmod.trigger as trigger
import cmod.visual as visual
import cmod.readout as readout
import cmod.sshfiler as sshfiler
import cmod.pico as pico
import cmod.actionlist as actionlist
import cmod.sighandle as sig
import numpy as np
import cmd
import sys
import os
import argparse
import readline
import glob
import traceback
import re
import datetime


class controlterm(cmd.Cmd):
  """
  Control term is the class for parsing commands and passing the arguments
  to C functions for gantry and readout control.
  It also handles the command as classes to allow for easier interfacing
  """

  intro = """
    SiPM Calibration Gantry Control System
    Type help or ? to list commands.
    Type help <cmd> for the individual help messages of each commands
    """
  prompt = 'SiPMCalib> '

  def __init__(self, cmdlist):
    cmd.Cmd.__init__(self)

    self.sshfiler = sshfiler.SSHFiler()
    self.gcoder = gcoder.GCoder()
    self.board = board.Board()
    self.visual = visual.Visual()
    self.pico = pico.PicoUnit()
    self.readout = readout.readout(self)  # Must be after picoscope setup
    self.trigger = trigger.Trigger()
    self.action = actionlist.ActionList()

    ## Creating command instances and attaching to associated functions
    for com in cmdlist:
      comname = com.__name__.lower()
      dofunc = 'do_' + comname
      helpfunc = 'help_' + comname
      compfunc = 'complete_' + comname
      self.__setattr__(comname, com(self))
      self.__setattr__(dofunc, self.__getattribute__(comname).do)
      self.__setattr__(helpfunc, self.__getattribute__(comname).callhelp)
      self.__setattr__(compfunc, self.__getattribute__(comname).complete)
      self.__getattribute__(comname).cmd = self

    # Removing hyphen and slash as completer delimiter, as it messes with
    # command auto completion
    readline.set_completer_delims(' \t\n`~!@#$%^&*()=+[{]}\\|;:\'",<>?')

  def postcmd(self, stop, line):
    log.printmsg("")  # Printing extra empty line for aesthetics

  def get_names(self):
    """
    Overriding the the original get_names command to allow for the dynamic
    introduced commands to be listed.
    """
    return dir(self)

  def do_exit(self, line):
    sys.exit(0)

  def help_exit(self):
    "Exit program current session"

  # running commands listed in the a file requires the onecmd() method. So it
  # cannot be declared using an external class.
  def do_runfile(self, line):
    """
    usage: runfile <file>

    Executing commands listed in a file. This should be used for standard
    calibration procedures only.
    """
    if len(line.split()) != 1:
      log.printerr('Please only specify one file!')
      return

    if not os.path.isfile(line):
      log.printerr('Specified file could not be opened!')
      return

    with open(line) as f:
      for cmdline in f.readlines():
        status = self.onecmd(cmdline.strip())
        if status != controlcmd.EXIT_SUCCESS:
          log.printerr(('Command [{0}] in file [{1}] has failed. Exiting '
                        '[runfile] command').format(cmdline.strip(), f.name))
          break
    return

  def complete_runfile(self, text, line, start_index, end_index):
    return controlcmd.globcomp(text)

  @staticmethod
  def yn_prompt(question, default='no'):
    """
    Ask a yes/no question via input() and return their answer.

    'question' is a string that is presented to the user.
    'default' is the presumed answer if the user just hits <Enter>.
              It must be 'yes' (the default), 'no' or None (meaning
              an answer is required of the user).

    The 'answer' return value is True for 'yes' or False for 'no'.
    """
    valid = {'yes': True, 'ye': True, 'y': True, 'no': False, 'n': False}
    if default is None:
      prompt = ' [y/n] '
    elif default.lower() == 'yes':
      prompt = ' [Y/n] '
    elif default.lower() == 'no':
      prompt = ' [y/N] '
    else:
      raise ValueError('invalid default answer: {0}'.format(default))

    while True:
      print(question + prompt)
      choice = input().lower()
      if default is not None and choice == '':
        return valid[default]
      elif choice in valid:
        return valid[choice]
      else:
        log.printerr(
            'Please respond with \'yes\' or \'no\' (or \'y\' or \'n\').\n')


class controlcmd():
  """
  The control command is the base interface for defining a command in the
  terminal class, the instance do, callhelp and complete functions corresponds
  to the functions do_<cmd>, help_<cmd> and complete_<cmd> functions in the
  vallina python cmd class. Here we will be using the argparse class by default
  to call for the help and complete functions
  """
  PARSE_ERROR = -1
  EXECUTE_ERROR = -2
  EXIT_SUCCESS = 0

  LOG = "DUMMY"

  def __init__(self, cmdsession):
    """
    Initializer declares an argument parser class with the class name as the
    program name and the class doc string as the description string. This
    greatly reduces the verbosity of writing custom commands.
    Each command will have accession to the cmd session, and by extension,
    every control object the could potentially be used
    """
    self.parser = argparse.ArgumentParser(prog=self.__class__.__name__.lower(),
                                          description=self.__class__.__doc__,
                                          add_help=False)
    self.cmd = cmdsession
    self.sighandle = None

    ## Reference to control objects for all commands
    self.sshfiler = cmdsession.sshfiler
    self.gcoder = cmdsession.gcoder
    self.board = cmdsession.board
    self.visual = cmdsession.visual
    self.pico = cmdsession.pico
    self.readout = cmdsession.readout  # Must be after pico setup
    self.trigger = cmdsession.trigger
    self.action = cmdsession.action

  def do(self, line):
    """
    Execution of the commands automatically handles the parsing in the parse
    method. Additional parsing is allowed by overloading the parse method in the
    children classes. The actual execution of the function is handled in the run
    method.
    """
    def print_tracestack():
      exc_msg = traceback.format_exc()
      exc_msg = exc_msg.splitlines()
      exc_msg = exc_msg[1:-1]  ## Remove traceback and error line.
      for idx in range(0, len(exc_msg), 2):
        file = re.findall(r'\"[A-Za-z0-9\/\.]+\"', exc_msg[idx])
        if len(file):  # For non-conventional error messages
          file = file[0].strip().replace('"', '')
        else:
          continue

        line = re.findall(r'line\s[0-9]+', exc_msg[idx])
        if len(line):  # For non-conventional error messages
          line = [int(s) for s in line[0].split() if s.isdigit()][0]
        else:
          continue

        content = exc_msg[idx + 1].strip()

        stackline = ''
        stackline += log.RED('{0:4d} | '.format(line))
        stackline += log.YELLOW('{0} | '.format(file))
        stackline += content
        log.printmsg(stackline)

    try:
      args = self.parse(line)
    except Exception as err:
      print_tracestack()
      self.printerr(str(err))
      return controlcmd.PARSE_ERROR

    try:
      self.run(args)
    except Exception as err:
      print_tracestack()
      self.printerr(str(err))
      return controlcmd.EXECUTE_ERROR

    log.clear_update()
    return controlcmd.EXIT_SUCCESS

  def callhelp(self):
    """
    Printing the help message via the ArgumentParse in built functions.
    """
    self.parser.print_help()

  def complete(self, text, line, start_index, end_index):
    """
    Auto completion of the functions. This function scans the options stored in
    the parse class and returns a string of things to return.
    - text is the word on this cursor is on (excluding tail)
    - line is the full input line string (including command)
    - start_index is the starting index of the word the cursor is at in the line
    - end_index is the position of the cursor in the line
    """
    cmdname = self.__class__.__name__.lower()
    textargs = line[len(cmdname):start_index].strip().split()
    prevtext = textargs[-1] if len(textargs) else ''
    options = [opt for x in self.parser._actions for opt in x.option_strings]

    def optwithtext():
      if text:
        return [x for x in options if x.startswith(text)]
      return options

    if prevtext in options:
      action = next(
          x for x in self.parser._actions if (prevtext in x.option_strings))
      if type(action.type) == argparse.FileType:
        return controlcmd.globcomp(text)
      if action.nargs == 0:  ## For store_true options
        return optwithtext()
      return ['input type: ' + str(action.type), 'Help: ' + action.help]
    else:
      return optwithtext()

  ## Overloading for less verbose message printing
  def update(self, text):
    """
    Printing an update message using the static variable "LOG".
    """
    log.update(self.LOG, text)

  def printmsg(self, text):
    """
    Printing a message new-line using the static variable "LOG".
    """
    log.clear_update()
    log.printmsg(self.LOG, text)

  def printerr(self, text):
    """
    Printing a error message with a standard red "ERROR" header.
    """
    log.clear_update()
    log.printerr(text)

  def printwarn(self, text):
    """
    Printing a warning message with a standard yellow "WARNING" header.
    """
    log.clear_update()
    log.printerr()

  def run(self, args):
    """
    Functions that require command specific definitions, should be overwritten in
    the descendent classes
    """
    pass

  def parse(self, line):
    """
    Default parsing arguments, overriding the system exits exception to that the
    session doesn't end with the user inputs a bad command. Additional parsing
    could be achieved by overloading this methods.
    """
    try:
      arg = self.parser.parse_args(line.split())
    except SystemExit as err:
      self.printerr(str(err))
      raise Exception('Cannot parse input')
    return arg

  def init_handle(self):
    """
    Creating the a new instance of the signal handling class to be used for
    process handling.
    """
    self.sighandle = sig.SigHandle()

  def check_handle(self, args):
    """
    Checking the status of the signal handle, closing files and raising an
    exception if a termination signal was ever set by the user.
    """
    check_msg = 'TERMINATION SIGNAL RECEIVED, '
    flush_msg = 'FLUSHING FILE CONTENTS THEN '
    exit_msg = 'EXITING COMMAND'
    msg = check_msg + exit_msg if hasattr(args, 'savefile') \
      else check_msg + flush_msg + exit_msg

    if self.sighandle.terminate:
      self.printmsg(msg)
      if hasattr(args, 'savefile'):
        args.savefile.flush()
        args.savefile.close()
      raise Exception('TERMINATION SIGNAL')

  def move_gantry(self, x, y, z, verbose):
    """
    Wrapper for gantry motion command, suppresses the exception raised for in
    case that the gantry isn't connected so that one can test with pre-defined
    models.
    """
    try:
      # Try to move the gantry. Even if it fails there will be fail safes
      # in other classes
      self.gcoder.moveto(x, y, z, verbose)
    except:
      pass

  def add_xychip_options(self):
    """
    Adding XY motion commands
    """
    self.parser.add_argument('-x',
                             type=float,
                             help=('Specifying the x coordinate explicitly [mm].'
                                   ' If none is given the current gantry '
                                   'position will be used instead'))
    self.parser.add_argument('-y',
                             type=float,
                             help=('Specifying the y coordinate explicitly [mm].'
                                   ' If none is given the current gantry '
                                   'position will be used.'))
    self.parser.add_argument('-c',
                             '--chipid',
                             type=str,
                             help=('Specify x-y coordinates via chip id, input '
                                   'negative value to indicate that the chip is '
                                   'a calibration one (so you can still specify '
                                   'coordinates with it)'))

  def add_readout_option(self):
    """
    Adding readout options
    """
    self.parser.add_argument('--mode',
                             type=int,
                             choices=[-1, 1, 2],
                             help=('Readout method to be used: 1:picoscope, '
                                   '2:ADC, -1:Predefined model'))
    self.parser.add_argument('--channel',
                             type=int,
                             default=0,
                             help='Input channel to use')
    self.parser.add_argument('--samples',
                             type=int,
                             default=5000,
                             help='Number of samples to take the average')

  def add_hscan_options(self, scanz=20, hrange=5, distance=1):
    """
    Common arguments for performing x-y scan
    """
    self.add_xychip_options()
    self.add_readout_option()
    self.parser.add_argument('-z',
                             '--scanz',
                             type=float,
                             default=scanz,
                             help=('Height to perform horizontal scan [mm], '
                                   'using present coordinates if not specified'))
    self.parser.add_argument('-r',
                             '--range',
                             type=float,
                             default=hrange,
                             help=('Range to perform x-y scanning from central '
                                   'position [mm]'))
    self.parser.add_argument('-d',
                             '--distance',
                             type=float,
                             default=distance,
                             help='Horizontal sampling distance [mm]')

  def add_savefile_options(self, default_filename):
    """
    Common arguments for file saving
    """
    self.parser.add_argument('-f',
                             '--savefile',
                             type=str,
                             default=default_filename,
                             help=('Writing results to file. The filename can be'
                                   ' specified using <ARG> to indicate '
                                   'placeholders to be used by argument values. '
                                   'The placeholder <TIMESTAMP> can be used for '
                                   'a string representing the current time'))
    self.parser.add_argument('--wipefile',
                             action='store_true',
                             help='Wipe existing content in output file')

  def add_zscan_options(self, zlist=range(10, 51, 1)):
    """
    Common arguments for scaning values along the z axis
    """
    self.add_xychip_options()
    self.add_readout_option()
    self.parser.add_argument('-z',
                             '--zlist',
                             type=str,
                             nargs='+',
                             default=zlist,
                             help=('List of z coordinate to perform scanning. '
                                   'One can add a list of number by the notation'
                                   ' "[start_z end_z sepration]"'))

  def parse_readout_options(self, args):
    """
    Parsing the readout option
    """
    if not args.mode:
      args.mode = self.readout.mode
    if args.mode == self.readout.MODE_PICO:
      if args.channel < 0 or args.channel > 1:
        raise Exception('Channel for PICOSCOPE can only be 0 or 1')
      self.readout.set_mode(args.mode)
    elif args.mode == self.readout.MODE_ADC:
      if args.channel < 0 or args.channel > 3:
        raise Exception('Channel for ADC can only be 0--3')
      self.readout.set_mode(args.mode)

  def make_hscan_mesh(self, args):
    """
    Common argument for generating x-y scanning coordinate mesh
    """
    max_x = gcoder.GCoder.max_x()
    max_y = gcoder.GCoder.max_y()

    if(args.x - args.range < 0 or
       args.x + args.range > max_x or
       args.y - args.range < 0 or
       args.y + args.range > max_y):
      log.printwarn(('The arguments placed will put the gantry past its limits, '
                     'the command will used modified input parameters'))

    xmin = max([args.x - args.range, 0])
    xmax = min([args.x + args.range, max_x])
    ymin = max([args.y - args.range, 0])
    ymax = min([args.y + args.range, max_y])
    sep = max([args.distance, 0.1])
    xmesh, ymesh = np.meshgrid(np.linspace(xmin, xmax, (xmax - xmin) / sep + 1),
                               np.linspace(ymin, ymax, (ymax - ymin) / sep + 1))
    return [
        xmesh.reshape(1, np.prod(xmesh.shape))[0],
        ymesh.reshape(1, np.prod(ymesh.shape))[0]
    ]

  def parse_zscan_options(self, args):
    """
    Parsing the z scanning options
    """
    args.zlist = " ".join(args.zlist)
    braces = re.findall(r'\[(.*?)\]', args.zlist)
    args.zlist = re.sub(r'\[.*?\]', '', args.zlist)
    args.zlist = [float(z) for z in args.zlist.split()]
    for rstring in braces:
      r = [float(rarg) for rarg in rstring.split()]
      if len(r) < 2 or len(r) > 3:
        raise Exception(('Range must be in the format [start end (sep)] '
                         'sep is assumed to be 1 if not specified'))
      minz = min(r[:2])
      maxz = max(r[:2])
      sep = 1 if len(r) == 2 else r[2]
      args.zlist.extend(
          np.linspace(minz, maxz, (maxz - minz) / sep, endpoint=False))
    args.zlist = [x for x in args.zlist if x < gcoder.GCoder.max_z()]
    args.zlist.sort()  ## Returning sorted result

  def parse_xychip_options(self, args, add_visoffset=False, raw_coord=False):
    """
    Parsing the x-y-chip position arguments
    """
    ## Setting up alias for board
    board = self.board

    # If not directly specifying the chip id, assuming some calibration chip
    # with specified coordinate system. Exit immediately.
    if args.chipid == None:
      args.chipid = '-100'
      if not args.x: args.x = self.gcoder.opx
      if not args.y: args.y = self.gcoder.opy
      return

    ## Attempt to get a board specified chip position.
    if not args.chipid in board.chips():
      raise Exception('Chip id was not specified in board type')

    ## Raising exception when attempting to overide chip position with raw
    ## x-y values
    if args.x or args.y:
      raise Exception('You can either specify chip-id or x y, not both')

    # Early exit if raw coordinates requested
    if raw_coord:
      args.x, args.y = board.orig_coord[args.chipid]
      return

    # Determining current z value ( from argument first, otherwise guessing
    # from present gantry position )
    current_z = args.z if hasattr(args, 'z') else \
                 min(args.zlist) if hasattr(args, 'zlist') else \
                 self.gcoder.opz

    if add_visoffset:
      if any(self.board.vis_coord[args.chipid]):
        closest_z = self.find_closest_z(self.board.vis_coord[args.chipid],
                                        current_z)
        args.x = board.vis_coord[args.chipid][closest_z][0]
        args.y = board.vis_coord[args.chipid][closest_z][1]
      else:
        x_offset, y_offset = self.find_xyoffset(current_z)
        args.x = board.orig_coord[args.chipid][0] + x_offset
        args.y = board.orig_coord[args.chipid][1] + y_offset
    else:
      if any(board.lumi_coord[args.chipid]):
        closest_z = self.find_closest_z(self.board.lumi_coord[args.chipid],
                                        current_z)
        args.x = board.lumi_coord[args.chipid][closest_z][0]
        args.y = board.lumi_coord[args.chipid][closest_z][2]
      elif any(board.vis_coord[args.chipid]):
        x_offset, y_offset = self.find_xyoffset(current_z)
        closest_z = self.find_closest_z(self.board.vis_coord[args.chipid],
                                        current_z)
        args.x = board.vis_coord[args.chipid][closest_z][0] - x_offset
        args.y = board.vis_coord[args.chipid][closest_z][1] - y_offset
      else:
        args.x, args.y = board.orig_coord[args.chipid]

  @staticmethod
  def find_closest_z(my_map, current_z):
    return min(my_map.keys(), key=lambda x: abs(float(x) - float(current_z)))

  def find_xyoffset(self, currentz):
    """
    Finding x-y offset between the luminosity and visual alignment based the
    existing calibration
    """

    # If no calibration chip exists, just return a default value (from gantry
    # head design.)
    DEFAULT_XOFFSET = -40
    DEFAULT_YOFFSET = 0
    if not any(self.board.calibchips()):
      return DEFAULT_XOFFSET, DEFAULT_YOFFSET

    # Calculations will be based on the "first" calibration chip available
    # That has both lumi and visual alignment offsets
    for calibchip in self.board.calibchips():
      lumi_x = None
      lumi_y = None
      vis_x = None
      vis_y = None

      # Trying to get the luminosity alignment with closest z value
      if any(self.board.lumi_coord[calibchip]):
        closestz = self.find_closest_z(self.board.lumi_coord[calibchip],
                                       currentz)
        lumi_x = self.board.lumi_coord[calibchip][closestz][0]
        lumi_y = self.board.lumi_coord[calibchip][closestz][2]

      # Trying to get the visual alignment with closest z value
      if any(self.board.vis_coord[calibchip]):
        closestz = self.find_closest_z(self.board.vis_coord[calibchip],
                                       currentz)
        vis_x = self.board.vis_coord[calibchip][closestz][0]
        vis_y = self.board.vis_coord[calibchip][closestz][1]

      if lumi_x and lumi_y and vis_x and vis_y:
        return vis_x - lumi_x, vis_y - lumi_y

    # If no calibration chip has both calibration values
    # Just return the original calibration value.
    return DEFAULT_XOFFSET, DEFAULT_YOFFSET

  def parse_savefile(self, args):
    filename = args.savefile

    # Adding time stamp filenames
    timestring = datetime.datetime.now().strftime('%Y%m%d_%H00')
    filename = re.sub('<TIMESTAMP>', timestring, filename, flags=re.IGNORECASE)

    # Substituting tokens for argument values
    for action in self.parser._actions:
      for string in action.option_strings:
        string = string.strip('-')
        if not hasattr(args, string): continue
        val = ''
        try:
          val = action.type(getattr(args, string))
        except:
          pass
        substring = '{0}{1}'.format(string, val)
        substring = re.sub(r'\.', 'p', substring)
        filename = re.sub('\\<{0}\\>'.format(string),
                          substring,
                          filename,
                          flags=re.IGNORECASE)

    # Opening the file using the remote file handle
    args.savefile = self.sshfiler.remotefile(filename, args.wipefile)

  def close_savefile(self,args):
    """
    Close a save file with a standard message for the verbosity of run files.
    """
    if not hasattr(args, 'savefile'):
      return
    self.printmsg( "Saving results to file [{0}]".format(args.savefile.name) )
    args.savefile.flush()
    args.savefile.close()

  # Helper function for globbing
  @staticmethod
  def globcomp(text):
    globlist = glob.glob(text + "*")
    globlist = [file + '/' if os.path.isdir(file) else file for file in globlist]
    return globlist
