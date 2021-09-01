"""
  cmdbase.py

  The core class for creating the command-line interface for the gantry control
  system. The base of the class is controlterm class derived from the python
  cmd.Cmd class. Rather than defining all commands under the various `do_<cmd>`
  methods within the Cmd class, we opt to split out the the commands into the
  various classes defined from our custom controlcmd and have python dynamically
  create commands based on the class name, which allows for very verbose commands
  while keeping the files more readable. The master Cmd class also spawns in the
  interface instances, and exposes this to all command such that commands can use
  which ever interface needed.

  Additional "meta command" classes will be provided to unify certain interface
  actions (like gantry motion), and provide common command line options and
  parsing methods.
"""
import cmod.gcoder as gcoder
import cmod.board as board
import cmod.logger as log
import cmod.gpio as gpio
import cmod.visual as visual
import cmod.sshfiler as sshfiler
import cmod.pico as pico
import cmod.drs as drs
import cmod.actionlist as actionlist
import cmod.sighandle as sig
import numpy as np
import cmd
import sys
import os
import argparse
import glob
import re
import datetime
import time
import traceback
import shlex
import select
import enum


class controlterm(cmd.Cmd):
  """
  The master Command-line parsing class. Which holds:

  - All instances of the interface classes.
  - All instances of the controlcmd classes that will be used to map functions

  Additional helper method will also be provided to help with common routines of
  across commands.
  """

  intro = """
    SiPM Calibration Gantry Control System
    Type help or ? to list commands.
    Type help <cmd> for the individual help messages of each commands
    """
  prompt = 'SiPMCalib> '
  last_status = None

  def __init__(self, cmdlist, **base_kwargs):
    """
    Constructing the command line instance from a list of classes that is
    requested. The `do_<cmd>`, `help_<cmd>`, and `complete_<cmd>` methods will be
    spawned in after the the command classes have been created, and the method
    will be mapped to the cmd.<do> methods of the spawned class.
    """
    cmd.Cmd.__init__(self, **base_kwargs)

    self.sshfiler = sshfiler.SSHFiler()
    self.gcoder = gcoder.GCoder.instance()
    self.board = board.Board()
    self.visual = visual.Visual()
    self.pico = pico.PicoUnit.instance()
    self.gpio = gpio.GPIO.instance()
    self.drs = drs.DRS.instance()
    self.action = actionlist.ActionList()
    self.sighandle = sig.SigHandle()
    self.sighandle.release()

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

    # Modifying readline default behavior:
    import readline
    # Removing hyphen and slash as completer delimiter, as it messes with
    # command auto completion
    readline.set_completer_delims(' \t\n`~!@#$%^&*()=+[{]}\\|;:\'",<>?')
    ## Setting the history file
    readline.set_history_length(1000)

    ## Additional members for command status logging
    self.last_cmd = ''  # string for containing the command that was last called
    self.last_cmd_status = None  # Execution status of the command
    self.last_cmd_start = None  # Start time of the last command
    self.last_cmd_stop = None  # End time of the last command
    self.opfile = ''

  def precmd(self, line):
    """
    Additional logging to be performed before the command has been run
    """
    self.last_cmd = line
    self.last_cmd_status = None
    self.last_cmd_start = datetime.datetime.now()
    self.last_cmd_stop = self.last_cmd_start
    # Duplicate to indicate command has not yet finished running.
    return line

  def postcmd(self, stop, line):
    """
    Printing extra empty line after command completion for clarity, also removing
    all return values to stop the command from exiting with the default return
    value
    """
    log.printmsg("")
    self.last_cmd_status = stop
    self.last_cmd_stop = datetime.datetime.now()
    if stop == controlcmd.TERMINATE_SESSION:
      return True

  def get_names(self):
    """
    Overriding the the original get_names command to allow for the dynamic
    introduced commands to be listed in the master help method.
    """
    return dir(self)

  def emptyline(self):
    """Don't do anything for empty lines"""
    pass

  @staticmethod
  def simplify_string(text):
    """
    Simplifying multiline text in python to a single line text in python, which
    also removes the additional whitespaces at the beginning of lines
    """
    return ' '.join(text.split())


