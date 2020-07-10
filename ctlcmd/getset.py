import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
from cmod.readout import readout
import argparse
import re


class set(cmdbase.controlcmd):
  """
  Setting session parameters
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('--boardtype',
                             '-b',
                             type=argparse.FileType(mode='r'),
                             help=('Setting board type via a configuration json '
                                   'file that lists DET_ID with x-y '
                                   'coordinates.'))
    self.parser.add_argument('--boardid',
                             '-i',
                             type=str,
                             help=('Override the existing board id with user '
                                   'string'))
    self.parser.add_argument('--printerdev',
                             type=str,
                             help=('Device path for the 3d printer. Should be '
                                   'something like `/dev/tty<SOMETHING>`.'))
    self.parser.add_argument('--camdev',
                             type=str,
                             help=('Device path for the primary camera, should '
                                   'be something like `/dev/video<index>.`'))
    self.parser.add_argument('--remotehost',
                             type=str,
                             help='Connecting to remote host for file transfer')
    self.parser.add_argument('--remotepath',
                             type=str,
                             help='Remote directory to save files to')
    self.parser.add_argument('--picodevice',
                             type=str,
                             help=('The serial number of the pico-tech device '
                                   'for dynamic light readout'))
    self.parser.add_argument(
        '--readout',
        '-r',
        type=int,
        choices=[readout.MODE_ADC, readout.MODE_PICO, readout.MODE_NONE],
        help='Setting readout mode of the current session')
    self.parser.add_argument('--action',
                             '-a',
                             type=argparse.FileType(mode='r'),
                             help=('Add files to a list of short hands for '
                                   'setting user prompts'))

  def run(self, args):
    if args.boardtype:
      self.set_board(args)
    if args.boardid:
      self.board.boardid = args.boardid
    if args.camdev:
      self.set_camera(args)
    if args.printerdev:
      self.set_printer(args)
    if args.remotehost:
      self.set_host(args)
    if args.remotepath:
      self.sshfiler.setremotepath(args.remotepath)
    if args.picodevice:
      self.set_picodevice(args)
    if args.readout:
      self.readout.set_mode(args.readout)
    if args.action:
      self.action.add_json(args.action.name)

  def set_board(self, args):
    try:
      self.board.set_boardtype(args.boardtype.name)
    except Exception as err:
      log.printerr(str(err))
      log.printwarn('Board type setting has failed, skipping over setting')

  def set_camera(self, args):
    if args.camdev == self.visual.dev_path:
      pass
    try:
      self.visual.init_dev(args.camdev)
    except Exception as err:
      log.printerr(str(err))
      log.printwarn('Initializing webcam has failed, skipping over setting')

  def set_printer(self, args):
    if args.printerdev == self.gcoder.dev_path:
      pass
    try:
      self.gcoder.initprinter(args.printerdev)
      printset = self.gcoder.getsettings()
      printset = printset.split('\necho:')
      for line in printset:
        log.printmsg(log.GREEN('[PRINTER]'), line)
    except Exception as err:
      log.printerr(str(err))
      log.printwarn('Failed to setup printer, skipping over settings')

  def set_host(self, args):
    try:
      self.sshfiler.reconnect(args.remotehost)
    except Exception as err:
      log.printerr(str(err))
      log.printwarn('Failed to establish connection remote host')

  def set_picodevice(self, args):
    try:
      self.pico.init()
    except Exception as err:
      log.printerr(str(err))
      log.printwarn('Picoscope device is not properly set!')


class get(cmdbase.controlcmd):
  """
  Printing out the session parameters, and equipment settings.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('--boardtype', action='store_true')
    self.parser.add_argument('--printerdev', action='store_true')
    self.parser.add_argument('--camdev', action='store_true')
    self.parser.add_argument('--origdet', action='store_true')
    self.parser.add_argument('--align', action='store_true')
    self.parser.add_argument('--pico', action='store_true')
    self.parser.add_argument('--readout', action='store_true')
    self.parser.add_argument('--action', action='store_true')

    self.parser.add_argument('-a', '--all', action='store_true')

  def run(self, args):
    if args.boardtype or args.all:
      self.print_board()
    if args.printerdev or args.all:
      self.print_printer()
    if args.camdev or args.all:
      self.print_camera()
    if args.align or args.all:
      self.print_alignment()
    if args.pico or args.all:
      self.pico.printinfo()
    if args.readout or args.all:
      self.print_readout()
    if args.action or args.all:
      self.print_action()

  def print_board(self):
    header = log.GREEN('[BOARDTYPE]')
    msg_format = 'Det:{0:>4s} | x:{1:5.1f}, y:{2:5.1f}'
    log.printmsg(header, str(self.board.boardtype))
    log.printmsg(header, str(self.board.boarddescription))
    log.printmsg(header, 'Board ID: ' + self.board.boardid)
    for detid in self.board.dets():
      det = self.board.get_det(detid)
      msg = msg_format.format(detid, det.orig_coord[0], det.orig_coord[1])
      log.printmsg(header, msg)

  def print_printer(self):
    header = log.GREEN('[PRINTER]')
    log.printmsg(header, 'device: ' + str(self.gcoder.dev_path))
    log.printmsg(
        header, 'current coordinates: x{0:.1f} y{1:.1f} z{2:0.1f}'.format(
            self.gcoder.opx, self.gcoder.opy, self.gcoder.opz))

  def print_camera(self):
    header = log.GREEN('[CAMERA]')
    log.printmsg(header, str(self.visual.dev_path))
    log.printmsg(header, 'Threshold:{0:3f}'.format(self.visual.threshold))
    log.printmsg(header, 'Blur:     {0:3d} [pix]'.format(self.visual.blur_range))
    log.printmsg(header, 'Max Lumi: {0:3f}'.format(self.visual.lumi_cutoff))
    log.printmsg(header,
                 'Min Size: {0:3d} [pix]'.format(self.visual.size_cutoff))
    log.printmsg(header, 'Ratio:    {0:3f}'.format(self.visual.ratio_cutoff))
    log.printmsg(header, 'Poly:     {0:3f}'.format(self.visual.poly_range))

  def print_alignment(self):
    lumi_header = log.GREEN('[LUMI_ALIGN]')
    matrix_header = log.GREEN('[VIS_MATRIX]')
    vis_header = log.GREEN('[VIS__ALIGN]')
    det_format = log.YELLOW(' DET{0:3d}')

    print('Printing alignment information')

    for detid in self.board.dets():
      det_str = det_format.format(int(detid))
      det = self.board.get_det(detid)
      for z in det.lumi_coord:
        log.printmsg(
            lumi_header + det_str,
            'x:{0:.2f}+-{1:.2f} y:{2:.2f}+-{3:.2f} | at z={4:.1f}'.format(
                det.lumi_coord[z][0], det.lumi_coord[z][2], det.lumi_coord[z][1],
                det.lumi_coord[z][3], z))
      for z in det.vis_M:
        log.printmsg(matrix_header + det_str, '{0} | at z={1:.1f}'.format(
            det.vis_M[z], z))
      for z in det.vis_coord:
        log.printmsg(
            vis_header + det_str, 'x:{0:.2f} y:{1:.2f} | at z={2:.1f}'.format(
                det.vis_coord[z][0], det.vis_coord[z][1], z))

  def print_readout(self):
    log.printmsg(
      log.GREEN('[READOUT]'),
      'PICOSCOPE' if self.readout.mode == readout.MODE_PICO else \
      'ADC DET'  if self.readout.mode == readout.MODE_ADC  else \
      'PREDEFINED MODEL')

  def print_action(self):
    header = log.GREEN('[ACTION]')
    msg_format = log.YELLOW('{0}') + ' | {1}'
    set_format = log.YELLOW('{0}') + ' | RUN CMD | set {1}'
    for key in self.action.shorthands():
      msg = msg_format.format(key, self.action.getmessage(key))
      smsg = set_format.format(key, " ".join(self.action.getset(key)))
      log.printmsg(header, msg)
      log.printmsg(header, smsg)


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
  LOG = log.GREEN('[SAVE_CALIB]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('-f',
                             '--file',
                             type=argparse.FileType('w'),
                             required=True,
                             help='File to save the calibration events to')

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    if not args.file:
      raise Exception('File name must be specified')
    return args

  def run(self, args):
    self.printmsg('Saving calibration results to file [{0}]'.format(
        args.file.name))
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
    args = cmdbase.controlcmd.parse(self, line)
    if not args.file:
      raise Exception('Filename must be specified')
    return args

  def run(self, args):
    self.board.load_calib_file(args.file.name)


