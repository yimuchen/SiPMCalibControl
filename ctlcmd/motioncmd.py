"""

  motioncmd.py

  COmmands related with controlling the gantry motion. Due to legacy reasons,
  this will include the luminosity alignment commands, as well as the non-linear
  scan command by moving in z.

"""
import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
import numpy as np
from scipy.optimize import curve_fit
import time


class rungcode(cmdbase.controlcmd):
  """
  Running a raw command gcode command. Notice that the gantry may still be busy
  after the command has been reported as completed by the gantry (ex: Motion
  command will be completed after the internal target coordinates have been
  updated, not when the gantry fully stops moving.) The user must be careful to
  add appropriate wait signals to avoid damaging the hardware when using this
  command.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument("cmd",
                             type=str,
                             #required=True,
                             help="Raw gcode command to run")

  def parse(self, args):
    args.cmd = args.cmd + '\n'
    return args

  def run(self, args):
    retstr = self.gcoder.run_gcode(args.cmd, 0, int(1e5), True)
    retstr = retstr.split('\necho:')
    for line in retstr:
      log.printmsg(log.GREEN('[PRINTER]'), line)


class moveto(cmdbase.singlexycmd):
  """
  Moving the gantry head to a specific location, either by det ID or by raw
  x,y,z coordinates. Units for the x-y-z inputs is millimeters.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('-z',
                             type=float,
                             help="""
                             Specifying the z coordinate explicitly [mm]. If
                             none is given the current gantry position will be
                             used instead""")

  def parse(self, args):
    if not args.z: args.z = self.gcoder.opz
    return args

  def run(self, args):
    self.move_gantry(args.x, args.y, args.z, True)


