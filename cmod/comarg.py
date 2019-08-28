import cmod.logger as log
import numpy as np
import datetime
import re


def prompt(question, default='no'):
  """
  Ask a yes/no question via input() and return their answer.

  'question' is a string that is presented to the user.
  'default' is the presumed answer if the user just hits <Enter>.
            It must be 'yes' (the default), 'no' or None (meaning
            an answer is required of the user).

  The 'answer' return value is True for 'yes' or False for 'no'.
  """
  valid = {'yes': True, 'ye': True, 'y': True, 'no': False, 'n': False}
  if default is None:
    prompt = ' [y/n] '
  elif default.lower() == 'yes':
    prompt = ' [Y/n] '
  elif default.lower() == 'no':
    prompt = ' [y/N] '
  else:
    raise ValueError('invalid default answer: %s'.format(default))

  while True:
    print(question + prompt)
    choice = input().lower()
    if default is not None and choice == '':
      return valid[default]
    elif choice in valid:
      return valid[choice]
    else:
      log.printerr(
          'Please respond with \'yes\' or \'no\' (or \'y\' or \'n\').\n')


def add_xychip_options(parser):
  parser.add_argument(
      '-x',
      type=float,
      help=('Specifying the x coordinate explicitly [mm]. If none is given '
            'the current gantry position will be used instead'))
  parser.add_argument(
      '-y',
      type=float,
      help=('Specify the y coordinate explicitly [mm]. If none is given '
            'the current gantry position will be used.'))
  parser.add_argument(
      '-c',
      '--chipid',
      type=str,
      help=('Specify x-y coordinates via chip id, input negative value to '
            'indicate that the chip is a calibration one (so you can '
            'still specify coordinates with it)'))


def add_readout_option(parser):
  parser.add_argument(
      '--mode',
      type=int,
      choices=[-1, 1, 2],
      help='Readout method to be used: 1:picoscope, 2:ADC, -1:Predefined model')
  parser.add_argument('--channel',
                      type=int,
                      default=0,
                      help='Input channel to use')
  parser.add_argument('--samples',
                      type=int,
                      default=5000,
                      help='Number of samples to take the average')


def add_hscan_options(parser, scanz=35, hrange=20, distance=0.5):
  """
  Common arguments for performing x-y scan
  """
  add_xychip_options(parser)
  add_readout_option(parser)
  parser.add_argument(
      '-z',
      '--scanz',
      type=float,
      default=scanz,
      help=('Height to perform horizontal scan [mm], using present '
            'coordinates if not specified'))
  parser.add_argument(
      '-r',
      '--range',
      type=float,
      default=hrange,
      help='Range to perform x-y scanning from central position [mm]')
  parser.add_argument('-d',
                      '--distance',
                      type=float,
                      default=distance,
                      help='Horizontal sampling distance [mm]')


def add_savefile_options(parser, default_filename):
  parser.add_argument('-f',
                      '--savefile',
                      type=str,
                      default=default_filename,
                      help='Writing results to file')
  parser.add_argument('--wipefile',
                      action='store_true',
                      help='Wipe existing content in output file')


def add_zscan_options(parser, zlist=range(10, 51, 1)):
  add_xychip_options(parser)
  add_readout_option(parser)
  parser.add_argument(
      '-z',
      '--zlist',
      type=str,
      nargs='+',
      default=zlist,
      help=('List of z coordinate to perform scanning. One can add a list '
            'of number by the notation "[startz endz sepration]"'))


def find_closest_z(my_map, current_z):
  return min(my_map.keys(), key=lambda x: abs(float(x) - float(current_z)))


def find_xyoffset(board, currentz):
  """
  Finding x-y offset between the luminosity and visual alignment based the
  existing calibration
  """
  # If no calibration chip exists, just return a default value (from gantry head
  # design.)
  DEFAULT_XOFFSET = -40
  DEFAULT_YOFFSET = 0
  if not any(board.calibchips()):
    return DEFAULT_XOFFSET, DEFAULT_YOFFSET

  # Calculations will be based on the "first" calibration chip available
  # That has both lumi and visual alignment offsets
  for calibchip in board.calibchips():
    lumi_x = None
    lumi_y = None
    vis_x = None
    vis_y = None

    # Trying to get the luminosity alignment with closest z value
    if any(board.vis_coord[calibchip]):
      closestz = find_closest_z(board.lumi_coord[calibchip], currentz)
      lumi_x = board.lumi_coord[calibchip][closestz][0]
      lumi_y = board.lumi_coord[calibchip][closestz][2]

    # Trying to get the visual alignment with closest z value
    if any(board.lumi_coord[calibchip]):
      closestz = min(board.lumi_coord[calibchip].keys(),
                     key=lambda x: abs(x - currentz))
      vis_x = board.vis_coord[calibchip][currentz][0]
      vis_y = board.vis_coord[calibchip][currentz][1]

    if lumi_x and lumi_y and vis_x and vis_y:
      return vis_x - lumi_x, vis_y - lumi_y

  # If no calibration chip has both calibration values
  # Just return the original calibration value.
  return DEFAULT_XOFFSET, DEFAULT_YOFFSET


