import python.cmdbase as cmdbase
import python.gcoder as gcoder
import python.logger as logger
import argparse
import numpy as np
import time
from scipy.optimize import curve_fit


class moveto(cmdbase.controlcmd):
  """
  Moving the gantry head to a specific location, either by chip ID or by raw
  x-y-z coordinates. Units for the x-y-z inputs is millimeters.
  """

  def __init__(self):
    cmdbase.controlcmd.__init__(self)
    self.parser.add_argument(
        "-x",
        type=float,
        help="Specifying the X coordinate (remains unchanged if not specificed)")
    self.parser.add_argument(
        "-y",
        type=float,
        help="Specifying the Y coordinate (remains unchanged if not specificed)")
    self.parser.add_argument(
        '-chip',
        type=int,
        help=
        "Moving to the specific chip location on the present board layout, overrides the settings given by the x,y settings"
    )
    self.parser.add_argument(
        "-z",
        type=float,
        help=
        "Specifying the Z coordinate (remains unchanged if not specificed). Can be used together with -chip options"
    )

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)

    if arg.chip:
      if not self.cmd.board.has_chip(arg.chip):
        print(
            """Warning chip of ID is not defined in board type! Not using chip ID to change target position"""
        )
        self.cmd.board.opchip = -1
      else:
        if arg.x or arg.y:
          print("Warning! Overriding user defined x,y with chip coordinates!")
      arg.x = self.cmd.board.get_chip_x(arg.chip)
      arg.y = self.cmd.board.get_chip_y(arg.chip)
      self.cmd.board.opchip = arg.chip
      arg.__delattr__('chip')
    else:
      self.cmd.board.opchip = -1

    ## Filling with NAN for no motion.
    if arg.x == None: arg.x = float('nan')
    if arg.y == None: arg.y = float('nan')
    if arg.z == None: arg.z = float('nan')
    if arg.x != arg.x and arg.y != arg.y and arg.z != arg.z:
      raise Exception("No coordinate specified! exiting command.")

    return arg

  def run(self, arg):
    self.cmd.gcoder.moveto(arg.x, arg.y, arg.z, True)


class movespeed(cmdbase.controlcmd):
  """
  Setting the motion speed of the gantry x-y-z motors. Units in mm/s.
  """

  def __init__(self):
    cmdbase.controlcmd.__init__(self)
    self.parser.add_argument(
        '-x', type=float, help='motion speed of gantry in x axis ')
    self.parser.add_argument(
        '-y', type=float, help='motion speed of gantry in y axis ')
    self.parser.add_argument(
        '-z', type=float, help='motion speed of gantry in z axis ')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    # Filling with NAN for missing settings.
    if not arg.x: arg.x = float('nan')
    if not arg.y: arg.y = float('nan')
    if not arg.z: arg.z = float('nan')

    return arg

  def run(self, arg):
    self.cmd.gcoder.set_speed_limit(arg.x, arg.y, arg.z, True)