class controlcmd(object):
  """
  The control command is the base interface for defining a command in the
  terminal class, the instance do, callhelp and complete functions corresponds to
  the functions do_<cmd>, help_<cmd> and complete_<cmd> functions in the vallina
  python cmd class. Here we will be using the argparse class by default to call
  for the help and complete functions.

  In addition, the class will also contain a `LOG` instance which is used to
  prettify the output of the printerr methods. This should be overridden in all
  subsequent classes.

  One big part of this class the the consistent construction of argument elements
  and the parsing of elements. This is how the creation and parsing of the
  arguments are performed:
  - Arguments will be added in the inverse order listed in the __mro__ method via
    the `add_args` method that meta-command classes and command classes should
    overload.
  - Arguments will be also be parsed in the order inversely listed in the __mro__
    method via the `parse` argument. Because of this, the input args object in
    the `parse` argument in inherited classes should simply assume that the
    `parse` of parent classes' has already been assumed, and should not attempt
    to call the parent class's parse method.
  """
  PARSE_ERROR = -1
  EXECUTE_ERROR = -2
  EXIT_SUCCESS = 0
  TERMINATE_SESSION = 1
  TERMINATE_CMD = 2

  LOG = "DUMMY"

  def __init__(self, cmdsession):
    """
    Initializer declares an argument parser class with the class name as the
    program name and the class doc string as the description string. This
    greatly reduces the verbosity of writing custom commands.
    Each command will have accession to the cmd session, and by extension,
    every interface object the could potentially be used.
    """
    self.parser = argparse.ArgumentParser(prog=self.__class__.__name__.lower(),
                                          description=self.__class__.__doc__,
                                          add_help=False)
    self.cmd = cmdsession  # Reference to the master object.

    ## Reference to control objects for all commands
    self.sshfiler = cmdsession.sshfiler
    self.gcoder = cmdsession.gcoder
    self.board = cmdsession.board
    self.visual = cmdsession.visual
    self.pico = cmdsession.pico
    self.drs = cmdsession.drs
    self.gpio = cmdsession.gpio
    self.action = cmdsession.action
    self.sighandle = cmdsession.sighandle

    self.__run_mro_method('add_args')

  def __run_mro_method(self, method, args=None):
    """
    Running over the the list of parent classes in inverted __mro__ order,
    extracting which everclass has an explicitly defined method, and running the
    method with the provided arguments.
    """
    for t in reversed(type(self).__mro__):
      if not hasattr(t, method): continue
      if method not in t.__dict__: continue  # Needs to be explicitly defined
      if args == None:
        getattr(t, method)(self)
      else:
        args = getattr(t, method)(self, args)
    return args

  def add_args(self):
    """
    Method to be overridden for adding additional argument to the containing
    `parser` object.
    """
    pass

  def parse_line(self, line):
    """
    Parsing the arguments from the input line using the argparse. argument
    parsing method. As this is a very standard method for parsing objects, this
    part should not be over written. Additional parsing the the resulting
    arguments (complicated parsing of default values... etc) should be handled by
    the `parse` method.
    """
    try:
      args = self.parser.parse_args(shlex.split(line))
      return self.__run_mro_method('parse', args)
    except SystemExit as err:
      self.printerr(str(err))
      raise Exception('Cannot parse input')

  def parse(self, args):
    """
    Method that should be overwritten for additional argument parsing.
    """
    return args

  def run(self, args):
    """
    Functions that require command specific definitions, should be overwritten in
    the descendent classes
    """
    pass

  def post_run(self):
    """
    Routines to run after the run argument. is called.
    """
    log.clear_update()

  def do(self, line):
    """
    Execution of the commands is now split up into following steps:

    - Parsing the command line using the standard argparse library
    - Results of the parsing will passed the run method (to be overloaded)
    - An additional return value will be evaluate execution status.

    Additional parsing is allowed by overloading the parse method in the children
    classes. The actual execution of the function is handled in the run method.
    The global signal handler is also triggered at the start of the command, so
    that signals like CTL+C will have additional handling in iterative commands
    so that data collection isn't completely lost.
    """
    try:
      args = self.parse_line(line)
    except Exception as err:
      self.print_tracestack(err)
      return controlcmd.PARSE_ERROR

    return_value = controlcmd.EXIT_SUCCESS

    self.sighandle.reset()
    try:
      x = self.run(args)
      if x == controlcmd.TERMINATE_SESSION:
        return_value = x
    except InterruptedError as err:
      self.print_tracestack(err)
      return_value = controlcmd.TERMINATE_CMD
    except Exception as err:
      self.print_tracestack(err)
      return_value = controlcmd.EXECUTE_ERROR
    self.sighandle.release()

    try:
      self.__run_mro_method('post_run')
    except Exception as err:
      self.print_tracestack(err)
      return_value = controlcmd.EXECUTE_ERROR

    return return_value

  def callhelp(self):
    """
    Printing the help message via the ArgumentParse in built functions.
    """
    self.parser.print_help(self.cmd.stdout)

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

  """

    MESSAGING HELPER FUNCTIONS

  """

  def update(self, text):
    """Printing an update message using the static 'LOG' variable."""
    log.update(self.LOG, controlterm.simplify_string(text))

  def printmsg(self, text):
    """Printing a newline message using the static LOG' variable."""
    log.clear_update()
    log.printmsg(self.LOG, controlterm.simplify_string(text))

  def printerr(self, text):
    """Printing a error message with a standard red "ERROR" header."""
    log.clear_update()
    log.printerr(controlterm.simplify_string(text))

  def printwarn(self, text):
    """Printing a warning message with a standard yellow "WARNING" header."""
    log.clear_update()
    log.printwarn(controlterm.simplify_string(text))

  def print_tracestack(self, err):
    """
    Helper function for a prettier trackstack printout. The file and error lines
    are highlighted in read and yellow, and compressed down to a single line to
    make the traceback more compact while still being readable and useful for
    debugging.
    """
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

    # Printing the original error message
    self.printerr(str(err))

  def update_progress(self,
                      progress=None,
                      coordinates=None,
                      temperature=None,
                      display_data={}):
    """
    Function for displaying a progress update for the data. The standard sequence
    would be (given the input variables)
    - progress: A two long iterable construct, indicating the number of
      iterations ran and the expected number of total iteration. A percent value
      will also be displayed for at a glance monitoring.
    - coordinates: If set to true, add columns for gantry coordinates
    - temperature: If set to true, add columns for temperature sensors
    - display_data: the key is used to display the data, and the values should be
      a list of floats corresponding to the data to be displayed. Data will be
      truncated to the 2nd decimal place, so scale data accordingly.
    """
    message_string = ''

    def append_msg(x, msg):
      if x != '':
        return x + ' | ' + msg
      else:
        return msg

    # Making the various progress string.
    if progress:
      done = progress[0]
      total = progress[1]
      width = len(str(total))
      per = done / total * 100.0
      pstr = '[{done:{width}d}/{total:{width}d}][{per:5.1f}%]'.format(
          done=done, total=total, width=width, per=per)
      message_string = append_msg(message_string, pstr)

    if coordinates:
      cstr = 'Gantry@({x:5.1f},{y:5.1f},{z:5.1f})'.format(x=self.gcoder.opx,
                                                          y=self.gcoder.opy,
                                                          z=self.gcoder.opz)
      message_string = append_msg(message_string, cstr)

    if temperature:
      tstr = 'bias:{bias:5.1f}mV pulser:{pt:.2f}C SiPM:{st:.2f}C'.format(
          bias=self.gpio.adc_read(2),
          pt=self.gpio.ntc_read(0),
          st=self.gpio.rtd_read(1))
      message_string = append_msg(message_string, tstr)

    for key, vals in display_data.items():
      list_str = ['{0:.2f}'.format(x) for x in vals]
      list_str = ' '.join(list_str)
      msg = '{key}: [{list}]'.format(key=key, list=list_str)
      message_string = append_msg(message_string, msg)

    self.update(message_string)

  def check_handle(self, args):
    """
    Checking the status of the signal handle, closing files and raising an
    exception if a termination signal was ever set by the user.
    """
    if self.sighandle.terminate:
      self.printmsg('TERMINATION SIGNAL RECIEVED, EXITING COMMAND')
      raise InterruptedError('TERMINATION SIGNAL')

  def move_gantry(self, x, y, z, verbose):
    """
    Wrapper for gantry motion command, suppresses the exception raised for in
    case that the gantry isn't connected so that one can test with pre-defined
    models. Notice that the stepper motor disable will not be handled here, as
    it should only be disabled for readout.
    """
    try:
      # Try to move the gantry. Even if it fails there will be fail safes
      # in other classes
      self.gcoder.moveto(x, y, z, verbose)
      while self.gcoder.in_motion(x, y, z):
        time.sleep(0.01)  ## Updating position in 0.01 second increments
    except Exception as e:
      # Setting internal coordinates to the designated position anyway.
      self.gcoder.opx = x
      self.gcoder.opy = y
      self.gcoder.opz = z
      self.gcoder.cx = x
      self.gcoder.cy = y
      self.gcoder.cz = z
      pass

  def prompt_yn(self, question, default='no'):
    """
    Ask a yes/no question and prompt a question to the user and return their
    answer.

    'question' is a string that is presented to the user. 'default' is the
    presumed answer if the user just hits <Enter>. It must be 'yes' (the
    default), 'no' or None (meaning an answer is required of the user).

    The 'answer' return value is True for 'yes' or False for 'no'.
    """
    valid = {'yes': True, 'ye': True, 'y': True, 'no': False, 'n': False}
    try:
      if default is None:
        prompt_str = ' [y/n] '
      elif valid[default.lower()]:
        prompt_str = ' [Y/n] '
      else:
        prompt_str = ' [y/N] '
    except KeyError:
      raise ValueError('invalid default answer: {0}'.format(default))

    # Special case of wrapped input
    if (self.cmd.use_rawinput == False or  #
        self.cmd.stdin != sys.stdin or self.cmd.stdout != sys.stdout):
      log.printmsg('wrapped I/O detected, assuming default answer:', default)
      return valid[default]

    while True:
      log.printmsg(controlterm.simplify_string(question + prompt_str))
      if self.cmd.use_rawinput:
        choice = input()
      else:
        choice = self.cmd.stdin.readline().strip().lower()
      if default is not None and choice == '':
        return valid[default]
      elif choice in valid:
        return valid[choice]
      else:
        log.printerr(
            'Please respond with \'yes\' or \'no\' (or \'y\' or \'n\').\n')

  # Helper function for globbing
  @staticmethod
  def globcomp(text):
    globlist = glob.glob(text + "*")
    globlist = [file + '/' if os.path.isdir(file) else file for file in globlist]
    return globlist


