import ctlcmd.cmdbase as cmdbase
import ctlcmd.motioncmd as motioncmd
import cmod.gcoder as gcoder
import cmod.logger as logger
import numpy as np
from scipy.optimize import curve_fit
import argparse
import time
import datetime
import cv2


class visualhscan(cmdbase.controlcmd):
  """
  Performing horizontal scan with camera system
  """

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument(
        '-x',
        '--guessx',
        type=float,
        help="Guesstimate of x position of photosensor [mm]")
    self.parser.add_argument(
        '-y',
        '--guessy',
        type=float,
        help="Guesstimate of y position of photosensor [mm]")
    self.parser.add_argument(
        '-z', '--scanz',
        type=float,
        default=30,
        help="Height to perform horizontal scan at")
    self.parser.add_argument(
        '-r', '--range',
        type=float,
        default=3,
        help="Range to perform x-y scanning from central position [mm]")
    self.parser.add_argument(
        '-d', '--h-distance'
         type=float, default=0.5, help='Horizontal sampling seperation')
    self.parser.add_argument(
        '-m', '--monitor',
        action='store_true',
        help='Whether or not to open the monitoring window (could be slow!!)')
    self.parser.add_argument(
        '-f', '--savefile'
        type=str,
        default='vhscan_<ZVAL>_<TIMESTAMP>.txt',
        help='Writing x-y scan results to file')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    if not arg.x:
      arg.x = self.cmd.gcoder.opx
    if not arg.y:
      arg.y = self.cmd.gcoder.opy
    if ((arg.x - arg.r < motioncmd.halign.hmin)
        or (arg.x + arg.r > motioncmd.halign.hmax)
        or (arg.y - arg.r < motioncmd.halign.hmin)
        or (arg.y + arg.r > motioncmd.halign.hmax)):
      logger.printwarn(
          ("The arguments placed will put the gantry past it's limits, "
           "the command will used modified input parameters"))

    if arg.f == 'vhscan_<ZVAL>_<TIMESTAMP>.txt':
      arg.f = self.cmd.sshfiler.remotefile('vhscan_z{0}_{1}.txt'.format(
          arg.z,
          datetime.datetime.now().strftime('%Y%m%d_%H00')))
    else:
      arg.f = self.cmd.sshfiler.remotefile(arg.f)

    return arg

  def run(self, arg):
    x, y = motioncmd.halign.make_xy_mesh(arg)
    ganx = []
    gany = []
    recox = []
    recoy = []

    ## Running over mesh.
    for xval, yval in zip(x, y):
      try:
        # Try to move the gantry. Even if it fails there will be fail safes
        # in other classes
        self.cmd.gcoder.moveto(xval, yval, arg.z, False)
      except:
        pass

      center = self.cmd.visual.find_chip(arg.m)

      if center.x > 0 and center.y > 0:
        ganx.append(xval)
        gany.append(yval)
        recox.append(center.x)
        recoy.append(center.y)

      logger.update(
          logger.GREEN("[VHSCAN]"),
          "x:{0:.1f}, y:{1:.1f}, z:{2:.1f}, Found x:{3:.1f} Found y: {4:.1f}".
          format(xval, yval, arg.z, center.x, center.y))
      arg.f.write("{0:.1f} {1:.1f} {2:.1f} {3:.2f} {4:.3f}\n".format(
          xval, yval, arg.z, center.x, center.y))

    logger.flush_update()
    cv2.destroyAllWindows()
    arg.f.close()

    fitx, corrx = curve_fit(visualhscan.model, np.vstack((ganx, gany)), recox)
    fity, corry = curve_fit(visualhscan.model, np.vstack((ganx, gany)), recoy)

    logger.printmsg(
        logger.GREEN("[ALIGN]"), "Transformation for CamX " \
          "= ({0:.2f}+-{1:.3f})x + ({2:.2f}+-{3:.2f})y".format(
              fitx[0], np.sqrt(corrx[0][0]),
              fitx[1], np.sqrt(corrx[1][1])  ) )
    logger.printmsg(
        logger.GREEN("[ALIGN]"), "Transformation for CamY " \
          "= ({0:.2f}+-{1:.3f})x + ({2:.2f}+-{3:.2f})y".format(
              fity[0], np.sqrt(corry[0][0]),
              fity[1], np.sqrt(corry[1][1])  ) )

    ## Saving rounded coordinates
    self.cmd.session.camT[self.cmd.gcoder.opz] = np.array([[fitx[0], fitx[1]],
                                                           [fity[0], fity[1]]])
    ## Moving back to center
    self.cmd.gcoder.moveto(arg.x, arg.y, arg.z, False)

  def model(xydata, a, b, c):
    x, y = xydata
    return a * x + b * y + c


