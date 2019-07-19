import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
import cmod.comarg as comarg
import numpy as np
from scipy.optimize import curve_fit
import time

class moveto(cmdbase.controlcmd):
  """
  Moving the gantry head to a specific location, either by chip ID or by raw
  x-y-z coordinates. Units for the x-y-z inputs is millimeters.
  """

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    comarg.add_xychip_options(self.parser)
    self.parser.add_argument(
        '-z',
        type=float,
        help=
        'Specifying the x coordinate explicitly [mm]. If none is given the current gantry position will be used instead'
    )

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    comarg.parse_xychip_options(arg, self.cmd)
    if not arg.z: arg.z = self.gcoder.opz
    return arg

  def run(self, arg):
    self.gcoder.moveto(arg.x, arg.y, arg.z, True)


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
    arg = cmdbase.controlcmd.parse(self, line)
    # Filling with NAN for missing settings.
    if not arg.x: arg.x = float('nan')
    if not arg.y: arg.y = float('nan')
    if not arg.z: arg.z = float('nan')

    return arg

  def run(self, arg):
    self.gcoder.set_speed_limit(arg.x, arg.y, arg.z)


class halign(cmdbase.controlcmd):
  """
  Running horizontal alignment procedure by luminosity readout v.s. x-y motion
  scanning
  """

  DEFAULT_SAVEFILE = 'halign_<ZVAL>_<TIMESTAMP>.txt'
  LOG = log.GREEN('[LUMI ALIGN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    comarg.add_hscan_options(self.parser, hrange=20, distance=1)
    comarg.add_savefile_options(self.parser, halign.DEFAULT_SAVEFILE)
    self.parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Forcing the storage of scan results as session information')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)

    comarg.parse_xychip_options(arg, self.cmd)

    filename = arg.savefile if arg.savefile != halign.DEFAULT_SAVEFILE \
               else comarg.timestamp_filename( 'halign', arg, ['scanz'] )
    arg.savefile = self.sshfiler.remotefile(filename, arg.wipefile)

    return arg

  def run(self, arg):
    x, y = comarg.make_hscan_mesh(arg)
    lumi = []
    unc = []

    ## Running over mesh.
    for xval, yval in zip(x, y):
      try:
        # Try to move the gantry. Even if it fails there will be fail safes
        # in other classes
        self.gcoder.moveto(xval, yval, arg.scanz, False)
      except:
        pass
      lumival, uncval = self.readout.read_adc()
      lumi.append(lumival)
      unc.append(uncval)

      ## Writing to screen
      self.update(
          'x:{0:5.1f}, y:{1:5.1f}, z:{2:5.1f}, Lumi:{3:8.5f}+-{4:8.6f}'.format(
              xval, yval, arg.scanz, lumival, uncval))

      ## Writing to file
      arg.savefile.write("{0:5.1f} {1:5.1f} {2:5.1f} {3:8.5f} {4:8.6f}\n".format(
          xval, yval, arg.scanz, lumival, uncval))

    ## Clearing output objects
    arg.savefile.close()

    # Performing fit
    p0 = (max(lumi) * (arg.scanz**2), arg.x, arg.y, arg.scanz, min(lumi))
    try:
      fitval, fitcorr = curve_fit(halign.model,
                                  np.vstack((x, y)),
                                  lumi,
                                  p0=p0,
                                  sigma=unc,
                                  maxfev=10000)
    except Exception as err:
      self.printerr(('Lumi fit failed to converge, check output stored in file '
                     '%s for collected values').format(arg.savefile.name))
      self.gcoder.moveto(arg.x, arg.y, arg.scanz, False)
      raise err

    self.printmsg("Best x:{0:.2f}+-{1:.3f}".format(fitval[1],
                                                   np.sqrt(fitcorr[1][1])))
    self.printmsg("Best y:{0:.2f}+-{1:.3f}".format(fitval[2],
                                                   np.sqrt(fitcorr[2][2])))
    self.printmsg("Fit  z:{0:.2f}+-{1:.3f}".format(fitval[3],
                                                   np.sqrt(fitcorr[3][3])))

    ## Saving session information
    if (not arg.scanz in self.board.lumi_coord[arg.chipid] or arg.overwrite):
      self.board.lumi_coord[arg.chipid][arg.scanz] = [
          fitval[1],
          np.sqrt(fitcorr[1][1]), fitval[2],
          np.sqrt(fitcorr[1][1])
      ]
    elif arg.scanz in self.board.lumi_coord[arg.chipid]:
      if comarg.prompt(
          'A lumi alignment for z={0:.1f} already exists for the current session, overwrite?'
          .format(targetz)):
        self.board.lumi_coord[arg.chipid][arg.scanz] = [
            fitval[1],
            np.sqrt(fitcorr[1][1]), fitval[2],
            np.sqrt(fitcorr[1][1])
        ]

    ## Sending gantry to position
    self.gcoder.moveto(fitval[1], fitval[2], arg.scanz, True)

  @staticmethod
  def model(xydata, N, x0, y0, z, p):
    x, y = xydata
    D = (x - x0)**2 + (y - y0)**2 + z**2
    return (N * z / D**1.5) + p


class zscan(cmdbase.controlcmd):
  """
  Performing z scanning at a certain x-y coordinate
  """

  DEFAULT_SAVEFILE = "zscan_<CHIP>_<TIMESTAMP>.txt"
  LOG = log.GREEN('[LUMI ZSCAN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    comarg.add_zscan_options(self.parser)
    comarg.add_savefile_options(self.parser, zscan.DEFAULT_SAVEFILE)

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    comarg.parse_xychip_options(arg, self.cmd)
    comarg.parse_zscan_options(arg)

    filename = arg.savefile if arg.savefile != zscan.DEFAULT_SAVEFILE  \
               else comarg.timestamp_filename('zscan', arg )
    arg.savefile = self.sshfiler.remotefile(filename, arg.wipefile)

    return arg

  def run(self, arg):
    lumi = []
    unc = []

    for z in arg.zlist:
      try:
        # Try to move the gantry regardless, there are fail safe for
        # readout errors
        self.gcoder.moveto(arg.x, arg.y, z, False)
      except:
        pass

      lumival, uncval = self.readout.read_adc(sample=100)
      lumi.append(lumival)
      unc.append(uncval)

      # Writing to screen
      self.update("z:{0:5.1f}, L:{1:8.5f}, uL:{2:8.6f}".format(
          z, lumival, uncval))
      # Writing to file
      arg.savefile.write(
          "{0:5.1f} {1:5.1f} {2:5.1f} {3:8.5f} {4:8.6f}\n".format(
          arg.x, arg.y, z, lumival, uncval))

    arg.savefile.close()


class showreadout(cmdbase.controlcmd):
  """
  Continuously display ADC readout
  """

  LOG = log.GREEN('[READOUT]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    comarg.add_readout_option( self.parser )
    self.parser.add_argument('--dumpval', action='store_true')
    self.parser.add_argument('--nowait', action='store_true')

  def parse(self, line):
    return cmdbase.controlcmd.parse(self, line)

  def run(self, arg):
    val = []

    #for i in range(10):  ## Ignoring first 10 ouptuts
    #self.readout.read_adc_raw(0)

    for i in range(1000):
      val.append(self.readout.read_adc_raw(0))
      self.update("Latest: {0:.5f} | Mean: {1:.5f} | STD: {2:.6f}".format(
          val[-1], np.mean(val), np.std(val)))
      if arg.nowait: continue
      time.sleep(1 / 50 * np.random.random())  ## Sleeping for random time
    meanval = np.mean(val)
    stdval = np.std(val)
    valstrip = [x for x in val if abs(x - meanval) < stdval]
    self.printmsg("RAWVAL | Mean: {0:.5f} | STD: {1:.6f}".format(
        np.mean(val), np.std(val)))
    self.printmsg("Update | Mean: {0:.5f} | STD: {1:.6f}".format(
        np.mean(valstrip), np.std(valstrip)))
    if arg.dumpval:
      for v in val:
        print(v)