class savefilecmd(controlcmd):
  """
  Command with the need to save a file. A standard method is provided adding the
  savefile options to the argparse instance, as well as additional parsing and
  handling of the method. All function that wish to have their default save
  location overridden should simple change the DEFAULT_SAVEFILE static variable.
  """
  DEFAULT_SAVEFILE = 'SAVEFILE_<TIMESTAMP>'

  def __init__(self, cmd):
    controlcmd.__init__(self, cmd)

  def add_args(self):
    group = self.parser.add_argument_group(
        "file saving options", """
    Options for changing the save file format. Specialized data formats for
    saving full waveforms, data is typically stored in the standard formats of:

    "time detid x y z pwm sipm_temp pulser_temp data1 data2..."

    Where datax is specificed in the command.
    """)
    group.add_argument('-f',
                       '--savefile',
                       type=str,
                       default=self.DEFAULT_SAVEFILE,
                       help="""
                       Writing results to file. The filename can be specified
                       using <ARG> to indicate placeholders to be used by
                       argument values. Additional place holders that can be
                       added include:
                       - <TIMESTAMP> can be used for a string representing the
                         current time.
                       - <BOARDID> can be used for board id string
                       - <BOARDTYPE> can be used for the board type string (like
                         T3, TBMOCK...etc).\n default=%(default)s""")
    group.add_argument('--wipefile',
                       action='store_true',
                       help='Wipe existing content in output file')

  def parse(self, args):
    """
    Additional parsing for the filename argument. Here we will be replacing the
    args.savefile argument with file descriptor that can be directly used by the
    children classes for string writing. Additional parsing is performed on the
    filename in accordance with what ever is placed in the angle braces.
    """
    filename = args.savefile

    # Adding time stamp filenames
    timestring = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = re.sub('<TIMESTAMP>', timestring, filename, flags=re.IGNORECASE)

    # Adding boardid to the settings
    filename = re.sub('<BOARDID>',
                      str(self.board.boardid),
                      filename,
                      flags=re.IGNORECASE)
    # Adding boardtype to the settings
    filename = re.sub('<BOARDTYPE>',
                      str(self.board.boardtype),
                      filename,
                      flags=re.IGNORECASE)

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

    # Opening the file using the remote file handle as an internal method to help
    # reduce verbosity.
    self.savefile = self.sshfiler.remotefile(filename, args.wipefile)
    return args

  def opensavefile(self, filename, wipefile):
    """
    Function for opening the save file. Here we also add a flag in the parent cmd
    session, so all subsystems can see which file is currently being written to.
    """
    mode = 'w' if wipefile else 'a'
    f = open(filename, mode)
    self.cmd.opfile = filename
    return f

  def post_run(self):
    """
    Close a save file with a standard message for the verbosity of run files.
    """
    self.printmsg(f"Saving results to file [{self.savefile.name}]")
    self.savefile.flush()
    self.savefile.close()
    self.cmd.opfile = ''

  def write_standard_line(self, data, det_id=-100, time=0.0):
    """
    This will be the standard format of saving data in space separated columns:
    - Timestamp
    - detID
    - gantry x, y, z
    - Voltage readouts: LED bias, LED temp (C) sipm temp (C) readouts
    - The readout data: an arbitrarily long iterable container of floats.
    """
    tokens = []
    tokens.append(f'{time:.2f}')
    tokens.append(f'{det_id}')
    tokens.extend([
        f'{self.gcoder.opx:.1f}',  #
        f'{self.gcoder.opy:.1f}',  #
        f'{self.gcoder.opz:.1f}'
    ])
    tokens.extend([
        f'{self.gpio.adc_read(2):.2f}',  #
        f'{self.gpio.ntc_read(0):.3f}',  #
        f'{self.gpio.rtd_read(1):.3f}'  #
    ])
    tokens.extend([f'{x:.2f}' for x in data])
    self.savefile.write(' '.join(tokens) + '\n')
    self.savefile.flush()