class visualcenterchip(cmdbase.controlcmd):
  """
  Moving the gantry so that the chip is in the center of the field of view
  """

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument(
        '-x',
        type=float,
        help=
        'Position x to being centering, User must be sure to keep one chip in the field of view using present coordinates if not specified'
    )
    self.parser.add_argument(
        '-y',
        type=float,
        help=
        'Position y to being centering, User must be sure to keep one chip in the field of view using present coordinates if not specified'
    )
    self.parser.add_argument(
        '-z',
        type=float,
        help=
        'Position z to perform centering. User must make sure the callibration vectors have already been created before'
    )

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    if not arg.x:
      arg.x = self.cmd.gcoder.opx
    if not arg.y:
      arg.y = self.cmd.gcoder.opy
    if not arg.z:
      arg.z = self.cmd.gcoder.opz
    if not arg.z in self.cmd.session.camT:
      logger.printerr(
          'Motion transformation equation was not found for position z={0:.2f}mm, please run command [visualhscan] first'
          .format(arg.z))
      logger.printerr("Available coordinates:" + str(self.cmd.session.camT))
      raise Exception('Transformation equation not found')
    return arg

  def run(self, arg):
    self.cmd.gcoder.moveto(arg.x, arg.y, arg.z, False)
    for movetime in range(10):  ## Maximum of 10 movements
      center = None

      ## Try to find center for a maximum of 3 times
      for findtime in range(3):
        center = self.cmd.visual.find_chip(False)
        if center.x > 0:
          break
      ## Early exit if chip is not found.
      if (center.x < 0 or center.y < 0):
        raise Exception("Chip lost! Move to center again")

      deltaxy = np.array([
          self.cmd.visual.frame_width() / 2 - center.x,
          self.cmd.visual.frame_height() / 2 - center.y
      ])

      motionxy = np.linalg.solve(self.cmd.session.camT[self.cmd.gcoder.opz],
                                 deltaxy)

      ## Early exit if difference from center is small
      if np.linalg.norm(motionxy) < 0.1: break

      self.cmd.gcoder.moveto(self.cmd.gcoder.opx + motionxy[0],
                             self.cmd.gcoder.opy + motionxy[1],
                             self.cmd.gcoder.opz, False)
      time.sleep(0.1)  ## Waiting for the gantry to stop moving

    center = self.cmd.visual.find_chip(False)
    logger.printmsg(
        logger.GREEN("[VCENTER]"),
        "Gantry position: x={0:.1f} y={1:.1f} | Chip FOV position: x={2} y={3}".
        format(self.cmd.gcoder.opx, self.cmd.gcoder.opy, center.x, center.y))

    if self.cmd.gcoder.opz not in self.cmd.session.vis_halign_x:
      self.cmd.session.vis_halign_x[self.cmd.gcoder.opz] = self.cmd.gcoder.opx
      self.cmd.session.vis_halign_y[self.cmd.gcoder.opz] = self.cmd.gcoder.opy
    elif self.cmd.gcoder.opz not in self.cmd.session.lumi_halign_x:
      deltax = self.cmd.session.vis_halign_x[
          self.cmd.gcoder.opz] - self.cmd.session.lumi_halign_x[
              self.cmd.gcoder.opz]
      deltay = self.cmd.session.vis_halign_y[
          self.cmd.gcoder.opz] - self.cmd.session.lumi_halign_y[
              self.cmd.gcoder.opz]

      logger.printmsg(
          logger.GREEN("[VCENTER]"), "Estimated Lumi center: x={0} y={1}".format(
              self.cmd.gcoder.opx - deltax, self.cmd.gcoder.opy - deltay))


