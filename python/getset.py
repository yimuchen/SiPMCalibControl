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
      help='Device path for the 3d printer. Should be something like /dev/tty<SOMETHING>.'  )
    self.parser.add_argument(
      '-camdev', type=str,
      help='Device path for the primary camera, should be something like /dev/video<index>.' )

  def run(self,arg):
    if arg.boardtype:
      self.cmd.board.set_boardtype( arg.boardtype.name )
    if arg.camdev and arg.camdev != self.cmd.visual.dev_path :
      self.cmd.visual.init_dev(arg.camdev)
    if arg.printerdev and arg.printerdev != self.cmd.gcoder.dev_path :
      self.cmd.gcoder.initprinter( arg.printerdev )
      logger.printmsg( self.cmd.gcoder.getsettings() )

class get(cmdbase.controlcmd):
  """
  Printing out the session parameters, and equipment settings.
  """
  def __init__(self):
    cmdbase.controlcmd.__init__(self)
    self.parser.add_argument('-boardtype',action='store_true')
    self.parser.add_argument('-opchip',action='store_true')
    self.parser.add_argument('-printerdev', action='store_true')
    self.parser.add_argument('-camdev', action='store_true')
    self.parser.add_argument('-all',action='store_true')

  def run(self,arg):
    if arg.boardtype or arg.all :
      logger.update( "[BOARDTYPE]", str(self.cmd.board.boardtype) )
    if arg.opchip    or arg.all :
      logger.update( "[OPCHIP ID]", str(self.cmd.board.op_chip) )
    if arg.printerdev or arg.all:
      logger.update( "[PRINTER DEV]", str(self.cmd.gcoder.dev_path) )
    if arg.camdev or arg.all:
      logger.update( "[CAM DEV]", str(self.cmd.visual.dev_path) )
    logger.flush_update()
    logger.clear_update()


class getcoord(cmdbase.controlcmd):
  """
  Printing current gantry coordinates
  """

  def __init__(self):
    cmdbase.controlcmd.__init__(self)

  def run(self,arg):
    logger.printmsg("x:{0:.1f} y:{1:.1f} z:{2:.1f}".format(
        self.cmd.gcoder.opx,
        self.cmd.gcoder.opy,
        self.cmd.gcoder.opz
        ))
