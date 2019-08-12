import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
import cmod.comarg as comarg
import numpy as np
from scipy.optimize import curve_fit
import time
import cv2


class visualhscan(cmdbase.controlcmd):
  """
  Performing horizontal scan with camera system
  """

  DEFAULT_SAVEFILE = 'vhscan_<ZVAL>_<TIMESTAMP>.txt'
  LOG = log.GREEN('[VIS HSCAN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    ## Adding common coordinate for x-y scanning
    comarg.add_hscan_options(self.parser, hrange=3, distance=0.5)
    comarg.add_savefile_options(self.parser, self.DEFAULT_SAVEFILE)
    self.parser.add_argument(
        '-m',
        '--monitor',
        action='store_true',
        help='Whether or not to open the monitoring window (could be slow!!)')
    self.parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Forcing the storage of scan results as session information')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)

    ## Defaults to present position
    comarg.parse_xychip_options(arg, self.cmd, add_visoffset=True)

    ## Setting up file name
    filename = arg.savefile if arg.savefile != visualhscan.DEFAULT_SAVEFILE \
               else comarg.timestamp_filename( 'vhscan', arg, ['scanz'] )
    arg.savefile = self.sshfiler.remotefile(filename, arg.wipefile)

    return arg

  def run(self, arg):
    x, y = comarg.make_hscan_mesh(arg)

    ## New container to account for chip not found in FOV
    gantry_x = []
    gantry_y = []
    reco_x = []
    reco_y = []

    ## Running over mesh.
    for xval, yval in zip(x, y):
      try:
        # Try to move the gantry. Even if it fails there will be fail safes
        # in other classes
        self.gcoder.moveto(xval, yval, arg.scanz, False)
      except:
        pass

      center = self.visual.find_chip(arg.monitor)

      if center.x > 0 and center.y > 0:
        gantry_x.append(xval)
        gantry_y.append(yval)
        reco_x.append(center.x)
        reco_y.append(center.y)

      self.update(
          'x:{0:.1f}, y:{1:.1f}, z:{2:.1f} | Reco x:{3:.1f}, y:{4:.1f}'.format(
              xval, yval, arg.scanz, center.x, center.y))
      arg.savefile.write('{0:.1f} {1:.1f} {2:.1f} {3:.2f} {4:.3f}\n'.format(
          xval, yval, arg.scanz, center.x, center.y))

    cv2.destroyAllWindows()
    arg.savefile.close()

    fitx, corrx = curve_fit(visualhscan.model, np.vstack((gantry_x, gantry_y)),
                            reco_x)
    fity, corry = curve_fit(visualhscan.model, np.vstack((gantry_x, gantry_y)),
                            reco_y)

    self.printmsg( 'Transformation for CamX ' \
          '= ({0:.2f}+-{1:.3f})x + ({2:.2f}+-{3:.2f})y'.format(
              fitx[0], np.sqrt(corrx[0][0]),
              fitx[1], np.sqrt(corrx[1][1])  ) )
    self.printmsg( 'Transformation for CamY ' \
          '= ({0:.2f}+-{1:.3f})x + ({2:.2f}+-{3:.2f})y'.format(
              fity[0], np.sqrt(corry[0][0]),
              fity[1], np.sqrt(corry[1][1])  ) )

    ## Saving rounded coordinates
    if (not self.gcoder.opz in self.board.visM[arg.chipid] or arg.overwrite):
      self.board.add_visM(arg.chipid, self.gcoder.opz,
                          [[fitx[0], fitx[1]], [fity[0], fity[1]]])
    elif self.gcoder.opz in self.board.visM[arg.chipid]:
      if comarg.prompt(
          'Tranformation equation for z={0:.1f} already exists, overwrite?'.
          format(arg.scanz), 'no'):
        self.board.add_visM(arg.chipid, self.gcoder.opz,
                            [[fitx[0], fitx[1]], [fity[0], fity[1]]])

    ## Moving back to center
    self.gcoder.moveto(arg.x, arg.y, arg.scanz, False)

  @staticmethod
  def model(xydata, a, b, c):
    x, y = xydata
    return a * x + b * y + c


class visualcenterchip(cmdbase.controlcmd):
  """
  Moving the gantry so that the chip is in the center of the field of view
  """

  LOG = log.GREEN('[VIS ALIGN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    comarg.add_xychip_options(self.parser)
    self.parser.add_argument(
        '-z',
        '--startz',
        type=float,
        help=(
        'Position z to perform centering. User must make sure the visual '\
        'transformation equation have already been created have already been '\
        'created before' )
    )
    self.parser.add_argument('--overwrite', action='store_true', help='T')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    comarg.parse_xychip_options(arg, self.cmd, add_visoffset=True)
    if not arg.startz:
      raise Exception("Specify the height to perform the centering operation")

    arg.calibchip = arg.chipid if (self.board.visM_hasz(
        arg.chipid, arg.startz)) else next(
            (x for x in self.board.calibchips()
             if self.board.visM_hasz(x, arg.startz)), None)

    if arg.calibchip == None:
      self.printerr(
          'Motion transformation equation was not found for position z={0:.1f}mm, please run command [visualhscan] first'
          .format(arg.startz))
      print(arg.startz, self.board.visM)
      raise Exception('Transformation equation not found')
    return arg

  def run(self, arg):
    self.gcoder.moveto(arg.x, arg.y, arg.startz, False)
    for movetime in range(10):  ## Maximum of 10 movements
      center = None

      ## Try to find center for a maximum of 3 times
      for findtime in range(3):
        center = self.visual.find_chip(False)
        if center.x > 0:
          break

      ## Early exit if chip is not found.
      if (center.x < 0 or center.y < 0):
        raise Exception(
            'Chip lost! Check current camera position with command visualchipshow'
        )

      deltaxy = np.array([
          self.visual.frame_width() / 2 - center.x,
          self.visual.frame_height() / 2 - center.y
      ])

      motionxy = np.linalg.solve(
          np.array(self.board.get_visM(arg.calibchip, self.gcoder.opz)), deltaxy)

      ## Early exit if difference from center is small
      if np.linalg.norm(motionxy) < 0.1: break

      self.gcoder.moveto(self.gcoder.opx + motionxy[0],
                         self.gcoder.opy + motionxy[1], self.gcoder.opz, False)
      time.sleep(0.1)  ## Waiting for the gantry to stop moving

    center = self.visual.find_chip(False)
    self.printmsg(
      'Gantry position: x={0:.1f} y={1:.1f} | '\
      ' Chip FOV position: x={2:.1f} y={3:.1f}'.
        format(self.gcoder.opx, self.gcoder.opy, center.x, center.y))

    if (not self.board.vis_coord_hasz(arg.chipid, self.gcoder.opz)
        or arg.overwrite):
      self.board.add_vis_coord(arg.chipid, self.gcoder.opz,
                               [self.gcoder.opx, self.gcoder.opy])

    # Luminosity calibrated coordinate doesn't exists. displaying the
    # estimated position from calibration chip position
    if not self.board.lumi_coord_hasz(arg.chipid, self.gocder.opz):
      deltax = None
      deltay = None
      currentz = self.gcoder.opz
      for calibchip in self.board.calibchips():
        if (self.board.vis_coord_hasz(calibchip, currentz)
            and any(self.board.lumi_coord[calibchip])):
          closestz = min(self.board.lumi_coord[calibchip].keys(),
                         key=lambda x: abs(x - currentz))
          deltax = self.board.get_vis_coord(calibchip, currentz)[0] \
                  - self.board.get_lumi_coord(calibchip,closestz)[0]
          deltay = self.board.get_vis_coord(calibchip,currentz)[1] \
                  - self.board.get_lumi_coord(calibchip, closestz)[2]
        if deltax != None and deltay != None:
          self.printmsg('Estimated Lumi center: x={0} y={1}'.format(
              self.gcoder.opx - deltax, self.gcoder.opy - deltay))


class visualmaxsharp(cmdbase.controlcmd):
  """
  Moving the gantry so that the image sharpness is maximized
  """
  LOG = log.GREEN('[VISMAXSHARP]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    comarg.add_xychip_options(self.parser)
    self.parser.add_argument(
        '-z',
        '--startz',
        type=float,
        default=30,
        help='Initial value to begin finding optimal z value [mm]')
    self.parser.add_argument(
        '-d',
        '--stepsize',
        type=float,
        default=1,
        help='First step size to scan for immediate neighborhood z scan [mm]')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    comarg.parse_xychip_options(arg, self.cmd, add_visoffset=True)
    return arg

  def run(self, arg):
    self.gcoder.moveto(arg.x, arg.y, arg.startz, False)
    laplace = self.visual.sharpness(False)
    zval = arg.startz
    zstep = arg.stepsize

    while abs(zstep) >= 0.1:
      self.gcoder.moveto(arg.x, arg.y, zval + zstep, False)
      newlap = self.visual.sharpness(False)

      if newlap > laplace:
        laplace = newlap
        zval += zstep
      else:
        zstep *= -0.8
      self.update("z:{0:.1f}, L:{1:.2f}".format(zval, laplace))
    self.printmsg("Final z:{0:.1f}".format(self.gcoder.opz))


class visualzscan(cmdbase.controlcmd):
  """
  Scanning focus to calibrate z distance
  """

  DEFAULT_SAVEFILE = 'vscan_<TIMESTAMP>.txt'
  LOG = log.GREEN('[VISZSCAN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    comarg.add_savefile_options(self.parser, visualzscan.DEFAULT_SAVEFILE)
    comarg.add_zscan_options(self.parser)
    self.parser.add_argument(
        '-m',
        '--monitor',
        action='store_true',
        help='Whether or not to open the monitoring window (could be slow!!)')

  def parse(self, line):
    arg = cmdbase.controlcmd.parse(self, line)
    comarg.parse_xychip_options(arg, self.cmd, add_visoffset=True)
    comarg.parse_zscan_options(arg)

    filename = arg.savefile if arg.savefile != visualzscan.DEFAULT_SAVEFILE    \
               else comarg.timestamp_filename( 'vzscan', arg )

    arg.savefile = self.sshfiler.remotefile(filename, arg.wipefile)

    return arg

  def run(self, arg):
    laplace = []
    reco_x = []
    reco_y = []
    reco_a = []
    reco_d = []

    for z in arg.zlist:
      try:
        # Try to move the gantry regardless, there are fail safe for
        # readout errors
        self.gcoder.moveto(arg.x, arg.y, z, False)
      except:
        pass

      reco = self.visual.find_chip(arg.monitor)
      laplace.append(self.visual.sharpness(arg.monitor))
      reco_x.append(reco.x)
      reco_y.append(reco.y)
      reco_a.append(reco.area)
      reco_d.append(reco.maxmeas)

      # Writing to screen
      self.update('{0} | {1} | {2}'.format(
          'x:{0:.1f} y:{1:.1f} z:{2:.1f}'.format(
              self.gcoder.opx, self.gcoder.opy, self.gcoder.opz),
          'Sharpness:{0:.2f}'.format(laplace[-1]),
          'Reco x:{0:.1f} Reco y:{1:.1f} Area:{2:.1f} MaxD:{3:.1f}'.format(
              reco.x, reco.y, reco.area, reco.maxmeas)))
      # Writing to file
      arg.savefile.write('{0:.1f} {1:.1f} {2:.1f} '\
                  '{3:.2f} '\
                  '{4:.1f} {5:.1f} {6:.1f} {7:.1f}\n'.format(
          self.gcoder.opx, self.gcoder.opy, self.gcoder.opz,
          laplace[-1],
          reco.x, reco.y, reco.area, reco.maxmeas
          ))

    cv2.destroyAllWindows()


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
      self.visual.find_chip(True)
      if cv2.waitKey(100) > 0:  ## If any key is pressed
        break
    cv2.destroyAllWindows()