class halign(cmdbase.controlcmd):
  """
  Running horizontal alignment procedure by luminosity readout v.s. x-y motion
  scanning
  """
  hmin = 1
  hmax = 400

  def __init__(self):
    cmdbase.controlcmd.__init__(self)
    self.parser.add_argument(
        '-x', type=float, help="Guestimation of x position of photosensor [mm]")
    self.parser.add_argument(
        '-y', type=float, help="Guestimation of y position of photosensor [mm]")
    self.parser.add_argument(
        '-r',
        type=float,
        default=20,
        help="Range to perform x-y scanning from central position [mm]")
    self.parser.add_argument(
        '-z',
        type=float,
        default=100,
        help="Height to perform horizontal scan at")
    self.parser.add_argument(
        '-d', type=float, default=0.5, help='Horizontal sampling seperation')
    self.parser.add_argument(
        '-f',
        type=argparse.FileType('w'),
        help='Writing x-y scan results to file')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    if not arg.x:
      raise Exception("Need to specify initial x position")
    if not arg.y:
      raise Exception("Need to specify initial y position")
    if ((arg.x - arg.r < halign.hmin) or (arg.x + arg.r > halign.hmax)
        or (arg.y - arg.r < halign.hmin) or (arg.y + arg.r > halign.hmax)):
      logger.printwarn(
          ("The arguments placed will put the gantry past it's limits, "
           "the command will used modified input parameters"))
    if arg.z < 100:
      logger.printwarn(
          ("The vertical position might not put the photosensor within "
           "the field of vision of the camera, camera calibration might fail!"))
    return arg

  def run(self, arg):
    x, y = halign.make_xy_mesh(arg)
    lumi = []
    unc = []

    ## Running over mesh.
    for xval, yval in zip(x, y):
      try:
        # Try to move the gantry. Even if it fails there will be fail safes
        # in other classes
        self.cmd.gcoder.moveto(x, y, arg.z, False)
      except:
        pass
      lumival, uncval = self.cmd.readout.read_adc()
      lumi.append(lumival)
      unc.append(uncval)

      logger.update(
          logger.GREEN("[ALIGN]"),
          "x:{0:.1f}, y:{1:.1f}, z:{2:.1f}, L:{3:.2f}, uL:{4:.3f}".format(
              xval, yval, arg.z, lumival, uncval))
    logger.clear_update()

    ## Flushing contents to file
    if arg.f:
      for xval, yval, lumival, uncval in zip(x, y, lumi, unc):
        arg.f.write("{0:.1f} {1:.1f} {2:.1f} {3:.2f} {4:.3f}\n".format(
            xval, yval, arg.z, lumival, uncval))
      arg.f.close()

    # Performing fit
    targetx = np.mean(arg.x)
    targety = np.mean(arg.y)
    p0 = (max(lumi) * (arg.z**2), arg.x, arg.y, arg.z, min(lumi))
    try:
      fitval, fitcorr = curve_fit(
          halign.model, np.vstack((x, y)), lumi, p0=p0, sigma=unc, maxfev=10000)

      logger.printmsg(
          logger.GREEN("[ALIGN]"), "Best x:{0:.2f}+-{1:.3f}".format(
              fitval[1], np.sqrt(fitcorr[1][1])))
      logger.printmsg(
          logger.GREEN("[ALIGN]"), "Best y:{0:.2f}+-{1:.3f}".format(
              fitval[2], np.sqrt(fitcorr[2][2])))
      logger.printmsg(
          logger.GREEN("[ALIGN]"), "Fit  z:{0:.2f}+-{1:.3f}".format(
              fitval[3], np.sqrt(fitcorr[3][3])))

      self.cmd.session.halign_xval[arg.z] = fitval[1]
      self.cmd.session.halign_xunc[arg.z] = np.sqrt(fitcorr[1][1])
      self.cmd.session.halign_yval[arg.z] = fitval[2]
      self.cmd.session.halign_yunc[arg.z] = np.sqrt(fitcorr[1][1])
      targetx = fitval[1]
      targety = fitval[2]
    except Exception as err:
      logger.printerr("Fit Failed to converge! Check for bad output in file!")

    ## Sending gantry to position
    self.cmd.gcoder.move_to_position(targetx, targety, arg.z, True)

  def model(xydata, N, x0, y0, z, p):
    x, y = xydata
    D = (x - x0)**2 + (y - y0)**2 + z**2
    return (N * z / D**1.5) + p

  def make_xy_mesh(arg):
    xmin = max([arg.x - arg.r, halign.hmin])
    xmax = min([arg.x + arg.r, halign.hmax])
    ymin = max([arg.y - arg.r, halign.hmin])
    ymax = min([arg.y + arg.r, halign.hmax])
    sep = max([arg.d, 0.5])
    xmesh, ymesh = np.meshgrid(
        np.linspace(xmin, xmax, (xmax - xmin) / arg.d + 1),
        np.linspace(ymin, ymax, (ymax - ymin) / arg.d + 1))
    return [
        xmesh.reshape(1, np.prod(xmesh.shape))[0],
        ymesh.reshape(1, np.prod(ymesh.shape))[0]
    ]


