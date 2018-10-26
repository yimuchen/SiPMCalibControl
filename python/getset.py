import python.cmdbase as cmdbase
import python.gcoder as gcoder
import python.logger as logger
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
      self.cmd.board.set_boardtype( arg.boardtype.name )
    if arg.printerdev and arg.printerdev != self.cmd.gcoder.dev_path :
      self.cmd.gcoder.init_printer( arg.printerdev )

      logger.printmsg( self.cmd.gcoder.get_settings() )

class get(cmdbase.controlcmd):
  """
  Printing out the session parameters, and equipment settings.
  """
  def __init__(self):
    cmdbase.controlcmd.__init__(self)
    self.parser.add_argument('-boardtype',action='store_true')
    self.parser.add_argument('-opchip',action='store_true')
    self.parser.add_argument('-printerdev', action='store_true')
    self.parser.add_argument('-all',action='store_true')

  def run(self,arg):
    if arg.boardtype or arg.all :
      logger.update( "[BOARDTYPE] ", str(self.cmd.board.boardtype) )
    if arg.opchip    or arg.all :
      logger.update( "[OPCHIP ID] ", str(self.cmd.board.op_chip) )
    if arg.printerdev or arg.all:
      logger.update( "[PRINTER DEV] ", str(self.cmd.gcoder.dev_path) )


