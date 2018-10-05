import cmd
import sys
import os
import argparse
import readline
import glob


class controlterm( cmd.Cmd ):
  """
  Control term is the class for parsing commands and passing the arguments
  to C functions for gantry and readout control.
  It also handles the command as classes to allow for easier interfacing
  """

  intro = """
    SiPM Calibration Gantry Control System
    Type help or ? to list commands.\n"""
  prompt = 'SiPMCalib> '

  def __init__(self,cmdlist):
    cmd.Cmd.__init__(self)
    for com in cmdlist :
      comname = com.__name__.lower()
      dofunc = "do_" + comname
      helpfunc = "help_" + comname
      compfunc = "complete_" + comname
      self.__setattr__( comname, com() )
      self.__setattr__( dofunc, self.__getattribute__(comname).do )
      self.__setattr__( helpfunc, self.__getattribute__(comname).callhelp )
      self.__setattr__( compfunc, self.__getattribute__(comname).complete )

    # Removing hyphen and slash as completer delimiter, as it messes with
    # command auto completion
    readline.set_completer_delims(' \t\n`~!@#$%^&*()=+[{]}\\|;:\'",<>?')

  def postcmd(self,stop,line):
    print("") # Printing extra empty line for aesthetics

  def get_names(self):
    """
    Overriding the the original get_names command to allow for the dynamic
    introduced commands to be listed.
    """
    return dir(self)

  def do_exit(self,line):
    sys.exit(0)

  def help_exit(self):
    "Exit program current session"

  # running commands listed in the a file requires the onecmd() method. So it
  # cannot be declared using an external class.
  def do_runfile(self,line):
    """
    usage: runfile <file>

    Executing commands listed in a file. This should be used for testing. And
    not used extensively.
    """
    if len(line.split()) != 1 :
      print("Please only specify one file!")
      return

    if not os.path.isfile(line):
      print("Specified file could not be opened!")
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
  def __init__(self):
    """
    Initializer declares an argument parser class with the class name as the
    program name and the class doc string as the description string. This
    greatly reduces the verbosity of writing custom commands.
    """
    self.parser = argparse.ArgumentParser(
      prog= self.__class__.__name__.lower() ,
      description= self.__class__.__doc__,
      add_help=False
    )

  """
  Execution of the commands automatically handles the parsing in the parse
  method. Additional parsing is allowed by overloading the parse method in the
  children classes. The actual execution of the function is handled in the run
  method.
  """
  def do(self,line):
    try:
      args=self.parse(line)
    except Exception as err:
      print("[Error parsing command]")
      #print(err)
      return

    try:
      self.run(args)
    except Exception as err:
      print("[Error running command]")
      print(err)
      return

    return

  """
  Printing the help message via the ArgumentParse in built functions.
  """
  def callhelp(self):
    self.parser.print_help()

  """
  Auto completion of the functions. This function scans the options stored in
  the parse class and returns a string of things to return.
  """
  def complete(self, text, line, start_index, end_index):
    # text is the word on this cursor is on (excluding tail)
    # Line is the full input line string (including command)
    # start_index is the starting index of the word the cursor is at in the line
    # end_index is the position of the cursor in the line

    cmdname   = self.__class__.__name__.lower()
    #while line[start_index-1] == '-': start_index = start_index-1
    textargs   = line[len(cmdname):start_index].strip().split()
    prevtext   = textargs[-1] if len(textargs) else ""
    actions    = self.parser._actions
    optstrings = [action.option_strings[0] for action in actions]

    def optwithtext():
      if text:
        return [option for option in optstrings if option.startswith(text)]
      else:
        return optstrings

    if prevtext.startswith('-') :
      ## If the previous string was already an option
      testact = [action for action in actions
                if action.option_strings[0] == prevtext]
      if len(testact) != 1 :
        return []
      prevact = testact[0]

      if type(prevact.type) == argparse.FileType :
        return globcomp(text)
      else:
        return [str(prevact.type),"input type"]

    else:
      return optwithtext()


  #############################
  ## The following functions should be overloaded in the inherited classes

  ## Functions that require command specific definitions
  def run(self,args):
    pass

  # Default parsing arguments, overriding the system exits exception to that the
  # session doesn't end with the user inputs a bad command. Additional parsing
  # could be achieved by overloading this methods.
  def parse(self,line):
    try:
      arg = self.parser.parse_args(line.split())
    except SystemExit as err :
      raise Exception("")
    return arg



## Helper function for globbing
def globcomp(text):
  return glob.glob(text+"*")