class getcoord(cmdbase.controlcmd):
  """
  Printing current gantry coordinates
  """
  LOG = log.GREEN('[GANTRY-COORD]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def run(self, args):
    self.printmsg('x:{0:.1f} y:{1:.1f} z:{2:.1f}'.format(
        self.gcoder.cx, self.gcoder.cy, self.gcoder.cz))


class disablestepper(cmdbase.controlcmd):
  """
  Manual disabling of stepper motor. Boolean flag for stopping each of the x,y,z
  components.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('-x',
                             action='store_true',
                             help='Disable x axis stepper motors')
    self.parser.add_argument('-y',
                             action='store_true',
                             help='Disable y axis stepper motors')
    self.parser.add_argument('-z',
                             action='store_true',
                             help='Disable z axis stepper motors')

  def run(self, args):
    self.gcoder.disablestepper(args.x, args.y, args.z)


class enablestepper(cmdbase.controlcmd):
  """
  Manual re-enabling of stepper motor. Boolean flag for stopping each of the
  x,y,z components.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('-x',
                             action='store_true',
                             help='Activate x axis stepper motors')
    self.parser.add_argument('-y',
                             action='store_true',
                             help='Activate y axis stepper motors')
    self.parser.add_argument('-z',
                             action='store_true',
                             help='Activate z axis stepper motors')

  def run(self, args):
    self.gcoder.enablestepper(args.x, args.y, args.z)


class movespeed(cmdbase.controlcmd):
  """
  Setting the motion speed of the gantry x-y-z motors. Units in mm/s.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('-x',
                             type=float,
                             help='motion speed of gantry in x axis')
    self.parser.add_argument('-y',
                             type=float,
                             help='motion speed of gantry in y axis')
    self.parser.add_argument('-z',
                             type=float,
                             help='motion speed of gantry in z axis')

  def parse(self, args):
    if not args.x: args.x = float('nan')
    if not args.y: args.y = float('nan')
    if not args.z: args.z = float('nan')

    return args

  def run(self, args):
    self.gcoder.set_speed_limit(args.x, args.y, args.z)


class sendhome(cmdbase.controlcmd):
  """
  Sending the gantry system home. This will reset in the internal coordinate
  systems in the gantry. So use only when needed.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('-x',
                             action='store_true',
                             help='reset x coordinates to 0')
    self.parser.add_argument('-y',
                             action='store_true',
                             help='reset y coordinates to 0')
    self.parser.add_argument('-z',
                             action='store_true',
                             help='reset z coordinates to 0')
    self.parser.add_argument('--all',
                             '-a',
                             action='store_true',
                             help='reset all coordinates to 0')

  def parse(self, args):
    # Filling with NAN for missing settings.
    if args.all:
      args.x = True
      args.y = True
      args.z = True
    return args

  def run(self, args):
    self.gcoder.sendhome(args.x, args.y, args.z)


class halign(cmdbase.readoutcmd, cmdbase.hscancmd, cmdbase.savefilecmd):
  """
  Running horizontal alignment procedure by luminosity readout v.s. x-y motion
  scanning. Notice that when running with scope-like readout systems (with the
  picoscope or DRS4), it assumes that the readout system has their readout
  settings adjusted to suitable value: trigger/range/integration range... etc.
  Make sure that is the case before running these commands.
  """

  DEFAULT_SAVEFILE = 'halign_<BOARDTYPE>_<BOARDID>_<DETID>_<SCANZ>_<TIMESTAMP>.txt'
  LOG = log.GREEN('[LUMI ALIGN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('--overwrite',
                             action='store_true',
                             help="""
                             Forcing the storage of scan results as session
                             information""")
    self.parser.add_argument('--power',
                             '-p',
                             type=float,
                             help="""
                             PWM duty cycle for data collection, using current
                             value if not specified""")

  def parse(self, args):
    if not args.power:
      args.power = self.gpio.pwm_duty(0)  ## Getting the PWM value
    return args

  def run(self, args):
    self.gpio.pwm(0, args.power, 1e5)  # Maximum PWM frequency
    lumi = []
    unc = []
    total = len(args.x)

    ## Running over mesh.
    for idx, (xval, yval) in enumerate(zip(args.x, args.y)):
      self.check_handle(args)
      self.move_gantry(xval, yval, args.scanz, False)
      lumival, uncval = self.readout(args, average=True)
      self.update_progress(progress=(idx + 1, total),
                           coordinates=True,
                           temperature=True,
                           display_data={'Lumi': (lumival, uncval)})
      self.write_standard_line((lumival, uncval), det_id=args.detid)
      lumi.append(abs(lumival))
      unc.append(uncval)

    # Performing fit
    p0 = (
        max(lumi) * (args.scanz**2),  #
        np.mean(args.x),  #
        np.mean(args.y),  #
        args.scanz,  #
        min(lumi))
    try:
      fitval, fitcovar = curve_fit(halign.model,
                                   np.vstack((args.x, args.y)),
                                   lumi,
                                   p0=p0,
                                   sigma=unc,
                                   maxfev=1000000)
    except Exception as err:
      self.printerr(f"""
                    Lumi fit failed to converge, check output stored in file
                    {self.savefile.name} for collected values""")
      self.move_gantry(args.x, args.y, args.scanz, False)
      raise err

    self.printmsg('Best x:{0:.2f}+-{1:.3f}'.format(fitval[1],
                                                   np.sqrt(fitcovar[1][1])))
    self.printmsg('Best y:{0:.2f}+-{1:.3f}'.format(fitval[2],
                                                   np.sqrt(fitcovar[2][2])))
    self.printmsg('Fit  z:{0:.2f}+-{1:.3f}'.format(fitval[3],
                                                   np.sqrt(fitcovar[3][3])))

    detid = str(args.detid)  ## Ensuring string convention in using this
    ## Generating calibration det id if using det coordinates
    if not detid in self.board.dets() and int(detid) < 0:
      self.board.add_calib_det(detid, args.mode, args.channel)

    ## Saving session information
    if not self.board.lumi_coord_hasz(detid, args.scanz) or args.overwrite:
      self.board.add_lumi_coord(detid, args.scanz, [
          fitval[1],
          np.sqrt(fitcovar[1][1]), fitval[2],
          np.sqrt(fitcovar[1][1])
      ])
    elif self.board.lumi_coord_hasz(detid, args.scanz):
      if self.prompt_yn(f"""
                        A lumi alignment for z={args.scanz:.1f} already exists
                        for the current session, overwrite?""",
                        default='no'):
        self.board.add_lumi_coord(detid, args.scanz, [
            fitval[1],
            np.sqrt(fitcovar[1][1]), fitval[2],
            np.sqrt(fitcovar[1][1])
        ])

    ## Sending gantry to position
    if (fitval[1] > 0 and fitval[1] < self.gcoder.max_x() and fitval[2] > 0
        and fitval[2] < self.gcoder.max_y()):
      self.move_gantry(fitval[1], fitval[2], args.scanz, True)
    else:
      self.printwarn("""
      Fit position is out of gantry bounds, the gantry will not attempt to move
      there
      """)

  @staticmethod
  def model(xydata, N, x0, y0, z, p):
    x, y = xydata
    D = (x - x0)**2 + (y - y0)**2 + z**2
    return (N * z / D**1.5) + p


class zscan(cmdbase.singlexycmd, cmdbase.zscancmd, cmdbase.readoutcmd,
            cmdbase.savefilecmd):
  """
  Performing the intensity scan give a list of scanning z coordinates and the
  list of biassing power.
  """

  DEFAULT_SAVEFILE = 'zscan_<BOARDTYPE>_<BOARDID>_<DETID>_<TIMESTAMP>.txt'
  LOG = log.GREEN('[LUMI ZSCAN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('--power',
                             '-p',
                             nargs='*',
                             type=float,
                             help="""
                             Give a list of pwm duty cycle values to try for each
                             coordinate point""")

  def parse(self, args):
    if not args.power:
      args.power = [self.gpio.pwm_duty(0)]  ## Getting the PWM value
    return args

  def run(self, args):
    lumi = []
    unc = []

    for idx, z in enumerate(args.zlist):
      self.move_gantry(args.x, args.y, z, False)
      for power in args.power:
        self.check_handle(args)

        self.gpio.pwm(0, power, 1e5)  # Maximum PWM frequency

        lumival = 0
        uncval = 0
        while 1:
          lumival, uncval = self.readout(args, average=True)
          if args.mode == cmdbase.readoutcmd.Mode.MODE_PICO:
            wmax = self.pico.waveformmax(args.channel)
            current_range = self.pico.rangeA(
            ) if args.channel == 0 else self.pico.rangeB()
            if wmax < 100 and current_range > self.pico.rangemin():
              self.pico.setrange(args.channel, current_range - 1)
            elif wmax > 200 and current_range < self.pico.rangemax():
              self.pico.setrange(args.channel, current_range + 1)
            else:
              break
          else:
            break

        lumi.append(lumival)
        unc.append(uncval)

        self.write_standard_line((lumival, uncval), det_id=args.detid)
        self.update_progress(progress=(idx + 1, len(args.zlist)),
                             temperature=True,
                             coordinates=True,
                             display_data={'Lumi': (lumival, uncval)})


class lowlightcollect(cmdbase.singlexycmd, cmdbase.readoutcmd,
                      cmdbase.savefilecmd):
  """
  Collection of low light data at a single gantry position, collecting data as
  fast as possible no waiting.
  """
  DEFAULT_SAVEFILE = 'lowlight_<BOARDTYPE>_<BOARDID>_<DETID>_<TIMESTAMP>.txt'
  LOG = log.GREEN('[LUMI LOWLIGHT]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('-z',
                             type=float,
                             default=300,
                             help="""
                             z height to perform the low light collection
                             result. (units: mm)""")
    self.parser.add_argument('--power',
                             '-p',
                             type=float,
                             help="""
                             PWM duty cycle for data collection, using current
                             value if not specified""")

  def parse(self, args):
    if not args.power:
      args.power = self.gpio.pwm_duty(0)
    ## Modifying the sample argument to make monitoring simpler:
    args.nparts = (args.samples // 1000) + 1
    args.samples = 1000
    return args

  def run(self, args):
    self.move_gantry(args.x, args.y, args.z, False)
    self.gpio.pwm(0, args.power, 1e5)
    for i in range(args.nparts):
      self.check_handle(args)
      readout = self.readout(args, average=False)
      self.write_standard_line(readout, det_id=args.detid)
      self.update_progress(progress=(i + 1, args.nparts),
                           temperature=True,
                           coordinates=True,
                           display_data={'Lumi': (readout[-1], readout[-2])})


class timescan(cmdbase.readoutcmd, cmdbase.savefilecmd):
  """
  Generate a log of the readout in terms relative to time.
  """
  DEFAULT_SAVEFILE = 'tscan_<TIMESTAMP>.txt'
  LOG = log.GREEN('[TIMESCAN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('--nslice',
                             type=int,
                             default=30,
                             help='total number of measurement to take')
    self.parser.add_argument('--interval',
                             type=float,
                             default=1,
                             help='Time interval between measurements (seconds)')
    self.parser.add_argument('--testpwm',
                             type=float,
                             nargs='*',
                             help="""
                             PWM duty cycle values to cycle through while
                             performing test""")
    self.parser.add_argument('--pwmslices',
                             type=int,
                             default=10,
                             help="""
                             Number of time slices to take for a given PWM test
                             value""")

  def parse(self, args):
    if not args.testpwm:
      args.testpwm = [self.gpio.pwm_duty(0)]
    return args

  def run(self, args):
    start_time = time.time_ns()
    pwmindex = 0

    for i in range(args.nslice):
      self.check_handle(args)
      if (i % args.pwmslices == 0):
        self.gpio.pwm(0, args.testpwm[pwmindex], 1e5)
        pwmindex = (pwmindex + 1) % len(args.testpwm)

      lumival, uncval = self.readout(args, average=True)
      s2 = self.visual.get_latest().s2
      s4 = self.visual.get_latest().s4
      sample_time = time.time_ns()
      timestamp = (sample_time - start_time) / 1e9
      self.write_standard_line((lumival, uncval, s2, s4),
                               det_id=-100,
                               time=timestamp)
      self.update_progress(progress=(i + 1, args.nslice),
                           coordinates=True,
                           temperature=True,
                           display_data={
                               'luminosity': [lumival, uncval],
                               'sharpness': [s2, s4]
                           })
      time.sleep(args.interval)
