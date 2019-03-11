import ctlcmd.cmdbase as cmdbase
import cmod.gcoder as gcoder
import cmod.logger as logger
import cmod.sshfiler as sshfiler
import argparse

class set(cmdbase.controlcmd):
  """
  Setting session parameters
  """

  def __init__(self,cmd):
    cmdbase.controlcmd.__init__(self,cmd)
    self.parser.add_argument(
        '-boardtype',
        type=argparse.FileType(mode='r'),
        help=
        'Setting board type via a configuration json file that lists CHIP_ID with x-y- coordinates.'
    )
    self.parser.add_argument(
        '-printerdev',
        type=str,
        help=
        'Device path for the 3d printer. Should be something like /dev/tty<SOMETHING>.'
    )
    self.parser.add_argument(
        '-camdev',
        type=str,
        help=
        'Device path for the primary camera, should be something like /dev/video<index>.'
    )

  def run(self, arg):
    if arg.boardtype:
      try:
        self.cmd.board.set_boardtype(arg.boardtype.name)
      except Exception as err:
        logger.printerr(str(err))
        logger.printwarn("Board type setting has failed, skipping over setting")
    if arg.camdev and arg.camdev != self.cmd.visual.dev_path:
      try:
        self.cmd.visual.init_dev(arg.camdev)
      except Exception as err:
        logger.printerr(str(err))
        logger.printwarn("Initializing webcam has failed, skipping over setting")
    if arg.printerdev and arg.printerdev != self.cmd.gcoder.dev_path:
      try:
        self.cmd.gcoder.initprinter(arg.printerdev)
        printset = self.cmd.gcoder.getsettings()
        printset = printset.split('\necho:')
        for line in printset:
          logger.printmsg(logger.GREEN("[PRINTER]"), line )
      except Exception as err:
        logger.printerr(str(err))
        logger.printwarn("Failed to setup printer, skipping over settings")


class get(cmdbase.controlcmd):
  """
  Printing out the session parameters, and equipment settings.
  """

  def __init__(self,cmd):
    cmdbase.controlcmd.__init__(self,cmd)
    self.parser.add_argument('-boardtype', action='store_true')
    self.parser.add_argument('-opchip', action='store_true')
    self.parser.add_argument('-printerdev', action='store_true')
    self.parser.add_argument('-camdev', action='store_true')
    self.parser.add_argument('-all', action='store_true')

  def run(self, arg):
    if arg.boardtype or arg.all:
      logger.update("[BOARDTYPE]", str(self.cmd.board.boardtype))
    if arg.opchip or arg.all:
      logger.update("[OPCHIP ID]", str(self.cmd.board.op_chip))
    if arg.printerdev or arg.all:
      logger.update("[PRINTER DEV]", str(self.cmd.gcoder.dev_path))
    if arg.camdev or arg.all:
      logger.update("[CAM DEV]", str(self.cmd.visual.dev_path))
    logger.flush_update()
    logger.clear_update()


class getcoord(cmdbase.controlcmd):
  """
  Printing current gantry coordinates
  """

  def __init__(self,cmd):
    cmdbase.controlcmd.__init__(self,cmd)

  def run(self, arg):
    logger.printmsg("x:{0:.1f} y:{1:.1f} z:{2:.1f}".format(
        self.cmd.gcoder.opx, self.cmd.gcoder.opy, self.cmd.gcoder.opz))

class remotelogin(cmdbase.controlcmd):
  """
  Resetting a login setting in case first login failed
  """
  def __init__(self,cmd):
    cmdbase.controlcmd.__init__(self,cmd)

  def run(self,arg):
    ## Re-instancing is enough!
    self.cmd.sshfiler = sshfiler.SSHFiler()

    logger.printmsg(logger.GREEN('Login success!'))