class zscan(cmdbase.controlcmd):
  """
  Performing z scanning at a certain x-y coordinate
  """

  def __init__(self):
    cmdbase.controlcmd.__init__(self)
    self.parser.add_argument(
        '-x', type=float, help='specifying the x coordinate explicitly [mm]')
    self.parser.add_argument(
        '-y', type=float, help='specify the y coordinate explicitly [mm]')
    self.parser.add_argument(
        '-calibz',
        type=float,
        help='specifying the x-y coordinates via some calibration z position')
    self.parser.add_argument(
        '-zmin',
        type=float,
        default=10,
        help='minimum value to begin z scan [mm]')
    self.parser.add_argument(
        '-zmax',
        type=float,
        default=450,
        help='maximum value to end z scan [mm]')
    self.parser.add_argument(
        '-zsep', type=float, default=5, help='z scanning seperation [mm]')
    self.parser.add_argument(
        '-f', type=argparse.FileType('w'), help='Writing results to some file')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    if arg.calibz:
      if (arg.x or arg.y):
        raise Exception('You can either specify calibz or xy, not both!')
      if not cmd.session.halign_xval[arg.calibz]:
        raise Exception(
            'Calibration value not found! Please run halign command first')
      arg.x = self.cmd.session.halign_xval[arg.calibz]
      arg.y = self.cmd.session.halign_yval[arg.calibz]

    if not (arg.x and arg.y):
      raise Exception('Please specify both x and y coordinates')

    return arg

  def run(self, arg):
    zlist = np.linspace(arg.zmin, arg.zmax, (arg.zmax - arg.zmin) / arg.zsep + 1)
    lumi = []
    unc = []

    for z in zlist:
      try:
        # Try to move the gantry regardless, there are fail safe for
        # readout errors
        self.cmd.gcoder.moveto(arg.x, arg.y, z, False)
      except:
        pass

      lumival, uncval = self.readout.read_adc(sample=100)
      lumi.append( lumival )
      unc.append( uncval )

      logger.update( logger.GREEN("[ZSCAN]"),
        "z:{0:.1f}, L:{1:.2f}, uL:{2:.3f}".format(
          z, lumival, uncval ) )
    logger.clear_update()

    if arg.f:
      for z,lumival,uncval in zip(zlist,lumi,unc):
        arg.f.write("{0:.1f} {1:.1f} {2:.1f} {3:.2f} {4:.3f}\n".format(
            arg.x, arg.y, z, lumival, uncval))
    else:
      logger.printmsg( logger.GREEN("[ZSCAN]"),
        "{0:.1f} {1:.1f} {2:.1f} {3:.2f} {4:.3f}\n".format(
            arg.x, arg.y, z, lumival, uncval) )


class showreadout(cmdbase.controlcmd):
  """
  Continuously display ADC readout
  """

  def __init__(self):
    cmdbase.controlcmd.__init__(self)

  def parse(self, line):
    return cmdbase.controlcmd.parse(self, line)

  def run(self, arg):
    val = []
    for i in range(1000):
      val.append(self.adc.read_adc_raw(0))
      logger.update( logger.GREEN("[READOUT]"),
          "{0:6d} {1:.2f} {2:.3f}".format(val[-1], np.mean(val), np.std(val)))
    logger.clear_update()


class findchip(cmdbase.controlcmd):
  """
  Finding the absolute chip position closest to current position of the gantry
  """

  def __init__(self):
    cmdbase.controlcmd.__init__(self)

  def parse(self, line):
    return cmdbase.controlcmd.parse(self, line)

  def run(self, arg):
    self.cmd.visual.find_chip()


class fscan(cmdbase.controlcmd):
  """
  Scanning focus to calibrate z distance
  """

  def __init__(self):
    cmdbase.controlcmd.__init__(self)

  def parse(self, line):
    return cmdbase.controlcmd.parse(self, line)

  def run(self, arg):
    self.cmd.visual.scan_focus()
