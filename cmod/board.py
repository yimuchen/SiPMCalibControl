"""
  board.py

  Python classes used to handling detector layout and board configurations, and
  positional calibration results. More details will be provided in the per class
  documentations.
"""
import cmod.logger as logger
import cmod.gcoder as gcoder
import json


class Detector(object):
  """
  A detector element is defined as an object with a specific readout mode, a
  corresponding channel, and at least one set of (default) coordinates. The
  handling of the detector. No name will be given for the detector element here,
  that will be handled by the parent "Board" class.

  The calibrated coordinates (either the visually calibrated coordinates and the
  accompanying transformation matrix, or the luminosity aligned coordinates will
  be stored as a dictionary, with the z operation value used for obtaining the
  calibration used as the key.)
  """
  def __init__(self, jsonmap):
    self.mode = int(jsonmap['mode'])
    self.channel = int(jsonmap['channel'])
    self.orig_coord = jsonmap['default coordinates']
    self.vis_coord = {}
    self.vis_M = {}
    self.lumi_coord = {}

    # Additional parsing.
    if (self.orig_coord[0] > gcoder.GCoder.max_x() or  #
        self.orig_coord[1] > gcoder.GCoder.max_y() or  #
        self.orig_coord[0] < 0 or self.orig_coord[1] < 0):
      logger.printwarn(f"""
      The specified detector position (x:{self.orig_coord[0]},
      y:{self.orig_coord[1]}) is outside of the gantry boundaries
      (0-{gcoder.GCoder.max_x()},0-{gcoder.GCoder.max_y()}). The expected
      detector position will be not adjusted, but gantry motion might not reach
      it. Which mean any results may be wrong.
      """)

  def __str__(self):
    return str(self.__dict__())

  def __dict__(self):
    return {
        'mode': self.mode,
        'channel': self.channel,
        'default coordinates': self.orig_coord,
        'Luminosity coordinates': self.lumi_coord,
        'Visual coordinates': self.vis_coord,
        'FOV transformation': self.vis_M
    }


class Board(object):
  """
  Class for storing a board type an a list of det x-y positions
  """
  def __init__(self):
    self.boardtype = ""
    self.boarddescription = ""
    self.boardid = ""
    self.det_map = {}

  def clear(self):
    self.boardtype = ""
    self.boarddescription = ""
    self.boardid = ""
    self.det_map = {}

  def set_boardtype(self, file):
    if any(self.dets()) or not self.empty():
      logger.printwarn(('The current session is not empty. Loading a new '
                        'boardtype will erase any existing configuration '
                        'for the current session'))

    jsonmap = json.loads(open(file, 'r').read())
    self.boardtype = jsonmap['board type']
    self.boarddescription = jsonmap['board description']
    self.boardid = jsonmap['board id']

    for detid in jsonmap['detectors']:
      self.det_map[detid] = Detector(jsonmap['detectors'][detid])

  def load_calib_file(self, file):
    if not self.empty():
      logger.printwarn(('The current session is not empty. Loading a new '
                        'boardtype will erase any existing configuration '
                        'for the current session'))
    jsonmap = json.loads(open(file, 'r').read())

    for det in jsonmap:
      if det not in self.det_map:
        if int(det) >= 0:
          logger.printwarn(('Detector recorded in the calibration file but not '
                            'defined in the calibration, ignoring'))
          continue
        else:
          self.add_calib_det(det)

      def format_dict(original_dict):
        return {float(z): original_dict[z] for z in original_dict}

      self.det_map[det].lumi_coord = format_dict(
          jsonmap[det]['Luminosity coordinates'])
      self.det_map[det].vis_coord = format_dict(
          jsonmap[det]['Visual coordinates'])
      self.det_map[det].vis_M = format_dict(jsonmap[det]['FOV transformation'])

  def save_calib_file(self, file):
    dicttemp = {det: self.det_map[det].__dict__() for det in self.det_map}

    with open(file, 'w') as f:
      f.write(json.dumps(dicttemp, indent=2))

  def get_det(self, detid):
    return self.det_map[detid]

  def dets(self):
    return self.det_map.keys()

  def calib_dets(self):
    return sorted([k for k in self.dets() if int(k) < 0], reverse=True)

  def add_calib_det(self, detid):
    detid = str(detid)
    if detid not in self.dets() and int(detid) < 0:
      self.det_map[detid] = Detector({
          "mode": -1,
          "channel": -1,
          "default coordinates": [-100, -100]
      })

  # Get/Set calibration measures with additional parsing
  def add_vis_coord(self, det, z, data):
    det = str(det)
    self.det_map[det].vis_coord[self.roundz(z)] = data

  def add_visM(self, det, z, data):
    det = str(det)
    self.det_map[det].vis_M[self.roundz(z)] = data

  def add_lumi_coord(self, det, z, data):
    det = str(det)
    self.det_map[det].lumi_coord[self.roundz(z)] = data

  def get_vis_coord(self, det, z):
    det = str(det)
    return self.det_map[det].vis_coord[self.roundz(z)]

  def get_visM(self, det, z):
    det = str(det)
    return self.det_map[det].vis_M[self.roundz(z)]

  def get_lumi_coord(self, det, z):
    det = str(det)
    return self.det_map[det].lumi_coord[self.roundz(z)]

  def vis_coord_hasz(self, det, z):
    det = str(det)
    return self.roundz(z) in self.det_map[det].vis_coord

  def visM_hasz(self, det, z):
    det = str(det)
    return self.roundz(z) in self.det_map[det].vis_M

  def lumi_coord_hasz(self, det, z):
    det = str(det)
    return self.roundz(z) in self.det_map[det].lumi_coord

  def empty(self):
    for det in self.det_map:
      if (any(self.det_map[det].vis_coord) or any(self.det_map[det].vis_M)
          or any(self.det_map[det].lumi_coord)):
        return False
    return True

  @staticmethod
  def roundz(rawz):
    return round(rawz, 1)


## In file unit testing
if __name__ == "__main__":
  board = Board()
  board.set_boardtype('cfg/reference_single.json')
  print(board.det_map['-100'])
  board.save_calib_file('test.json')
