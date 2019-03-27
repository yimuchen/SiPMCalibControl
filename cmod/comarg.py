import cmod.logger as log
import numpy as np
import datetime
import sys
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
      help=
      'Specifying the x coordinate explicitly [mm]. If none is given the current gantry position will be used instead'
  )
  parser.add_argument(
      '-y',
      type=float,
      help=
      'Specify the y coordinate explicitly [mm]. If none is give nthe current gantry position will be used.'
  )
  parser.add_argument(
      '-c',
      '--chipid',
      type=str,
      help=
      'Specify x-y coordinates via chip id, input negative value to indicate that the chip is a calibration one (so you can still specify coordinates with it)'
  )
  return


def add_hscan_options(parser, scanz=35, hrange=20, distance=0.5):
  """
  Common arguments for performing x-y scan
  """
  add_xychip_options(parser)
  parser.add_argument(
      '-z',
      '--scanz',
      type=float,
      default=scanz,
      help=
      "Height to perform horizontal scan [mm], using present coordinates if not specified"
  )
  parser.add_argument(
      '-r',
      '--range',
      type=float,
      default=hrange,
      help="Range to perform x-y scanning from central position [mm]")
  parser.add_argument(
      '-d',
      '--distance',
      type=float,
      default=distance,
      help='Horizontal sampling distance [mm]')
  return


def add_savefile_options(parser, default_filename):
  parser.add_argument(
      '-f',
      '--savefile',
      type=str,
      default=default_filename,
      help='Writing results to file')
  parser.add_argument(
      '--wipefile',
      action='store_true',
      help='Wipe existing content in output file')


def add_zscan_options(parser, zlist=range(10, 51, 1)):
  add_xychip_options(parser)
  parser.add_argument(
      '-z',
      '--zlist',
      type=str,
      nargs='+',
      default=zlist,
      help=
      'List of z coordinate to perform scanning. One can add a list of number by the notation "[startz endz sepration]"'
  )


def parse_xychip_options(arg, cmdsession, add_visoffset=False, raw_coord=False):
  if arg.chipid != None:
    if int(arg.chipid) >= 0:
      if arg.x or arg.y:
        raise Exception('You can either specify chip-id or x y, not both')
      if not str(arg.chipid) in cmdsession.board.chips():
        raise Exception('Chip id was not speficied in board type')
      arg.x, arg.y = cmdsession.board.orig_coord[arg.chipid]
    else:
      ## Setting up alias for board
      board = cmdsession.board

      if not arg.chipid in board.chips():
        raise Exception('Chip id was not speficied in board type')
      if raw_coord:
        # Early exit if not specified
        arg.x, arg.y = board.orig_coord[arg.chipid]
        return

      arg.x, arg.y = board.orig_coord[arg.chipid]

      # Determining current z value ( from argument first, otherwise guessing
      # from present gantry position )
      currentz = arg.z if hasattr( arg, 'z' ) else \
                 min(arg.zlist) if hasattr( arg, 'zlist' ) else \
                 cmdsession.gcoder.opz

      # Determine visual offset to assign based on *calibration* chips!
      xoffset = -20
      yoffset = 0
      if any(board.calibchips()):
        calibchip = board.calibchips()[0]
        if (currentz in board.vis_coord[calibchip]
            and any(board.lumi_coord[calibchip])):
          closestz = min(
              board.lumi_coord[calibchip].keys(),
              key=lambda x: abs(x - currentz))
          xoffset = board.vis_coord[calibchip][currentz][0] \
                  - board.lumi_coord[calibchip][closestz][0]
          yoffset = board.vis_coord[calibchip][currentz][1] \
                  - board.lumi_coord[calibchip][closestz][2]

      ## If Lumi coordinate exists, use the lumi coordinate (closest z value if multiple values exist s)
      if any(cmdsession.board.lumi_coord[arg.chipid]):
        closestz = min(
            board.lumi_coord[arg.chipid].keys(), key=lambda x: abs(x - currentz))
        arg.x = board.lumi_coord[arg.chipid][closestz][0]
        arg.y = board.lumi_coord[arg.chipid][closestz][2]
      # Else if visual coordinates exists, move to visual cooridnate with
      # offset subtracted, the operating z value must have a matching
      # entry in the vis coordinates, otherwise there will be mismatches
      elif currentz in cmdsession.board.vis_coord[arg.chipid]:
        arg.x = board.vis_coord[arg.chipid][currentz][0] - xoffset
        arg.y = board.vis_coord[arg.chipid][currentz][1] - yoffset
      else:
        arg.x, arg.y = cmdsession.board.orig_coord[arg.chipid]

      ## Adding back the horizontal offset if specified
      if add_visoffset:
        arg.x += xoffset
        arg.y += yoffset
  else:
    arg.chipid = "-100"  ## Assuming some calibration chip is not specified
    if not arg.x: arg.x = cmdsession.gcoder.opx
    if not arg.y: arg.y = cmdsession.gcoder.opy


