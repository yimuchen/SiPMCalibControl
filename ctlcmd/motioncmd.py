import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
import numpy as np
from scipy.optimize import curve_fit
import time


class moveto(cmdbase.controlcmd):
  """
  Moving the gantry head to a specific location, either by det ID or by raw
  x-y-z coordinates. Units for the x-y-z inputs is millimeters.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.add_xydet_options()
    self.parser.add_argument('-z',
                             type=float,
                             help=('Specifying the z coordinate explicitly [mm].'
                                   ' If none is given the current gantry '
                                   'position will be used instead'))

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_xydet_options(args)
    if not args.z: args.z = self.gcoder.opz
    return args

  def run(self, args):
    self.move_gantry(args.x, args.y, args.z, True)


class movespeed(cmdbase.controlcmd):
  """
  Setting the motion speed of the gantry x-y-z motors. Units in mm/s.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('-x',
                             type=float,
                             help='motion speed of gantry in x axis ')
    self.parser.add_argument('-y',
                             type=float,
                             help='motion speed of gantry in y axis ')
    self.parser.add_argument('-z',
                             type=float,
                             help='motion speed of gantry in z axis ')

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    # Filling with NAN for missing settings.
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

  def run(self, args):
    self.gcoder.sendhome()


class halign(cmdbase.controlcmd):
  """
  Running horizontal alignment procedure by luminosity readout v.s. x-y motion
  scanning. Notice that when running with the picoscope, the only the number of
  captures to perform the average/spread calculation can be adjusted directly in
  this command. For the other options such as the integration window, the voltage
  range... etc. You will still need the picoset command.
  """

  DEFAULT_SAVEFILE = 'halign_<BOARDTYPE>_<BOARDID>_<DETID>_<SCANZ>_<TIMESTAMP>.txt'
  LOG = log.GREEN('[LUMI ALIGN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.add_hscan_options(hrange=20, distance=1)
    self.add_savefile_options(halign.DEFAULT_SAVEFILE)
    self.parser.add_argument('--overwrite',
                             action='store_true',
                             help=('Forcing the storage of scan results as '
                                   'session information'))
    self.parser.add_argument('--power',
                             '-p',
                             type=float,
                             help=('PWM duty cycle for data collection, using '
                                   'current value if not specified'))

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_xydet_options(args)
    self.parse_readout_options(args)
    self.parse_savefile(args)
    if not args.power:
      args.power = self.gpio.pwm_duty(0)  ## Getting the PWM value
    return args

  def run(self, args):
    x, y = self.make_hscan_mesh(args)
    lumi = []
    unc = []
    total = len(x)

    self.gpio.pwm(0, args.power, 1e5)  # Maximum PWM frequency

    ## Running over mesh.
    for idx, (xval, yval) in enumerate(zip(x, y)):
      self.check_handle(args)
      self.move_gantry(xval, yval, args.scanz, False)
      lumival, uncval = self.readout.read(channel=args.channel,
                                          samples=args.samples,
                                          average=True)
      self.update_luminosity(lumival,
                             uncval,
                             Progress=(idx + 1, total),
                             Temperature=True)
      lumi.append(abs(lumival))
      unc.append(uncval)
      ## Writing to file
      args.savefile.write(
          self.make_standard_line((lumival, uncval), det_id=args.detid))
      args.savefile.flush()

    self.close_savefile(args)

    # Performing fit
    p0 = (max(lumi) * (args.scanz**2), args.x, args.y, args.scanz, min(lumi))
    try:
      fitval, fitcovar = curve_fit(halign.model,
                                   np.vstack((x, y)),
                                   lumi,
                                   p0=p0,
                                   sigma=unc,
                                   maxfev=1000000)
    except Exception as err:
      self.printerr(('Lumi fit failed to converge, check output stored in file '
                     '{0} for collected values').format(args.savefile.name))
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
      self.board.add_calib_det(detid)

    ## Saving session information
    if not self.board.lumi_coord_hasz(detid, args.scanz) or args.overwrite:
      self.board.add_lumi_coord(detid, args.scanz, [
          fitval[1],
          np.sqrt(fitcovar[1][1]), fitval[2],
          np.sqrt(fitcovar[1][1])
      ])
    elif self.board.lumi_coord_hasz(detid, args.scanz):
      if self.cmd.prompt_yn(
          str('A lumi alignment for z={0:.1f} already exists for the current session, overwrite?'
              .format(args.scanz))):
        self.board.add_lumi_coord(detid, args.scanz, [
            fitval[1],
            np.sqrt(fitcovar[1][1]), fitval[2],
            np.sqrt(fitcovar[1][1])
        ])

    ## Sending gantry to position
    self.move_gantry(fitval[1], fitval[2], args.scanz, True)

  @staticmethod
  def model(xydata, N, x0, y0, z, p):
    x, y = xydata
    D = (x - x0)**2 + (y - y0)**2 + z**2
    return (N * z / D**1.5) + p


class zscan(cmdbase.controlcmd):
  """
  Performing z scanning at a certain x-y coordinate
  """

  DEFAULT_SAVEFILE = 'zscan_<BOARDTYPE>_<BOARDID>_<DETID>_<TIMESTAMP>.txt'
  LOG = log.GREEN('[LUMI ZSCAN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.add_zscan_options()
    self.add_savefile_options(zscan.DEFAULT_SAVEFILE)
    self.parser.add_argument('--power',
                             '-p',
                             nargs='*',
                             type=float,
                             help=('Give a list of pwm duty cycle values to '
                                   'try for each coordinate point'))

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_xydet_options(args)
    self.parse_zscan_options(args)
    self.parse_readout_options(args)
    self.parse_savefile(args)
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
          lumival, uncval = self.readout.read(channel=args.channel,
                                              samples=args.samples)
          if self.readout.mode == self.readout.MODE_PICO:
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

        # Writing to screen
        self.update_luminosity(lumival,
                               uncval,
                               Progress=(idx, len(args.zlist)),
                               Temperature=True)
        # Writing to file
        args.savefile.write(
            self.make_standard_line((lumival, uncval), det_id=args.detid))
        args.savefile.flush()

    self.close_savefile(args)


class lowlightcollect(cmdbase.controlcmd):
  """
  Collection of low light data at a single gantry position, collecting data as
  fast as possible no waiting.
  """
  DEFAULT_SAVEFILE = 'lowlight_<BOARDTYPE>_<BOARDID>_<DETID>_<TIMESTAMP>.txt'
  LOG = log.GREEN('[LUMI LOWLIGHT]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.add_zscan_options()
    self.add_savefile_options(lowlightcollect.DEFAULT_SAVEFILE)
    self.parser.add_argument('--power',
                             '-p',
                             type=float,
                             help=('PWM duty cycle for data collection, using '
                                   'current value if not specified'))

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_xydet_options(args)
    self.parse_zscan_options(args)
    self.parse_readout_options(args)
    self.parse_savefile(args)
    if not args.power:
      args.power = self.gpio.pwm_duty(0)
    if len(args.zlist) != 1:
      raise Exception("This functions accepts exactly 1 z-value.")

    return args

  def run(self, args):
    self.move_gantry(args.x, args.y, args.zlist[0], False)
    self.gpio.pwm(0, args.power, 1e5)
    nparts = int(args.samples / 1000) + 1
    for i in range(nparts):
      self.check_handle(args)
      ## Collecting data in 1000 sample bunchs for better monitoring
      readout = self.readout.read(channel=args.channel,
                                  samples=1000,
                                  average=False)
      args.savefile.write(self.make_standard_line(readout, det_id=args.detid))
      args.savefile.flush()
      self.update_luminosity(readout[-1],
                             readout[-2],
                             data_tag='Latest',
                             Progress=(i, nparts),
                             Temperature=True)
    self.close_savefile(args)


class timescan(cmdbase.controlcmd):
  """
  Generate a log of the readout in terms relative to time.
  """
  DEFAULT_SAVEFILE = 'tscan_<TIMESTAMP>.txt'
  LOG = log.GREEN('[TIMESCAN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.add_readout_option()
    self.add_savefile_options(timescan.DEFAULT_SAVEFILE)
    self.parser.add_argument('--nslice',
                             type=int,
                             default=30,
                             help='total number of sample to take')
    self.parser.add_argument('--interval',
                             type=int,
                             default=1,
                             help='Time interval between sampling (seconds)')
    self.parser.add_argument('--testpwm',
                             type=float,
                             nargs='*',
                             help=('PWM duty cycle values to cycle through '
                                   'while performing test'))
    self.parser.add_argument('--pwmslices',
                             type=int,
                             default=10,
                             help=('Number of time slices to take for a given '
                                   'PWM test value'))

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_readout_options(args)
    self.parse_savefile(args)
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

      lumival, uncval = self.readout.read(channel=args.channel,
                                          samples=args.samples)
      sample_time = time.time_ns()
      timestamp = (sample_time - start_time) / 1e9
      args.savefile.write(
          self.make_standard_line((lumival, uncval), det_id=-100,
                                  time=timestamp))
      args.savefile.flush()
      self.update_luminosity(lumival,
                             uncval,
                             Progress=(i + 1, args.nslice),
                             Temperature=True)
      time.sleep(args.interval)

    self.close_savefile(args)


class showreadout(cmdbase.controlcmd):
  """
  Continuously display ADC readout
  """

  LOG = log.GREEN('[READOUT]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.add_readout_option()
    self.parser.add_argument('--dumpval',
                             action='store_true',
                             help='Dump the entire sequence of collected data')
    self.parser.add_argument('--nowait',
                             action='store_true',
                             help=('Whether or not to perform the random wait '
                                   'process for ADC data collection'))

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_readout_options(args)
    return args

  def run(self, args):
    val = []

    for i in range(1000):
      self.check_handle(args)

      val.append(self.readout.read_adc_raw(0))
      self.update('{0} | {1} | {2} | {3}'.format(
          'Latest: {0:10.5f}'.format(val[-1]), 'Mean: {0:10.5f}'.format(
              np.mean(val)), 'STD: {0:11.6f}'.format(np.std(val)),
          'PROGRESS [{0:3d}/1000]'.format(i + 1)))
      if args.nowait:
        continue
      time.sleep(1 / 50 * np.random.random())  ## Sleeping for random time
    meanval = np.mean(val)
    stdval = np.std(val)
    valstrip = [x for x in val if abs(x - meanval) < stdval]
    self.printmsg('RAWVAL | Mean: {0:.5f} | STD: {1:.6f}'.format(
        np.mean(val), np.std(val)))
    self.printmsg('Update | Mean: {0:.5f} | STD: {1:.6f}'.format(
        np.mean(valstrip), np.std(valstrip)))
    if args.dumpval:
      for v in val:
        print(v)