class lighton(cmdbase.controlcmd):
  """
  Turning the LED lights on.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def run(self, args):
    self.gpio.light_on()


class lightoff(cmdbase.controlcmd):
  """
  Turning the LED lights on.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def run(self, line):
    self.gpio.light_off()


class promptaction(cmdbase.controlcmd):
  """
  Displaying message that requires manual intervention.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument(
        'string',
        nargs=1,
        type=str,
        help=('String of message to show (program is paused until Enter key '
              'is pressed). This can either be a short hand that is defined '
              'using the loadaction command (use the listaction command to '
              'get a list) or a raw string message that is to be shown on the '
              'screen'))

  def parse(self, line):
    return cmdbase.controlcmd.parse(self, line)

  def run(self, args):
    def color_change(x):
      """
      Formatting the output for clarity of what the user should be doing.
      """
      if x == '[ON]':
        return log.GREEN(x)
      if x == '[OFF]':
        return log.RED(x)
      if re.match(r'\[[\d\.]+[a-zA-Z]*\]', x):
        return log.GREEN(x)
      if x.isupper():
        return log.YELLOW(x)
      return x

    is_defined = args.string[0] in self.action.shorthands()

    msg = self.action.getmessage(args.string[0]) if is_defined \
          else args.string[0]

    msg = ' '.join([color_change(x) for x in msg.split()])
    log.printmsg(log.GREEN('    THE NEXT STEP REQUIRES USER INTERVENTION'))
    log.printmsg('    > ' + msg)

    input_text = ''
    while input_text != args.string[0]:
      self.check_handle(args)
      input_text = input(
          log.GREEN('    TYPE [%s] to continue...') % args.string[0])

    if is_defined:
      cmd = 'set ' + ' '.join(self.action.getset(args.string[0]))
      self.cmd.onecmd(cmd.strip())
