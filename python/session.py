import python.cmdbase as cmdbase
import python.gcodestream as gcode
import os.path
import json
import argparse

class Session(object):
  """
  All public class keeping track of current calibration session's information
  (Board type, on-memory data-storage... etc), all setting will be done
  externally, only defining the member objects for further reference.
  """
  def __init__(self):
    self.boardtype = None
    self.chipcoord = []
    self.opchip    = None
    self.printerdev = None

  def set_boardtype(self,arg):
    self.boardtype = arg
    self.set_chipposition()
    self.opchip = None

  def set_chipposition(self):
    if not self.boardtype:
      raise Exception("""
        No board type is defined! Make sure to set the board type
        during the program start up or via the 'set' command
        """)

    self.chipcoord = json.load(self.boardtype)

    if len(self.chipcoord ) != 64 :
      print("""
      Warning! This board config doesn't contain 64 chips, the setting maybe incomplete or for testing only.
      """)

  def get_chipposition(self,id):
    if not self.chipcoord:
      return
    if str(id) not in self.chipcoord:
      return
    return self.chipcoord[str(id)]


"""
Global session object for every command to modify
"""
calibsession = Session()


import argparse

class set(cmdbase.controlcmd):
  """
  Setting session parameters
  """
  def __init__(self):
    cmdbase.controlcmd.__init__(self)
    self.parser.add_argument(
      '-boardtype', type=argparse.FileType(mode='r'),
      help='Setting board type via a configuration json file that lists CHIP_ID with x-y- coordinates.')
    self.parser.add_argument(
      '-printerdev', type=str,
      help='Device path for the 3d printer. Should be something like /dev/tty<SOMETHING>.'
    )

  def run(self,arg):
    if arg.boardtype:
      calibsession.set_boardtype( arg.boardtype )
    if arg.printerdev and arg.printerdev != calibsession.printerdev:
      calibsession.printerdev = arg.printerdev
      gcode.init_printer( arg.printerdev )

      cfgstr = "MINTEMP"
      gcode.pass_gcode("M503\n")
      while "MINTEMP" in cfgstr :
        cfgstr = gcode.get_printer_out()
      print( cfgstr )



class get(cmdbase.controlcmd):
  """
  Printing out the session parameters, and equipment settings.
  """
  def __init__(self):
    cmdbase.controlcmd.__init__(self)
    self.parser.add_argument('-boardtype',action='store_true')
    self.parser.add_argument('-opchip',action='store_true')
    self.parser.add_argument('-all',action='store_true')

  def run(self,arg):
    if arg.boardtype or arg.all :
      print("[BOARDTYPE] ", calibsession.boardtype.name )
    if arg.opchip    or arg.all :
      print("[OPCHIP ID] ", calibsession.opchip)
    if arg.printerdev or arg.all:
      print("[PRINTER DEV] ", calibsession.printerdev)