class singlexycmd(controlcmd):
  """
  Commands that require the motion around a single x-y position. This class will
  also provide the static variable to act as the flag for whether the target
  position should add the visual offset position or not (say for visual alignment
  and lumi-alignment, we want to keep the command similar for align at detector
  1, while working at different physical coordinates.) The default offset for
  when there no valid calibration data is available is provided should be based
  on the gantry head design.
  """
  VISUAL_OFFSET = False
  DEFAULT_XOFFSET = -35
  DEFAULT_YOFFSET = 0

  def __init__(self, cmd):
    controlcmd.__init__(self, cmd)

  def add_args(self):
    group = self.parser.add_argument_group(
        "horizontal position", """
        Options for specifiying the operation postion in the x-y coordinates.
    """)
    group.add_argument('-x',
                       type=float,
                       help="""
                       Specifying the x coordinate explicitly [mm]. If none is
                       given the current gantry position will be used instead""")
    group.add_argument('-y',
                       type=float,
                       help="""
                       Specifying the y coordinate explicitly [mm]. If none is
                       given the current gantry' position will be used.""")
    group.add_argument('-c',
                       '--detid',
                       type=str,
                       help="""
                       Specify x-y coordinates via det id, input negative value
                       to indicate that the det is a calibration one (so you can
                       still specify coordinates with it)""")

  def parse(self, args):
    """
    Additional Parsing the x-y position arguments. If the detector is not
    specified, then we are using the directly using the provided x/y coordinates
    or the override with the current position.

    If the detector is specified: We check if the detector exists in the current
    detector list. If not an exception is raised. If yes then we attempt to look
    up the x/y coordinates according to the target z position. The target z
    position is defined as follow:
    - If the args has a single z argument, then that is used.
    - If the args has a list of z arguments, then the minimal is used.
    - If neither is present, then the current z position is used.

    If the visual offset flag is True, then the look up sequence will be:
    - Direct visual calibrated coordinates.
    - Lumi cooridnates with visual offset added
    - Original coorindates with visual offset added
    If the visul offset flag is set to false, then the look up sequence will be:
    - Lumi-calibrated coordinates.
    - Visual calibrated cooridnates with visual offset subtracted.
    - The original cooridnates.

    """
    if args.detid == None:  # Early exits if the detector ID is not used
      args.detid = -100
      if not args.x: args.x = self.gcoder.opx
      if not args.y: args.y = self.gcoder.opy
      return args

    if args.x or args.y:
      raise Exception('You can either specify det-id or x y, not both')

    if not args.detid in self.board.dets():
      raise Exception('Det id was not specified in board type')

    current_z = args.z if hasattr(args, 'z') and args.z else \
                 min(args.zlist) if hasattr(args, 'zlist') else \
                 self.gcoder.opz

    det = self.board.get_det(args.detid)

    if self.VISUAL_OFFSET:
      if any(det.vis_coord):
        closest_z = self.find_closest_z(det.vis_coord, current_z)
        args.x = det.vis_coord[closest_z][0]
        args.y = det.vis_coord[closest_z][1]
      elif any(det.lumi_coord):
        closest_z = self.find_closest_z(det.lumi_coord, current_z)
        x_offset, y_offset = self.find_xyoffset(current_z)
        args.x = det.lumi_coord[closest_z][0] + x_offset
        args.y = det.lumi_coord[closest_z][2] + y_offset
      else:
        x_offset, y_offset = self.find_xyoffset(current_z)
        args.x = det.orig_coord[0] + x_offset
        args.y = det.orig_coord[1] + y_offset
    else:
      if any(det.lumi_coord):
        closest_z = self.find_closest_z(det.lumi_coord, current_z)
        args.x = det.lumi_coord[closest_z][0]
        args.y = det.lumi_coord[closest_z][2]
      elif any(det.vis_coord):
        x_offset, y_offset = self.find_xyoffset(current_z)
        closest_z = self.find_closest_z(det.vis_coord, current_z)
        args.x = det.vis_coord[closest_z][0] - x_offset
        args.y = det.vis_coord[closest_z][1] - y_offset
      else:
        args.x, args.y = det.orig_coord

    return args

  def find_xyoffset(self, currentz):
    """
    Finding x-y offset between the luminosity and visual alignment based the
    existing calibration. This function will loop over all calibration detectors,
    and finding if there are any detector that has both a lumi-calibrated
    coordinates, and visual-calibrated coordinates, and create the offset based
    on the two measurement. If none are found, a default value will be used.
    """
    if not any(self.board.calib_dets()):
      return self.DEFAULT_XOFFSET, self.DEFAULT_YOFFSET

    for detid in self.board.calib_dets():
      lumi_x = None
      lumi_y = None
      vis_x = None
      vis_y = None
      det = self.board.get_det(detid)

      if any(det.lumi_coord):
        closestz = self.find_closest_z(det.lumi_coord, currentz)
        lumi_x = det.lumi_coord[closestz][0]
        lumi_y = det.lumi_coord[closestz][2]

      if any(det.vis_coord):
        closestz = self.find_closest_z(det.vis_coord, currentz)
        vis_x = det.vis_coord[closestz][0]
        vis_y = det.vis_coord[closestz][1]

      if lumi_x and lumi_y and vis_x and vis_y:
        return vis_x - lumi_x, vis_y - lumi_y

    return self.DEFAULT_XOFFSET, self.DEFAULT_YOFFSET

  @staticmethod
  def find_closest_z(my_map, current_z):
    return min(my_map.keys(), key=lambda x: abs(float(x) - float(current_z)))