class visualmaxsharp(cmdbase.controlcmd):
  """
  Moving the gantry so that the image sharpness is maximized
  """

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument(
        '-x', type=float, help='specifying the x coordinate explicitly [mm]')
    self.parser.add_argument(
        '-y', type=float, help='specify the y coordinate explicitly [mm]')
    self.parser.add_argument(
        '-zinit',
        type=float,
        default=30,
        help='Initial value to begin finding optimal z value [mm]')
    self.parser.add_argument(
        '-stepinit',
        type=float,
        default=1,
        help='Step size to scan for immediate neighborhood z scan [mm]')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    if not arg.x:
      arg.x = self.cmd.gcoder.opx
    if not arg.y:
      arg.y = self.cmd.gcoder.opy
    return arg

  def run(self, arg):
    self.cmd.gcoder.moveto(arg.x, arg.y, arg.zinit, False)
    laplace = self.cmd.visual.sharpness(False)
    zval = arg.zinit
    zstep = arg.stepinit

    while abs(zstep) >= 0.1:
      self.cmd.gcoder.moveto(arg.x, arg.y, zval + zstep, False)
      newlap = self.cmd.visual.sharpness(False)

      if newlap > laplace:
        laplace = newlap
        zval += zstep
      else:
        zstep *= -0.5
      logger.update(
          logger.GREEN("[MAX-SHARP]"), "z:{0:.1f}, L:{1:.2f}".format(
              zval, laplace))
    logger.flush_update()
    logger.update(
        logger.GREEN("[MAX-SHARP]"),
        "Final z:{0:.1f}".format(self.cmd.gcoder.opz))


class visualzscan(cmdbase.controlcmd):
  """
  Scanning focus to calibrate z distance
  """

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
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
        '-zmax', type=float, default=50, help='maximum value to end z scan [mm]')
    self.parser.add_argument(
        '-zsep', type=float, default=1, help='z scanning seperation [mm]')
    self.parser.add_argument(
        '-m',
        action='store_true',
        help='Whether or not to open the monitoring window (could be slow!!)')
    self.parser.add_argument(
        '-f',
        type=str,
        default='vzscan_<TIMESTAMP>.txt',
        help='Writing results to some file')

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

    if arg.f == 'vzscan_<TIMESTAMP>.txt':
      arg.f = self.cmd.sshfiler.remotefile('vzscan_{0}.txt'.format(
          datetime.datetime.now().strftime('%Y%m%d_%H00')))
    else:
      arg.f = self.cmd.sshfiler.remotefile(arg.f)

    return arg

  def run(self, arg):
    zlist = motioncmd.zscan.make_z_mesh(arg)
    laplace = []

    for z in zlist:
      try:
        # Try to move the gantry regardless, there are fail safe for
        # readout errors
        self.cmd.gcoder.moveto(arg.x, arg.y, z, False)
      except:
        pass

      laplace.append(self.cmd.visual.sharpness(arg.m))

      # Writing to screen
      logger.update(
          logger.GREEN("[VZSCAN]"), "z:{0:.1f}, L:{1:.2f}".format(
              z, laplace[-1]))
      # Writing to file
      arg.f.write("{0:.1f} {1:.1f} {2:.1f} {3:.2f}\n".format(
          arg.x, arg.y, z, laplace[-1]))

    logger.flush_update()
    cv2.destroyAllWindows()
    arg.f.close()


#########################
# Helper commands for debugging


class visualshowchip(cmdbase.controlcmd):
  """
  Long display of chip position, until termination signal is obtained.
  """

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def parse(self, line):
    return cmdbase.controlcmd.parse(self, line)

  def run(self, arg):
    while True:
      self.cmd.visual.find_chip(True)
      if cv2.waitKey(100) > 0:  ## If any key is pressed
        break
    cv2.destroyAllWindows()