def parse_xychip_options(arg, cmdsession, add_visoffset=False, raw_coord=False):
  ## Setting up alias for board
  board = cmdsession.board

  ## If not directly specifying the chip id, assuming some calibration chip with
  ## specified coordinate system. Exit immediately.
  if arg.chipid == None:
    arg.chipid = '-100'
    if not arg.x: arg.x = cmdsession.gcoder.opx
    if not arg.y: arg.y = cmdsession.gcoder.opy
    return

  ## Attempt to get a board specified chip position.
  if not arg.chipid in board.chips():
    raise Exception('Chip id was not specified in board type')

  ## Raising exception when attempting to overide chip position with raw
  ## x-y values
  if arg.x or arg.y:
    raise Exception('You can either specify chip-id or x y, not both')

  # Early exit if raw coordinates requested
  if raw_coord:
    arg.x, arg.y = board.orig_coord[arg.chipid]
    return

  # Determining current z value ( from argument first, otherwise guessing
  # from present gantry position )
  current_z = arg.z if hasattr(arg, 'z') else \
               min(arg.zlist) if hasattr(arg, 'zlist') else \
               cmdsession.gcoder.opz

  if add_visoffset:
    if any(board.vis_coord[arg.chipid]):
      closest_z = find_closest_z(board.vis_coord[arg.chipid], current_z)
      arg.x = board.vis_coord[arg.chipid][closest_z][0]
      arg.y = board.vis_coord[arg.chipid][closest_z][1]
    else:
      x_offset, y_offset = find_xyoffset(board, current_z)
      arg.x = board.orig_coord[arg.chipid][0] + x_offset
      arg.y = board.orig_coord[arg.chipid][1] + x_offset
  else:
    if any(board.lumi_coord[arg.chipid]):
      closest_z = find_closest_z(board.lumi_coord[arg.chipid], current_z)
      arg.x = board.lumi_coord[arg.chipid][closest_z][0]
      arg.y = board.lumi_coord[arg.chipid][closest_z][2]
    elif any(board.vis_coord[arg.chipid]):
      x_offset, y_offset = find_xyoffset(board, current_z)
      closest_z = find_closest_z(board.vis_coord[arg.chipid], current_z)
      arg.x = board.vis_coord[arg.chipid][closest_z][0] - x_offset
      arg.y = board.vis_coord[arg.chipid][closest_z][1] - y_offset
    else:
      arg.x, arg.y = board.orig_coord[arg.chipid]


def parse_readout_options(arg, cmd):
  if not arg.mode:
    arg.mode = cmd.readout.mode
  if arg.mode == cmd.readout.MODE_PICO:
    if arg.channel < 0 or arg.channel > 1:
      raise Exception('Channel for PICOSCOPE can only be 0 or 1')
    cmd.readout.set_mode(arg.mode)
  elif arg.mode == cmd.readout.MODE_ADC:
    if arg.channel < 0 or arg.channel > 3:
      raise Exception('Channel for ADC can only be 0--3')
    cmd.readout.set_mode(arg.mode)


def make_hscan_mesh(arg):
  """
  Common argument for generating x-y scanning coordinate mesh
  """
  gantrymin = 1
  gantrymax = 450

  if (arg.x - arg.range < gantrymin or arg.x + arg.range > gantrymax
      or arg.y - arg.range < gantrymin or arg.y + arg.range > gantrymax):
    log.printwarn(('The arguments placed will put the gantry past its limits, '
                   'the command will used modified input parameters'))

  xmin = max([arg.x - arg.range, gantrymin])
  xmax = min([arg.x + arg.range, gantrymax])
  ymin = max([arg.y - arg.range, gantrymin])
  ymax = min([arg.y + arg.range, gantrymax])
  sep = max([arg.distance, 0.1])
  xmesh, ymesh = np.meshgrid(np.linspace(xmin, xmax, (xmax - xmin) / sep + 1),
                             np.linspace(ymin, ymax, (ymax - ymin) / sep + 1))
  return [
      xmesh.reshape(1, np.prod(xmesh.shape))[0],
      ymesh.reshape(1, np.prod(ymesh.shape))[0]
  ]


def parse_zscan_options(arg):
  arg.zlist = " ".join(arg.zlist)
  braces = re.findall(r'[(.*?)]', arg.zlist)
  arg.zlist = re.sub(r'[(.*?)]', '', arg.zlist)
  arg.zlist = [float(z) for z in arg.zlist.split()]
  for rstring in braces:
    r = [float(rarg) for rarg in rstring.split()]
    if len(r) < 2 or len(r) > 3:
      raise Exception(('Range must be in the format [start end (sep)] '
                       'sep is assumed to be 1 if not specified'))
    minz = min(r[:2])
    maxz = max(r[:2])
    sep = 1 if len(r) == 2 else r[2]
    arg.zlist.extend(np.linspace(minz, maxz, (maxz - minz) / sep,
                                 endpoint=False))
  arg.zlist.sort()  ## Returning sorted result


def timestamp_filename(prefix, arg, add_attributes=[]):
  tags = ''
  for attr in add_attributes:
    if hasattr(arg, attr):
      tags += '_' + attr + str(getattr(arg, attr))

  if not hasattr(arg, 'chipid') or arg.chipid.startswith('-'):
    return '{0}{1}_{2}.txt'.format(
        prefix, tags,
        datetime.datetime.now().strftime('%Y%m%d_%H00'))
  else:
    return '{0}_{1}{2}_{3}.txt'.format(
        prefix, 'chip%s'.format(arg.chipid), tags,
        datetime.datetime.now().strftime('%Y%m%d_%H00'))


if __name__ == "__main__":
  my_map = {"20.4": "2", "21.5": "irt"}
  print(find_closest_z(my_map,10.2))
  print(find_closest_z(my_map,30.2))
