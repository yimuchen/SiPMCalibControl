import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
import cmod.visual as vis
import numpy as np
from scipy.optimize import curve_fit
import time
import cv2
import copy


class visualset(cmdbase.controlcmd):
  """
  Defining the visual computation parameters
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('--threshold',
                             '-t',
                             type=float,
                             help=('Grayscale threshold to perform contouring '
                                   'algorithm [0-255]'))
    self.parser.add_argument('--blur',
                             '-b',
                             type=int,
                             help=('Blur size to perform to the image before '
                                   'contouring to avoid picking up noise '
                                   '[pixels]'))
    self.parser.add_argument('--lumi',
                             '-l',
                             type=int,
                             help=('Maximum luminosity threshold of the '
                                   'interior of a contour to be selected as a '
                                   'det candidate (typically 0-255)'))
    self.parser.add_argument('--size',
                             '-s',
                             type=int,
                             help=('Minimum size of a contour to be '
                                   'selected as a det candidate [pixels]'))
    self.parser.add_argument('--ratio',
                             '-r',
                             type=float,
                             help=('Maximum Ratio of the two dimension of a '
                                   'contour to be selected as a det '
                                   'candidate (>1)'))
    self.parser.add_argument('--poly',
                             '-p',
                             type=float,
                             help=('Relative tolerance for performing polygon '
                                   'approximation algorithm (0, 1)'))

  def run(self, args):
    if args.threshold:
      self.visual.threshold = args.threshold
    if args.blur:
      self.visual.blur_range = args.blur
    if args.lumi:
      self.visual.lumi_cutoff = args.lumi
    if args.size:
      self.visual.size_cutoff = args.size
    if args.ratio:
      self.visual.ratio_cutoff = args.ratio
    if args.poly:
      self.visual.poly_range = args.poly


class visualhscan(cmdbase.controlcmd):
  """
  Performing horizontal scan with camera system
  """

  DEFAULT_SAVEFILE = 'vhscan_<BOARDTYPE>_<BOARDID>_<DETID>_<SCANZ>_<TIMESTAMP>.txt'
  LOG = log.GREEN('[VIS HSCAN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    ## Adding common coordinate for x-y scanning
    self.add_hscan_options(hrange=3, distance=0.5)
    self.add_savefile_options(self.DEFAULT_SAVEFILE)
    self.parser.add_argument('-m',
                             '--monitor',
                             action='store_true',
                             help=('Whether or not to open the monitoring window'
                                   ' (could be slow!!)'))
    self.parser.add_argument('--overwrite',
                             action='store_true',
                             help=('Forcing the storage of scan results as '
                                   'session information'))

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_xydet_options(args, add_visoffset=True)
    self.parse_savefile(args)
    return args

  def run(self, args):
    x, y = self.make_hscan_mesh(args)

    ## New container to account for det not found in FOV
    gantry_x = []
    gantry_y = []
    reco_x = []
    reco_y = []

    ## Running over mesh.
    for idx, (xval, yval) in enumerate(zip(x, y)):
      self.check_handle(args)
      self.move_gantry(xval, yval, args.scanz, False)
      time.sleep(0.3)  ## Waiting two frame tiles

      center = self.visual.get_latest()
      image = np.copy(self.visual.get_image(False))

      if center.x > 0 and center.y > 0:
        gantry_x.append(xval)
        gantry_y.append(yval)
        reco_x.append(center.x)
        reco_y.append(center.y)

      self.update_luminosity(center.x,
                             center.y,
                             data_tag='Reco:',
                             Progress=(idx, len(x)))
      args.savefile.write('{0:.1f} {1:.1f} {2:.1f} {3:.2f} {4:.3f}\n'.format(
          xval, yval, args.scanz, center.x, center.y))

      if args.monitor:
        cv2.imshow("SIPMCALIB - visualhscan", image)
        cv2.waitKey(1)

    cv2.destroyAllWindows()
    self.close_savefile(args)

    fitx, covar_x = curve_fit(visualhscan.model, np.vstack((gantry_x, gantry_y)),
                              reco_x)
    fity, covar_y = curve_fit(visualhscan.model, np.vstack((gantry_x, gantry_y)),
                              reco_y)

    self.printmsg( 'Transformation for CamX ' \
          '= ({0:.2f}+-{1:.3f})x + ({2:.2f}+-{3:.2f})y'.format(
              fitx[0], np.sqrt(covar_x[0][0]),
              fitx[1], np.sqrt(covar_x[1][1])  ) )
    self.printmsg( 'Transformation for CamY ' \
          '= ({0:.2f}+-{1:.3f})x + ({2:.2f}+-{3:.2f})y'.format(
              fity[0], np.sqrt(covar_y[0][0]),
              fity[1], np.sqrt(covar_y[1][1])  ) )

    ## Generating calibration det id if using det coordinates
    detid = str(args.detid)
    if not detid in self.board.dets() and int(args.detid) < 0:
      self.board.add_calib_det(args.detid)

    ## Saving rounded coordinates
    if not self.board.visM_hasz(detid, self.gcoder.opz) or args.overwrite:
      self.board.add_visM(detid, self.gcoder.opz,
                          [[fitx[0], fitx[1]], [fity[0], fity[1]]])
    elif self.board.visM_hasz(detid, self.gcoder.opz):
      if self.cmd.prompt_yn(
          'Tranformation equation for z={0:.1f} already exists, overwrite?'.
          format(args.scanz), 'no'):
        self.board.add_visM(detid, self.gcoder.opz,
                            [[fitx[0], fitx[1]], [fity[0], fity[1]]])

    ## Moving back to center
    self.move_gantry(args.x, args.y, args.scanz, False)

  @staticmethod
  def model(xydata, a, b, c):
    x, y = xydata
    return a * x + b * y + c


class visualcenterdet(cmdbase.controlcmd):
  """
  Moving the gantry so that the det is in the center of the field of view
  """

  LOG = log.GREEN('[VIS ALIGN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.add_xydet_options()
    self.parser.add_argument('-z',
                             '--scanz',
                             type=float,
                             help=('Position z to perform centering. User must '
                                   'make sure the visual transformation '
                                   'equation has already been created before'))
    self.parser.add_argument('--overwrite',
                             action='store_true',
                             help=('Whether to overwrite the existing '
                                   'information or not'))
    self.parser.add_argument('--monitor',
                             action='store_true',
                             help=('Open the monitoring window (can be slow!)'))

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_xydet_options(args, add_visoffset=True)
    if not args.scanz:
      raise Exception('Specify the height to perform the centering operation')

    args.calibdet = args.detid if (self.board.visM_hasz(
        args.detid, args.scanz)) else next(
            (x for x in self.board.calib_dets()
             if self.board.visM_hasz(x, args.scanz)), None)

    if args.calibdet == None:
      self.printerr(('Motion transformation equation was not found for '
                     'position z={0:.1f}mm, please run command '
                     '[visualhscan] first').format(args.scanz))
      raise Exception('Transformation equation not found')
    return args

  def run(self, args):
    self.move_gantry(args.x, args.y, args.scanz, False)

    for movetime in range(10):  ## Maximum of 10 movements
      center = None
      image = None

      ## Try to find center for a maximum of 3 times
      for findtime in range(10):
        center = self.visual.get_latest()
        if center.x > 0:
          break
        time.sleep(0.1)

      ## Early exit if det is not found.
      if (center.x < 0 or center.y < 0):
        print( self.gcoder.opx, self.gcoder.opy )
        raise Exception(('Det lost! Check current camera position with '
                         'command visualdetshow'))
      if args.monitor:
        cv2.imshow('SIPMCALIB - visualcenterdet', image)
        cv2.waitKey(1)

      # We are dividing by 4 since the working image is half of the
      # camera resolution

      deltaxy = np.array([
          self.visual.frame_width() / 2 - center.x,
          self.visual.frame_height() / 2 - center.y
      ])

      motionxy = np.linalg.solve(
          np.array(self.board.get_visM(args.calibdet, self.gcoder.opz)), deltaxy)

      ## Early exit if difference from center is small
      if np.linalg.norm(motionxy) < 0.1: break

      self.move_gantry(self.gcoder.opx + motionxy[0],
                         self.gcoder.opy + motionxy[1], self.gcoder.opz, False)
      time.sleep(0.1)  ## Waiting for the gantry to stop moving

    cv2.destroyAllWindows()

    center = self.visual.get_latest()
    self.printmsg(
      'Gantry position: x={0:.1f} y={1:.1f} | '\
      'Det FOV position: x={2:.1f} y={3:.1f}'.
        format(self.gcoder.opx, self.gcoder.opy, center.x, center.y))
    self.printmsg(
      'Det corner coordinate: '\
      '[{0:d},{1:d}], [{2},{3}], [{4},{5}], [{6},{7}]'.format(
        center.poly_x1, center.poly_y1,
        center.poly_x2, center.poly_y2,
        center.poly_x3, center.poly_y3,
        center.poly_x4, center.poly_y4,
      )
    )

    detid = str(args.detid)

    if not self.board.vis_coord_hasz(detid, self.gcoder.opz) or args.overwrite:
      self.board.add_vis_coord(detid, self.gcoder.opz,
                               [self.gcoder.opx, self.gcoder.opy])
    elif self.board.vis_coord_hasz(detid, self.gcoder.opz):
      if self.cmd.prompt_yn(
          str('A visual alignment for z={0:.1f} already exists for the current session, overwrite?'
              .format(args.scanz))):
        self.board.add_vis_coord(detid, self.gcoder.opz,
                                 [self.gcoder.opx, self.gcoder.opy])

    # Luminosity calibrated coordinate doesn't exists. displaying the
    # estimated position from calibration det position
    if not self.board.lumi_coord_hasz(detid, self.gcoder.opz):
      deltax = None
      deltay = None
      currentz = self.gcoder.opz
      for calibdet in self.board.calib_dets():
        det = self.board.get_det(calibdet)
        if (self.board.vis_coord_hasz(calibdet, currentz)
            and any(det.lumi_coord)):
          closestz = min(det.lumi_coord.keys(), key=lambda x: abs(x - currentz))
          deltax = self.board.get_vis_coord(calibdet, currentz)[0] \
                  - self.board.get_lumi_coord(calibdet,closestz)[0]
          deltay = self.board.get_vis_coord(calibdet,currentz)[1] \
                  - self.board.get_lumi_coord(calibdet, closestz)[2]
        if deltax != None and deltay != None:
          self.printmsg('Estimated Lumi center: x={0} y={1}'.format(
              self.gcoder.opx - deltax, self.gcoder.opy - deltay))


class visualmaxsharp(cmdbase.controlcmd):
  """
  Moving the gantry to the position such that the image sharpness is maximized.
  The user is required to input the z points to scan for maximum sharpness.
  """
  LOG = log.GREEN('[VISMAXSHARP]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.add_zscan_options()
    self.parser.add_argument('--wait',
                             type=float,
                             default=0.5,
                             help=('Time to wait between motion and image acquisiation (seconds)'))
    self.parser.add_argument('--monitor',
                             '-m',
                             action='store_true',
                             help=('Open a monitoring window'))
    self.parser.add_argument('--fitmodel',
                             type=str,
                             default='cubic',
                             choices=['quad','cubic','gauss'],
                             help='Model to fit the sharpness profile.')

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_xydet_options(args, add_visoffset=True)
    self.parse_zscan_options(args)
    return args

  def run(self, args):
    zval = np.array(args.zlist)
    laplace = []

    for z in args.zlist:
      self.check_handle(args)
      self.move_gantry(args.x, args.y, z, False)
      time.sleep(args.wait)
      center = self.visual.get_latest()
      laplace.append(center.sharpness)

      # Information
      self.update("z position: {0:.1f} | sharpness: {1:6.2f}".format(z,laplace[-1]))

      # Additional information
      if args.monitor:
        cv2.imshow('SIPMCALIB - visualmaxsharp',
                    np.copy(self.visual.get_image(True)))
        cv2.waitKey(1)

    # Truncating data set to only valid values
    laplace = np.array(laplace)
    mask = laplace > 0
    laplace = laplace[mask]
    zval    = zval[mask]

    model = visualmaxsharp.quad_model() if args.fitmodel == 'quad' else \
            visualmaxsharp.gauss_model() if args.fitmodel == 'gauss' else \
            visualmaxsharp.cubic_model()

    # First fit over full scan range
    fit,cov = curve_fit( model, zval,
                        laplace,
                        p0=[zval[np.argmax(laplace)], *model.init_guess],
                        # Initial guess
                        bounds=([np.min(args.zlist), *model.bounds[0]],
                                [np.max(args.zlist), *model.bounds[1]]),
                        maxfev=int(1e4))
    self.printmsg("Target z position: {0:.2f}mm (actual: {0:.1f}mm)".format(
      fit[0]))
    self.move_gantry(args.x,args.y, fit[0],False)

    cv2.destroyAllWindows()

  """
  Models for running the sharpness fit profile, defined as static methods. Notice
  the various models be defined such that:

  - In the implementation of the __call__ method
    - `z` is the first argument
    - `z_0` indicating the maximum sharpness point must be the second argument
  - provide the following variables:
    - `init_guess` indicating the estimated stating point of the parameters other
      than z_0
    - `bounds` indicating the boundaries of the parameters other than z_0 The
      initial value and boundaries of z0 will be determined from the data.
  """
  class cubic_model(object):
    def __init__(self):
      self.init_guess = [0,-1000,0]
      self.bounds = ([-np.inf,-np.inf,-np.inf],
                     [ np.inf,      0, np.inf])

    def __call__(self,z,z0,a,b,c):
      return a*(z-z0)**3 + b*(z-z0)**2 + c

  class quad_model(object):
    def __init__(self):
      self.init_guess = [-1000,0]
      self.bounds = ([-np.inf,-np.inf],
                     [      0, np.inf])

    def __call__(self,z,z0,a,c):
      return a*(z-z0)**2 + c

  class gauss_model(object):
    def __init__(self):
      self.init_guess = [1000, 10,0]
      self.bounds = ([     0,     0,-np.inf],
                     [np.inf,np.inf, np.inf])

    def __call__(self,z,z0,a,b,c):
      return a*exp(-(z-z0)**2/(2*b**2)) + c


class visualsaveframe(cmdbase.controlcmd):
  """
  Saving the current image to some path
  """
  def __init__(self,cmd):
    cmdbase.controlcmd.__init__(self,cmd)
    self.parser.add_argument('--saveimg',
                             type=str,
                             required=True,
                             help='Local path to store image file')
    self.parser.add_argument('--raw',
                             action='store_true',
                             help='Store raw image or processes image')

  def run(self, args):
    self.visual.save_image(args.saveimg,args.raw)


class visualzscan(cmdbase.controlcmd):
  """
  Scanning focus to calibrate z distance
  """

  DEFAULT_SAVEFILE = 'vscan_<DETID>_<TIMESTAMP>.txt'
  LOG = log.GREEN('[VISZSCAN]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.add_savefile_options(visualzscan.DEFAULT_SAVEFILE)
    self.add_zscan_options()
    self.parser.add_argument('--wait',
                             type=float,
                             default=0.2,
                             help=('Time to wait between image acquisiation (seconds)'))
    self.parser.add_argument('-m',
                             '--monitor',
                             action='store_true',
                             help=('Whether or not to open a monitoring window '
                                   '(could be slow!!)'))

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_zscan_options(args)
    self.parse_xydet_options(args, add_visoffset=True)
    self.parse_savefile(args)
    return args

  def run(self, args):
    laplace = []
    reco_x = []
    reco_y = []
    reco_a = []
    reco_d = []

    for z in args.zlist:
      # Checking termination signal
      self.check_handle(args)
      self.move_gantry(args.x, args.y, z, False)
      time.sleep(args.wait)

      center = self.visual.get_latest()
      image = np.copy(self.visual.get_image(True))
      laplace.append(center.sharpness)
      reco_x.append(center.x)
      reco_y.append(center.y)
      reco_a.append(center.area)
      reco_d.append(center.maxmeas)

      # Writing to screen
      self.update('{0} | {1} | {2}'.format(
          'x:{0:.1f} y:{1:.1f} z:{2:.1f}'.format(
              self.gcoder.opx, self.gcoder.opy, self.gcoder.opz),
          'Sharpness:{0:.2f}'.format(laplace[-1]),
          'Reco x:{0:.1f} Reco y:{1:.1f} Area:{2:.1f} MaxD:{3:.1f}'.format(
              center.x, center.y, center.area, center.maxmeas)))
      # Writing to file
      args.savefile.write('{0:.1f} {1:.1f} {2:.1f} '\
                  '{3:.2f} '\
                  '{4:.1f} {5:.1f} {6:.1f} {7:.1f}\n'.format(
          self.gcoder.opx, self.gcoder.opy, self.gcoder.opz,
          laplace[-1],
          center.x, center.y, center.area, center.maxmeas
          ))

      args.savefile.flush()
      if args.monitor:
        cv2.imshow('SIPMCALIB - visualzscan', image)
        cv2.waitKey(1)

    #Flushing and saving file
    args.savefile.flush()
    args.savefile.close()

    cv2.destroyAllWindows()

class visualshowdet(cmdbase.controlcmd):
  """
  Display of detector position, until termination signal is obtained.
  """
  LOG = log.GREEN('[SHOW DETECTOR]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('--raw',
                             '-r',
                             action='store_true',
                             help='Show the raw image without image processing lines')

  def parse(self, line):
    return cmdbase.controlcmd.parse(self, line)

  def run(self, args):
    self.printmsg("PRESS CTL+C to stop the command")
    self.printmsg("Legend")
    self.printmsg("Failed contor ratio requirement")
    self.printmsg(log.GREEN("Failed area luminosity requirement"))
    self.printmsg(log.YELLOW("Failed rectangular approximation"))
    self.printmsg(log.CYAN("Candidate contour (not largest)"))
    while True:
      try:
        self.check_handle(args)
      except:
        break

      image = self.visual.get_image(args.raw)
      cv2.imshow("SIPMCALIB - visualshowdet", np.copy(image))
      cv2.waitKey(1)
      time.sleep(0.05)
    cv2.destroyAllWindows()