class hscancmd(singlexycmd):
  """
  Commands that expand the operations around a (x,y) point to a small grid for
  alignment purposes. This classes uses the static variables to designate the
  grid range and mesh finess.
  """
  HSCAN_ZVALUE = 20
  HSCAN_RANGE = 5
  HSCAN_SEPARATION = 1

  def __init__(self, cmd):
    controlcmd.__init__(self, cmd)

  def add_args(self):
    group = self.parser.add_argument_group("options for setting up x-y grid")
    group.add_argument('-z',
                       '--scanz',
                       type=float,
                       default=self.HSCAN_ZVALUE,
                       help="""
                       Height to perform horizontal scan [mm] (default:
                       %(default)f[mm]).""")
    group.add_argument('-r',
                       '--range',
                       type=float,
                       default=self.HSCAN_RANGE,
                       help="""
                       Range to perform x-y scanning from central position [mm]
                       (default=%(default)f)""")
    group.add_argument('-d',
                       '--distance',
                       type=float,
                       default=self.HSCAN_SEPARATION,
                       help="""
                       Horizontal sampling distance [mm]
                       (default=%(default)f)""")

  def parse(self, args):
    """
    After parsing the arguments, the args.x and arg.y arguments will be expanded
    out into the list of x,y coordinates to be looped overs. In case the
    operation requests that the grid cooridnates be larger than the physical
    range, the range will be reduced to avoid gantry damage.
    """
    max_x = gcoder.GCoder.max_x()
    max_y = gcoder.GCoder.max_y()

    if (args.x - args.range < 0 or args.x + args.range > max_x
        or args.y - args.range < 0 or args.y + args.range > max_y):
      log.printwarn("""
        The arguments placed will put the gantry past its limits, the command
        will used modified input parameters""")

    xmin = max([args.x - args.range, 0])
    xmax = min([args.x + args.range, max_x])
    ymin = max([args.y - args.range, 0])
    ymax = min([args.y + args.range, max_y])
    sep = max([args.distance, 0.1])
    numx = int((xmax - xmin) / sep + 1)
    numy = int((ymax - ymin) / sep + 1)
    xmesh, ymesh = np.meshgrid(np.linspace(xmin, xmax, numx),
                               np.linspace(ymin, ymax, numy))

    args.x = xmesh.reshape(1, np.prod(xmesh.shape))[0]
    args.y = ymesh.reshape(1, np.prod(ymesh.shape))[0]
    return args


