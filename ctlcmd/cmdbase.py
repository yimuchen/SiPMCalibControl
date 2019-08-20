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
import cmd
import sys
import os
import argparse
import readline
import glob
import traceback
import re


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
        self.onecmd(cmdline.strip())
    return

  def complete_runfile(self, text, line, start_index, end_index):
    return globcomp(text)


class controlcmd():
  """
  The control command is the base interface for defining a command in the
  terminal class, the instance do, callhelp and complete functions corresponds
  to the functions do_<cmd>, help_<cmd> and complete_<cmd> functions in the
  vallina python cmd class. Here we will be using the argparse class by default
  to call for the help and complete functions
  """

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
    try:
      args = self.parse(line)
    except Exception as err:
      self.printerr(str(err))
      return

    try:
      self.run(args)
    except Exception as err:
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

      self.printerr(str(err))
      return

    log.clear_update()
    return

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
        return globcomp(text)
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

  # Helper function for globbing
  @staticmethod
  def globcomp(text):
    globlist = glob.glob(text + "*")
    globlist = [file + '/' if os.path.isdir(file) else file for file in globlist]
    return globlist
