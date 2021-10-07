"""
  getset.py

  Commands that are used for looking up, displaying and modifying session
  parameters. This includes loading and saving the master coordinate calibration
  results, setting the readout devices, and commands used to stall the program.
  Notice that "setting the readout devices" will only handle the opening and
  closing of device interfaces, not the actual readout device internal settings.
  That should be handled in their designate command files.
"""

import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
import argparse, re, os, sys, time


class exit(cmdbase.controlcmd):
  """
  Command for exiting the main session
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def run(self, args):
    if self.prompt_yn("""
                      Exiting this will terminate the session and all calibration
                      variables (results are still on disk), are you sure you
                      want to exit?""",
                      default='no'):
      return cmdbase.controlcmd.TERMINATE_SESSION


class set(cmdbase.controlcmd):
  """
  Setting calibration devices. This will only modify opening and closing the
  interface, not the actual operation of the various interfaces.

  - For visual system settings, see command: visualset
  - For settings for the picoscope, see command: picoset
  - For settings for the DRS4, see command: drsset
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('--boardtype',
                             '-b',
                             type=argparse.FileType(mode='r'),
                             help="""
                             Setting board type via a configuration json file
                             that lists DET_ID with x-y coordinates.""")
    self.parser.add_argument('--boardid',
                             '-i',
                             type=str,
                             help="""
                             Override the existing board id with user string""")
    self.parser.add_argument('--printerdev',
                             type=str,
                             help="""
                             Device path for the 3d printer. Should be something
                             like `/dev/tty<SOMETHING>`.""")
    self.parser.add_argument('--camdev',
                             type=str,
                             help="""
                             Device path for the primary camera, should be
                             something like `/dev/video<index>.`""")
    self.parser.add_argument('--picodevice',
                             type=str,
                             help="""
                             The serial number of the pico-tech device for
                             dynamic light readout""")
    self.parser.add_argument('--drsdevice',
                             type=str,
                             help='Code flag to refresh DRS device')
    self.parser.add_argument('--action',
                             '-a',
                             type=argparse.FileType(mode='r'),
                             help="""
                             Add files to a list of short hands for setting user
                             prompts""")

  def run(self, args):
    """
    For the sake of clarity, device settings is split into each of their
    functions. Notice that all function should have expection guards so the
    subsequent settings can still be set if a single settings is bad.
    """
    if args.boardtype:
      self.set_board(args)
    if args.boardid:
      self.board.boardid = args.boardid
    if args.camdev:
      self.set_camera(args)
    if args.printerdev:
      self.set_printer(args)
    if args.picodevice:
      self.set_picodevice(args)
    if args.drsdevice:
      self.set_drs(args)
    if args.action:
      self.action.add_json(args.action.name)

  def set_board(self, args):
    try:
      self.board.set_boardtype(args.boardtype.name)
    except Exception as err:
      log.printerr(str(err))
      log.printwarn('Board type setting has failed, skipping over setting')

  def set_camera(self, args):
    """Setting up the camera system, given /dev/video path"""
    if (not self.is_dummy_dev(args.camdev, 'Visual System')
        and args.camdev != self.visual.dev_path):
      try:
        self.visual.init_dev(args.camdev)
      except Exception as err:
        log.printerr(str(err))
        log.printwarn('Initializing webcam has failed, skipping over setting')

  def set_printer(self, args):
    """Setting up the gantry system, given the /dev/ USB path"""
    if (not self.is_dummy_dev(args.printerdev, 'Printer')
        and args.printerdev != self.gcoder.dev_path):
      try:
        self.gcoder.init(args.printerdev)
        printset = self.gcoder.getsettings()
        printset = printset.split('\necho:')
        for line in printset:
          log.printmsg(log.GREEN('[PRINTER]'), line)
      except Exception as err:
        self.printerr(str(err))
        self.printwarn('Failed to setup printer, skipping over settings')

  def set_picodevice(self, args):
    """Setting up the pico device, Skipping if dummy path detected """
    if not self.is_dummy_dev(args.picodevice, 'PicoScope'):
      try:
        self.pico.init()
      except Exception as err:
        self.printerr(str(err))
        self.printwarn('Picoscope device is not properly set!')

  def set_drs(self, args):
    """Setting up the DRS4. Skipping if dummy path is detected"""
    if not self.is_dummy_dev(args.drsdevice, 'DRS4'):
      try:
        self.drs.init()
      except Exception as err:
        self.printerr(str(err))
        self.printwarn('DRS device is not properly set!')

  def is_dummy_dev(self, dev, device_name):
    """
    Simple check for illegal device string, so that certain hardware interfaces
    can be disabled. A legal device string must start with the '/dev' prefix and
    must not contain the "dummy" string.
    """
    is_dummy = not dev.startswith('/dev') or 'dummy' in dev
    if is_dummy:
      self.printwarn(f"""
        Path [{dev}] for device [{device_name}] is as dummy path, skipping setup
        of device. If not already setup, then future commands using
        [{device_name}] may misbehave.""")
    return is_dummy