def make_hscan_mesh(arg):
  """
  Common argument for generating x-y scanning coordinate mesh
  """
  gantrymin = 1
  gantrymax = 450

  if (arg.x - arg.range < gantrymin or arg.x + arg.range > gantrymax
      or arg.y - arg.range < gantrymin or arg.y + arg.range > gantrymax):
    log.printwarn(("The arguments placed will put the gantry past it's limits, "
                   "the command will used modified input parameters"))

  xmin = max([arg.x - arg.range, gantrymin])
  xmax = min([arg.x + arg.range, gantrymax])
  ymin = max([arg.y - arg.range, gantrymin])
  ymax = min([arg.y + arg.range, gantrymax])
  sep = max([arg.distance, 0.1])
  xmesh, ymesh = np.meshgrid(
      np.linspace(xmin, xmax, (xmax - xmin) / sep + 1),
      np.linspace(ymin, ymax, (ymax - ymin) / sep + 1))
  return [
      xmesh.reshape(1, np.prod(xmesh.shape))[0],
      ymesh.reshape(1, np.prod(ymesh.shape))[0]
  ]


def parse_zscan_options(arg):
  arg.zlist = " ".join(arg.zlist)
  braces = re.findall("\[(.*?)\]", arg.zlist)
  arg.zlist = re.sub('\[(.*?)\]', '', arg.zlist)
  arg.zlist = [float(z) for z in arg.zlist.split()]
  for rstring in braces:
    r = [float(rarg) for rarg in rstring.split()]
    if len(r) < 2 or len(r) > 3:
      raise Exception('Range must be in the format [start end (sep)]'\
                      'sep is assumed to be 1 if not specified')
    minz = min(r[:2])
    maxz = max(r[:2])
    sep = 1 if len(r) == 2 else r[2]
    arg.zlist.extend(np.linspace(minz, maxz, (maxz - minz) / sep + 1))
  arg.zlist.sort() ## Returning sorted result


def timestamp_filename(prefix, arg, add_attributes = []):
  tags = ""
  for attr in add_attributes:
    if hasattr(arg, attr):
      tags += "_" + attr + str(getattr(arg, attr))

  if arg.chipid.startswith('-'):
    return '{0}{1}_{2}.txt'.format(
        prefix, tags,
        datetime.datetime.now().strftime('%Y%m%d_%H00'))
  else:
    return '{0}_{1}{2}_{3}.txt'.format(
        prefix, 'chip%s'.format(arg.chipid), tags,
        datetime.datetime.now().strftime('%Y%m%d_%H00'))


if __name__ == "__main__":
  s = '[1 2 3] 5 6 7 8 9] [10 12 14]'
  s = re.sub("\[(.*?)\]", '', s)
  s = [float(z) for z in s.split()]
  print(s)
