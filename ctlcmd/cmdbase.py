import cmod.gcoder as gcoder
import cmod.board as board
import cmod.logger as log
import cmod.trigger as trigger
import cmod.visual as visual
import cmod.readout as readout
import cmod.sshfiler as sshfiler
import cmod.pico as pico
import cmd
import sys
import os
import argparse
import readline
import glob


class controlterm(cmd.Cmd):
  """
  Control term is the class for parsing commands and passing the arguments
  to C functions for gantry and readout control.
  It also handles the command as classes to allow for easier interfacing
  """

  intro = """
    SiPM Calibration Gantry Control System
    Type help or ? to list commands.\n"""
  prompt = 'SiPMCalib> '

  def __init__(self, cmdlist):
    cmd.Cmd.__init__(self)

    self.sshfiler = sshfiler.SSHFiler()
    self.gcoder = gcoder.GCoder()
    self.board = board.Board()
    self.visual = visual.Visual()
    self.pico = pico.PicoUnit()
    self.readout = readout.readout(self)

    ## The following is PI specific! Wrapping up to allow for local testing
    # on laptop
    try:
      self.trigger = trigger.Trigger()
    except Exception as err:
      log.printerr(str(err))
      log.printwarn((
        'Error message emitted when setting up GPIO interface, '
        'trigger might not work as expected'))

    ## Creating command instances and attaching to associated functions
    for com in cmdlist:
      comname = com.__name__.lower()
      dofunc = "do_" + comname
      helpfunc = "help_" + comname
      compfunc = "complete_" + comname
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

    Executing commands listed in a file. This should be used for testing. And
    not used extensively.
    """
    if len(line.split()) != 1:
      log.printerr("Please only specify one file!")
      return

    if not os.path.isfile(line):
      log.printerr("Specified file could not be opened!")
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

    ## Reference to control objects for all commands
    self.sshfiler = cmdsession.sshfiler
    self.gcoder = cmdsession.gcoder
    self.readout = cmdsession.readout
    self.board = cmdsession.board
    self.visual = cmdsession.visual
    self.pico = cmdsession.pico
    if (hasattr(cmdsession, 'trigger')):  # Potentially missing (PI specific)
      self.trigger = cmdsession.trigger

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
    prevtext = textargs[-1] if len(textargs) else ""
    options  = [opt for x in self.parser._actions for opt in x.option_strings]

    def optwithtext():
      if text:
        return [x for x in options if x.startswith(text)]
      else:
        return options

    if prevtext in options:
      action = next( x for x in self.parser._actions
         if (prevtext in x.option_strings) )
      if type(action.type) == argparse.FileType:
        return globcomp(text)
      else:
        return ["input type: " + str(action.type), "Help: "+action.help]
    else:
      return optwithtext()

  ## Overloading for less verbose message printing
  def update(self, text):
    log.update(self.LOG, text)

  def printmsg(self, text):
    log.clear_update()
    log.printmsg(self.LOG, text)

  def printerr(self, text):
    log.clear_update()
    log.printerr(text)

  def printwarn(self, text):
    log.clear_update()
    log.printerr()

  def run(self, args):
    """
    Functions that require command specific definitions, should be overwritten in
    the decendent classes
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
      raise Exception("Cannot parse input")
    return arg


## Helper function for globbing
def globcomp(text):
  globlist =  glob.glob(text + "*")
  globlist = [ file + '/' if os.path.isdir(file) else file for file in globlist ]
  return globlist
