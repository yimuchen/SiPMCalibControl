import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
import argparse
from cmod.readout import readout


class set(cmdbase.controlcmd):
  """
  Setting session parameters
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument(
        '-boardtype',
        type=argparse.FileType(mode='r'),
        help=('Setting board type via a configuration json file that lists '
              'CHIP_ID with x-y-coordinates.'))
    self.parser.add_argument(
        '-printerdev',
        type=str,
        help=('Device path for the 3d printer. Should be something like '
              '`/dev/tty<SOMETHING>`.'))
    self.parser.add_argument(
        '-camdev',
        type=str,
        help=('Device path for the primary camera, should be something like '
              '/dev/video<index>.'))
    self.parser.add_argument('-remotehost',
                             type=str,
                             help='Connecting to remote host for file transfer')
    self.parser.add_argument('-remotepath',
                             type=str,
                             help='Remote directory to save files to')
    self.parser.add_argument(
        '-picodevice',
        type=str,
        help=('The serial number of the pico-tech device for dynamic light '
              'readout'))
    self.parser.add_argument(
        '-readout',
        type=int,
        choices=[readout.MODE_ADC, readout.MODE_PICO, readout.MODE_NONE],
        help='Setting readout mode of the current session')

  def run(self, arg):
    if arg.boardtype:
      try:
        self.board.set_boardtype(arg.boardtype.name)
      except Exception as err:
        log.printerr(str(err))
        log.printwarn('Board type setting has failed, skipping over setting')
    if arg.camdev and arg.camdev != self.visual.dev_path:
      try:
        self.visual.init_dev(arg.camdev)
      except Exception as err:
        log.printerr(str(err))
        log.printwarn('Initializing webcam has failed, skipping over setting')
    if arg.printerdev and arg.printerdev != self.gcoder.dev_path:
      try:
        self.gcoder.initprinter(arg.printerdev)
        printset = self.gcoder.getsettings()
        printset = printset.split('\necho:')
        for line in printset:
          log.printmsg(log.GREEN('[PRINTER]'), line)
      except Exception as err:
        log.printerr(str(err))
        log.printwarn('Failed to setup printer, skipping over settings')
    if arg.remotehost:
      print(self.sshfiler.host)
      try:
        self.sshfiler.reconnect(arg.remotehost)
      except Exception as err:
        log.printerr(str(err))
        log.printwarn('Failed to establish connection remote host')
    if arg.remotepath:
      self.sshfiler.setremotepath(arg.remotepath)
    if arg.picodevice:
      try:
        self.pico.init()
      except Exception as err:
        log.printerr(str(err))
        log.printwarn('Picoscope device is not properly set!')
    if arg.readout:
      self.readout.set_mode(arg.readout)


class get(cmdbase.controlcmd):
  """
  Printing out the session parameters, and equipment settings.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('--boardtype', action='store_true')
    self.parser.add_argument('--printerdev', action='store_true')
    self.parser.add_argument('--camdev', action='store_true')
    self.parser.add_argument('--origchip', action='store_true')
    self.parser.add_argument('--align', action='store_true')
    self.parser.add_argument('--pico', action='store_true')
    self.parser.add_argument('--readout', action='store_true')

    self.parser.add_argument('-a', '--all', action='store_true')

  def run(self, arg):
    if arg.boardtype or arg.all:
      log.printmsg(log.GREEN("[BOARDTYPE]"), str(self.board.boardtype))
      for chip in self.board.chips():
        log.printmsg(
            log.GREEN('[BOARDTYPE]'),
            'Default Coord | Chip:{0} | x:{1}, y:{2}'.format(
                chip, self.board.orig_coord[chip][0],
                self.board.orig_coord[chip][1]))
    if arg.printerdev or arg.all:
      log.printmsg(log.GREEN('[PRINTER DEV]'), str(self.gcoder.dev_path))
    if arg.camdev or arg.all:
      log.printmsg(log.GREEN('[CAM DEV]'), str(self.visual.dev_path))
    if arg.align or arg.all:
      for chip in self.board.chips():
        for z in self.board.lumi_coord[chip].keys():
          log.printmsg(
              log.GREEN('[LUMI ALIGN]') + log.YELLOW('[CHIP%s]' % chip),
              'x:{0:.2f}+-{1:.2f} y:{2:.2f}+-{3:.2f} | at z={4:.1f}'.format(
                  self.board.vis_coord[chip][z][0],
                  self.board.vis_coord[chip][z][2],
                  self.board.vis_coord[chip][z][1],
                  self.board.vis_coord[chip][z][3], z))
        for z in self.board.visM[chip].keys():
          log.printmsg(
              log.GREEN('[VISUAL MATRIX]') + log.YELLOW('[CHIP%s]' % chip),
              '{0} | at z={1:.1f}'.format(self.board.visM[chip][z], z))
        for z in self.board.vis_coord[chip].keys():
          log.printmsg(
              log.GREEN('[VISUAL ALIGN]') + log.YELLOW('[CHIP%s]' % chip),
              'x:{0:.2f} y:{1:.2f} | at z={2:.1f}'.format(
                  self.board.vis_coord[chip][z][0],
                  self.board.vis_coord[chip][z][1], z))
    if arg.pico or arg.all:
      self.pico.printinfo()
    if arg.readout or arg.all:
      log.printmsg(
        log.GREEN('[READOUT MODE]'),
        'PICOSCOPE' if self.readout.mode == readout.MODE_PICO else \
        'ADC CHIP'  if self.readout.mode == readout.MODE_ADC  else \
        'PREDEFINED MODEL'
      )


class getcoord(cmdbase.controlcmd):
  """
  Printing current gantry coordinates
  """
  LOG = log.GREEN('[GANTRY-COORD]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def run(self, args):
    self.printmsg('x:{0:.1f} y:{1:.1f} z:{2:.1f}'.format(
        self.gcoder.opx, self.gcoder.opy, self.gcoder.opz))


class savecalib(cmdbase.controlcmd):
  """
  Saving current calibration information into a json file
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('-f',
                             '--file',
                             type=argparse.FileType('w'),
                             required=True,
                             help='File to save the calibration events to')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    if not arg.file:
      raise Exception('File name must be specified')
    return arg

  def run(self, args):
    self.board.save_calib_file(args.file.name)


class loadcalib(cmdbase.controlcmd):
  """
  Loading calibration information from a json file
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument(
        '-f',
        '--file',
        type=argparse.FileType('r'),
        help='File to load the calibration information from')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    if not arg.file:
      raise Exception('Filename must be specified')
    return arg

  def run(self, args):
    self.board.load_calib_file(args.file.name)