class zscancmd(controlcmd):
  """
  Commands that will scan over a range of z positions. As string parsing is used
  for abbreviate lists, the default zscan values should be provided using syntax
  corrected string rather a list of numbers.
  """
  ZSCAN_ZLIST = "[10 51 1]"

  def __init__(self, cmd):
    controlcmd.__init__(self, cmd)

  def add_args(self):
    group = self.parser.add_argument_group("options for scanning in z")
    group.add_argument('-z',
                       '--zlist',
                       type=str,
                       nargs='+',
                       default=self.ZSCAN_ZLIST,
                       help="""
                       List of z coordinate to perform scanning. One can add a
                       list of number by the notation "[start_z end_z sepration]"
                       """)

  def parse(self, args):
    """
    Regular expression is used to find the sets of numbers in square braces, the
    numbers in the square braces is then used to expand out into a list of
    floating points similar to the range command.
    """
    args.zlist = " ".join(args.zlist)
    braces = re.findall(r'\[(.*?)\]', args.zlist)
    args.zlist = re.sub(r'\[.*?\]', '', args.zlist)
    args.zlist = [float(z) for z in args.zlist.split()]
    for rstring in braces:
      r = [float(rarg) for rarg in rstring.split()]
      if len(r) < 2 or len(r) > 3:
        raise Exception("""
              Range must be in the format [start end (sep)]. sep is assumed to be
              1 if not specified""")
      startz = float(r[0])
      stopz = float(r[1])
      sep = float(1 if len(r) == 2 else r[2])
      args.zlist.extend(
          np.linspace(startz,
                      stopz,
                      int(np.rint((stopz - startz) / sep)),
                      endpoint=False))

    # Rounding to closest 0.1
    args.zlist = np.around(args.zlist, decimals=1)

    # Additional filtering
    args.zlist = [x for x in args.zlist if x < gcoder.GCoder.max_z()]

    ## Returning sorted results, STL or LTS depending on the first two entries
    if len(args.zlist) > 1:
      if args.zlist[0] > args.zlist[1]:
        args.zlist.sort(reverse=True)  ## Returning sorted result
      else:
        args.zlist.sort()  ## Returning sorted result

    return args


