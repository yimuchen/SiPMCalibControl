import cmod.logger as logger
import cmod.gcoder as gcoder
import json

class Board(object):
  """
  Class for storing a board type an a list of det x-y positions
  """

  def __init__(self):
    self.boardtype = ""
    self.boarddescription = ""
    self.boardid = ""
    self.orig_coord = {}
    self.vis_coord = {}
    self.visM = {}
    self.lumi_coord = {}

  def clear(self):
    self.boardtype = ""
    self.boarddescription = ""
    self.boardid = ""
    self.orig_coord = {}
    self.vis_coord = {}
    self.visM = {}
    self.lumi_coord = {}

  def set_boardtype(self, file):
    if any(self.dets()) or not self.empty():
      logger.printwarn(('The current session is not empty. Loading a new '
                        'boardtype will erase any existing configuration '
                        'for the current session'))

    jsontemp = json.loads(open(file, 'r').read())
    self.boardtype = jsontemp['board type']
    self.boarddescription = jsontemp['board description']
    self.boardid = jsontemp['board id']

    ## Getting the original coordinate list
    for key in jsontemp['default coordinate']:
      self.orig_coord[str(key)] = jsontemp['default coordinate'][key]
      if (self.orig_coord[str(key)][0] > gcoder.GCoder.max_x()
          or self.orig_coord[str(key)][1] > gcoder.GCoder.max_y()
          or self.orig_coord[str(key)][0] < 0
          or self.orig_coord[str(key)][1] < 0):
        logger.printwarn(('The det position for det {0} (x:{1},y:{2}) '
                          'is outside of the gantry boundaries (0-{3},0-{4}). '
                          'For safety of operation, the det position will be '
                          'adjusted. This might lead to unexpected '
                          'behavior').format(key, self.orig_coord[str(key)][0],
                                             self.orig_coord[str(key)][1],
                                             gcoder.GCoder.max_x(),
                                             gcoder.GCoder.max_y()))
        self.orig_coord[str(key)][0] = max(
            [min([self.orig_coord[str(key)][0],
                  gcoder.GCoder.max_x()]), 0])
        self.orig_coord[str(key)][1] = max(
            [min([self.orig_coord[str(key)][1],
                  gcoder.GCoder.max_y()]), 0])

      self.vis_coord[str(key)] = {}
      self.visM[str(key)] = {}
      self.lumi_coord[str(key)] = {}

  def load_calib_file(self, file):
    if not self.empty():
      logger.printwarn(('The current session is not empty. Loading a new '
                        'boardtype will erase any existing configuration '
                        'for the current session'))
    jsontemp = json.loads(open(file, 'r').read())

    def make_fz_dict(ext_dict):
      return {
          detid: {float(z): obj
                   for z, obj in ext_dict[detid].items()}
          for detid in self.dets()
      }

    self.lumi_coord = make_fz_dict(jsontemp['Lumi scan calibration'])
    self.vis_coord = make_fz_dict(jsontemp['FOV scan calibration'])
    self.visM = make_fz_dict(jsontemp['FOV transformation matrix'])

  def save_calib_file(self, file):
    dicttemp = {
        'Lumi scan calibration': self.lumi_coord,
        'FOV scan calibration': self.vis_coord,
        'FOV transformation matrix': self.visM
    }

    with open(file, 'w') as f:
      f.write(json.dumps(dicttemp, indent=2))

  def dets(self):
    return self.orig_coord.keys()

  def calibdets(self):
    return sorted([k for k in self.orig_coord.keys() if int(k) < 0],
                  reverse=True)

  def add_calib_det(self, detid):
    detid = str(detid)
    if detid not in self.orig_coord and int(detid) < 0:
      self.orig_coord[detid] = [-100, -100]  # Non-existent calibration det
      self.vis_coord[detid] = {}
      self.visM[detid] = {}
      self.lumi_coord[detid] = {}

  # Get/Set calibration measures with additional parsing
  def add_vis_coord(self, det, z, data):
    det = str(det)
    self.vis_coord[det][self.roundz(z)] = data

  def add_visM(self, det, z, data):
    det = str(det)
    self.visM[det][self.roundz(z)] = data

  def add_lumi_coord(self, det, z, data):
    det = str(det)
    self.lumi_coord[det][self.roundz(z)] = data

  def get_vis_coord(self, det, z):
    det = str(det)
    return self.vis_coord[det][self.roundz(z)]

  def get_visM(self, det, z):
    det = str(det)
    return self.visM[det][self.roundz(z)]

  def get_lumi_coord(self, det, z):
    det = str(det)
    return self.vis_coord[det][self.roundz(z)]

  def vis_coord_hasz(self, det, z):
    det = str(det)
    return self.roundz(z) in self.vis_coord[det]

  def visM_hasz(self, det, z):
    det = str(det)
    return self.roundz(z) in self.visM[det]

  def lumi_coord_hasz(self, det, z):
    det = str(det)
    return self.roundz(z) in self.lumi_coord[det]

  def empty(self):
    for det in self.dets():
      if (any(self.vis_coord[det]) or any(self.visM[det])
          or any(self.lumi_coord[det])):
        return False
    return True

  @staticmethod
  def roundz(rawz):
    return round(rawz, 1)
