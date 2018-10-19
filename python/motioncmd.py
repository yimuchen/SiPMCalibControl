import python.cmdbase as cmdbase
import python.gcoder as gcoder
import argparse


class moveto(cmdbase.controlcmd):
  """
  Moving the gantry head to a specific location, either by chip ID or by raw
  x-y-z coordinates. Units for the x-y-z inputs is millimeters.
  """
  def __init__(self):
    cmdbase.controlcmd.__init__(self)
    self.parser.add_argument(
      "-x",type=float,
      help="Specifying the X coordinate (remains unchanged if not specificed)")
    self.parser.add_argument(
      "-y",type=float,
      help="Specifying the Y coordinate (remains unchanged if not specificed)")
    self.parser.add_argument(
      '-chip',type=int,
      help="Moving to the specific chip location on the present board layout, overrides the settings given by the x,y settings")
    self.parser.add_argument(
      "-z",type=float,
      help="Specifying the Z coordinate (remains unchanged if not specificed). Can be used together with -chip options")

  def parse(self,line):
    arg=cmdbase.controlcmd.parse(self,line)

    if arg.chip :
      if not self.cmd.board.has_chip(arg.chip):
        print("""Warning chip of ID is not defined in board type! Not using chip ID to change target position""")
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
    if arg.x == None : arg.x = float('nan')
    if arg.y == None : arg.y = float('nan')
    if arg.z == None : arg.z = float('nan')
    if arg.x != arg.x and arg.y != arg.y and arg.z != arg.z:
      raise Exception("""No coordinate specified! exiting command.""")

    return arg

  def run(self,arg):
    self.cmd.gcoder.move_to_position(arg.x, arg.y, arg.z )

class movespeed(cmdbase.controlcmd):
  """
  Setting the motion speed of the gantry x-y-z motors. Units in mm/s.
  """
  def __init__(self):
    cmdbase.controlcmd.__init__(self)
    self.parser.add_argument('-x',type=float,
      help='motion speed of gantry in x axis ')
    self.parser.add_argument('-y',type=float,
      help='motion speed of gantry in y axis ')
    self.parser.add_argument('-z',type=float,
      help='motion speed of gantry in z axis ')

  def parse(self,line):
    arg = cmdbase.controlcmd.parse(self,line)
    # Filling with NAN for missing settings.
    if not arg.x :  arg.x = float('nan')
    if not arg.y :  arg.y = float('nan')
    if not arg.z :  arg.z = float('nan')

    return arg

  def run(self,arg):
    self.cmd.gcoder.set_speed_limit(arg.x,arg.y,arg.z)
