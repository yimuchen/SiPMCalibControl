import python.cmdbase as cmdbase
import python.gcodestream as gcodestream
import python.session as session
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
      if not session.calibsession.get_chipposition(arg.chip):
        print("""Warning chip of ID is not defined in board type! Not using chip ID to change target position""")
        session.calibsession.opchip = None
      else:
        if arg.x or arg.y:
          print("Warning! Overriding user defined x,y with chip coordinates!")
        [arg.x, arg.y]= session.calibsession.get_chipposition(arg.chip)
        session.calibsession.opchip = arg.chip
        arg.__delattr__('chip')
    else:
      session.calibsession.opchip = None

    ## Filling with NAN for no motion.
    if not arg.x : arg.x = float('nan')
    if not arg.y : arg.y = float('nan')
    if not arg.z : arg.z = float('nan')
    if arg.x != arg.x and arg.y != arg.y and arg.z != arg.z:
      raise Exception("""No coordinate specified! exiting command.""")

    return arg

  def run(self,arg):
    gcodestream.move_to_position(arg.x, arg.y, arg.z )