class get(cmdbase.controlcmd):
  """
  Printing out the session parameters, and equipment settings. This is bundle
  here for simple debugging.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('--boardtype', action='store_true')
    self.parser.add_argument('--printerdev', action='store_true')
    self.parser.add_argument('--camdev', action='store_true')
    self.parser.add_argument('--align', action='store_true')
    self.parser.add_argument('--pico', action='store_true')
    self.parser.add_argument('--drs', action='store_true')
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
    if args.drs or args.all:
      self.print_drs()
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
    printset = self.gcoder.getsettings()
    printset = printset.split('\necho:')
    for line in printset:
      log.printmsg(log.GREEN('[PRINTER]'), line)

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

  def print_drs(self):
    log.printmsg(self.drs.is_available())

  def print_action(self):
    header = log.GREEN('[ACTION]')
    msg_format = log.YELLOW('{0}') + ' | {1}'
    set_format = log.YELLOW('{0}') + ' | RUN CMD | set {1}'
    for key in self.action.shorthands():
      msg = msg_format.format(key, self.action.getmessage(key))
      smsg = set_format.format(key, " ".join(self.action.getset(key)))
      log.printmsg(header, msg)
      log.printmsg(header, smsg)


class savecalib(cmdbase.controlcmd):
  """
  Saving current calibration information into a json file
  """
  LOG = log.GREEN('[SAVE_CALIB]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('-f',
                             '--file',
                             type=argparse.FileType('w'),
                             required=True,
                             help='File to save the calibration events to')

  def parse(self, args):
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

  def add_args(self):
    self.parser.add_argument(
        '-f',
        '--file',
        type=argparse.FileType('r'),
        help='File to load the calibration information from')

  def parse(self, args):
    if not args.file:
      raise Exception('Filename must be specified')
    return args

  def run(self, args):
    self.board.load_calib_file(args.file.name)


class promptaction(cmdbase.controlcmd):
  """
  Displaying message that requires manual intervention. This is handy for
  inserting pause points in a runfile that requires user intervension.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('string',
                             nargs=1,
                             type=str,
                             help="""
        String of message to show (program is paused until Enter key is pressed).
        This can either be a short hand that is defined using the loadaction
        command (use the listaction command to get a list) or a raw string
        message that is to be shown on the screen""")

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
      self.printmsg(log.GREEN(f'    TYPE [{args.string[0]}] to continue...'))
      input_text = self.cmd.stdin.readline().strip()

    if is_defined:
      cmd = 'set ' + ' '.join(self.action.getset(args.string[0]))
      self.cmd.onecmd(cmd.strip())


class history(cmdbase.controlcmd):
  """
  Getting the input history. Notice that this will only include the user input
  history. Commands in the runfile will note be expanded.
  """
  LOG = log.GREEN("[SIPMCALIB HISTORY]")

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def run(self, args):
    import readline
    self.printmsg(
        f'commands since startup: {str(readline.get_current_history_length())}')
    for idx in range(1, readline.get_current_history_length() + 1):
      self.printmsg(readline.get_history_item(idx))


class wait(cmdbase.controlcmd):
  """
  Suspending the interactive session for N seconds. The wait time can be
  terminated early using Ctl+C.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('--time',
                             '-t',
                             type=float,
                             default=30,
                             help='Time to suspend session (seconds)')

  def run(self, args):
    start_time = time.time_ns()
    current_time = start_time
    while (current_time - start_time) / 1e9 < args.time:
      self.check_handle(args)
      time.sleep(0.1)
      current_time = time.time_ns()


class runfile(cmdbase.controlcmd):
  """
  Running a file with a list of commands.

  Notice that while runfiles can be called recursively, you cannot call runfiles
  that have already been called, as this will cause infinite recursion. If any
  command in the command file fails, the whole runfile call will be terminated to
  prevent user error from damaging the gantry.
  """
  LOG = log.GREEN('[RUNFILE LINE]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('file',
                             nargs=1,
                             type=str,
                             help="""
                             Runfile to use. Relative paths will be evaluated
                             from the current working directory.""")

  def parse(self, args):
    """Making sure the target is a readable file."""
    args.file = args.file[0]
    if not os.path.isfile(args.file):
      raise RuntimeError('Specified path is not a file!')
    return args

  def run(self, args):
    """
    The command will infer a runfile stack in the controlterm instance to keep
    track of which files has already been invoked by the runfile command. The
    last file in the stack will be opened and executed per-line.
    """
    if not hasattr(self.cmd, 'runfile_stack'):
      self.cmd.runfile_stack = []

    if args.file in self.cmd.runfile_stack:
      self.error_exit_run(f"""
        File [{args.file}] has already been called! This indicates there is some
        error in user logic. Exiting the top level runfile command.
      """)
    else:
      self.cmd.runfile_stack.append(args.file)

    with open(args.file) as f:
      for line in f.readlines():
        line = line.strip()
        self.check_handle(args)
        self.printmsg(line)
        status = self.cmd.onecmd(line)
        if status != cmdbase.controlcmd.EXIT_SUCCESS:
          self.error_exit_run(f"""
            Command [{line}] in file [{args.file}] has failed.
            Exiting top level runfile command.
          """)
    self.cmd.runfile_stack.pop(-1)

  def error_exit_run(self, msg):
    """
    Save exit on error to ensure that the runfile stack is properly cleared out.
    """
    self.cmd.runfile_stack = []
    raise RuntimeError(msg)

  def complete(self, text, line, start_index, end_index):
    return cmdbase.controlcmd.globcomp(text)