class readoutcmd(controlcmd):
  """
  Commands that should have single readout models. This typically assumes that
  the readout device (ADC/picoscope/drs4 or otherwise) has been properly set up
  with the correct range and settings, and this class will provide the new
  "self.readout" method to subsequent commands such that the the return can be a
  singular number representing the readout value of triggers.
  """
  class Mode(enum.IntEnum):
    MODE_PICO = 1
    MODE_ADC = 2
    MODE_DRS = 3
    MODE_NONE = -1

  def __init__(self, cmd):
    from cmod.readoutmodel import SiPMModel, DiodeModel
    controlcmd.__init__(self, cmd)
    self.sipm = SiPMModel()
    self.diode = DiodeModel()

  def add_args(self):
    group = self.parser.add_argument_group(
        "Readout", """
    Arguments for changing the behaviour of readout without directly interacting
    with the reaout interfaces.
    """)
    group.add_argument('--mode',
                       type=int,
                       choices=[e.value for e in readoutcmd.Mode],
                       help="""
                       Readout method to be used: 1:picoscope, 2:ADC, 3:DRS4,
                      -1:Predefined model (simulated)""")
    group.add_argument('--channel',
                       type=int,
                       default=None,
                       help='Input channel to use')
    group.add_argument('--samples',
                       type=int,
                       default=5000,
                       help="""
                       Number of readout samples to take the average for
                       luminosity measurement (default=%(default)d)""")
    group.add_argument('--intstart',
                       type=int,
                       default=-1,
                       help="""
                       Time slice to start integration for scope-like readouts
                       (DRS4/Picoscope). Leave negative to intergrate over full
                       range""")
    group.add_argument('--intstop',
                       type=int,
                       default=-1,
                       help="""
                       Time slice to stop integration for scope-like readouts
                       (DRS4/Picoscope). Leave negative to intergrate over full
                       range""")
    group.add_argument('--pedstart',
                       type=int,
                       default=-1,
                       help="""
                       Time slice to start integration to obtain value for
                       pedestal subtraction for scope-like readouts
                       (DRS4/Picoscope). Leave negative to ignore pedestal
                       subtraction""")
    group.add_argument('--pedstop',
                       type=int,
                       default=-1,
                       help="""
                       Time slice to start integration to obtain value for
                       pedestal subtraction for scope-like readouts
                       (DRS4/Picoscope). Leave negative to ignore pedestal
                       subtraction""")

  def parse(self, args):
    """
    Parsing the readout option. Basing the "default" arguments on additional
    inputs that may exist in the command input:
    - If the channel is not specified, then the channel will be assumed to be the
      channel associated with the detector ID (if applicable). Otherwise the
      channel defaults to 0.
    - If the readout mode is not specified, then the mode will be pulled from the
      board information if applicable. Otherwise, the last-used mode will be
      used.
    - Here we will also be double checking that the channel makes sense for the
      read-out mode. An exception will be raised if the readout mode is not
      sensible.
    """

    ## Defaulting to the det id if it isn't specified exists
    if args.channel is None:
      if hasattr(args, 'detid') and str(args.detid) in self.board.dets():
        args.channel = self.board.get_det(str(args.detid)).channel
      else:
        args.channel = 0

    ## Resetting mode to current mode if it doesn't already exists
    if not args.mode:
      if hasattr(args, 'detid') and str(args.detid) in self.board.dets():
        args.mode = self.board.get_det(str(args.detid)).mode
      else:
        raise Exception("Readout mode needs to be specified")

    ## Double checking the readout channel is sensible
    if args.mode == readoutcmd.Mode.MODE_PICO:
      if int(args.channel) < 0 or int(args.channel) > 1:
        raise Exception(
            f'Channel for PICOSCOPE can only be 0 or 1 (got {args.channel})')
    elif args.mode == readoutcmd.Mode.MODE_ADC:
      if int(args.channel) < 0 or int(args.channel) > 3:
        raise Exception(f'Channel for ADC can only be 0--3 (got {args.channel})')
    elif args.mode == readoutcmd.Mode.MODE_DRS:
      if int(args.channel) < 0 or int(args.channel) > 3:
        raise Exception(
            f'Channel for DRS4 can only be 0--4 (got {args.channel})')

    ## Checking the integration settings
    if args.mode == readoutcmd.Mode.MODE_PICO:
      pass
    elif args.mode == readoutcmd.Mode.MODE_DRS:
      pass
    else:
      if (args.intstart > 0 or args.intstop or args.pedstart > 0
          or args.pedstop > 0):
        self.printwarn("""
          Integration is not supported for this readout mode, integration
          settings will be ignored.
        """)

    return args

  def readout(self, args, average=True):
    """
    Abstracting the readout method for child classes, the input should be the
    parsed arguments along with a flag of whether the return should be some
    averaged value with STD or some the full list.
    """
    readout_list = []
    try:  # Stopping the stepper motors for cleaner readout
      self.gcoder.disablestepper(False, False, True)
    except:  # In case the gcode interface is not available, do nothing
      pass

    if args.mode == readoutcmd.Mode.MODE_PICO:
      readout_list = self.read_pico(args)
    elif args.mode == readoutcmd.Mode.MODE_ADC:
      readout_list = self.read_adc(args)
    elif args.mode == readoutcmd.Mode.MODE_DRS:
      readout_list = self.read_drs(args)
    else:
      readout_list = self.read_model(args)

    try:  # Re-enable the stepper motors
      self.gcoder.enablestepper(True, True, True)
    except:  # In the case that the gcode interface isn't availabe, do nothing.
      pass

    if average:
      return np.mean(readout_list), np.std(readout_list)
    else:
      return readout_list

  def read_adc(self, args):
    """
    Getting the averaged readout from the ADC. Here we provide a random sleep
    between adc_read call to avoid any aliasing with either the readout rate or
    the slow varying fluctuations in our DC systems.
    """
    val = []
    for _ in range(args.samples):
      val.append(self.gpio.adc_read(args.channel))
      ## Sleeping for random time in ADC to avoid 60Hz aliasing
      time.sleep(1 / 200 * np.random.random())
    return val

  def read_pico(self, args):
    """
    Averaged readout of the picoscope. Here we always set the blocksize to be
    1000 captures. This function will continuously fire the trigger system until
    a single rapidblock has been completed.
    """
    Nblock = 1000
    val = []
    while len(val) < args.samples:
      self.pico.setblocknums(Nblock, self.pico.postsamples, self.pico.presamples)
      self.pico.startrapidblocks()
      while not self.pico.isready():
        self._fire_trigger()
      self.pico.flushbuffer()
      val.extend(
          self.pico.waveformsum(args.channel, x, args.intstart, args.intstop,
                                args.pedstart, args.pedstop)
          for x in range(Nblock))
    return val

  def read_drs(self, args):
    """
    Average the readout results from the DRS4. Here we will contiously fire the
    trigger until collections have been completed.
    """
    val = []
    for _ in range(args.samples):
      self.drs.startcollect()
      while not self.drs.is_ready():
        self._fire_trigger()
      # Decent settings for drs delay 550 and 2.0 GHz sample rate.
      # Try to change programatically.
      val.append(
          self.drs.waveformsum(args.channel, args.intstart, args.intstop,
                               args.pedstart, args.pedstop))

    return val

  def _fire_trigger(self, n=10, wait=100):
    """
    Helper function for firing trigger for the scope-like readouts.
    """
    try:  # For standalone runs with external trigger
      self.gpio.pulse(n, wait)
    except:
      pass

  def read_model(self, channel, samples):
    """
    Generating a fake readout from a predefined model. THe location is extracted
    from the current gantry position
    """
    x = self.gcoder.opx
    y = self.gcoder.opy
    z = self.gcoder.opz

    det_x = self.board.det_map[str(channel)].orig_coord[0]
    det_y = self.board.det_map[str(channel)].orig_coord[1]

    r0 = ((x - det_x)**2 + (y - det_y)**2)**0.5
    pwm = self.gpio.pwm_duty(0)

    if channel >= 0 or channel % 2 == 0:
      ## This is a typical readout, expect a SiPM output,
      return self.sipm.read_model(r0, z, pwm, samples)
    else:
      ## This is a linear photo diode readout
      return self.diode.read_model(r0, z, pwm, samples)
