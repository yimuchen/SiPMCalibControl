#!/usr/bin/env python3
import python.cmdbase as cmdbase
import python.motioncmd as motioncmd
import python.getset as getset
import python.logger as logger
import argparse
import copy
import sys

if __name__ == '__main__':
  cmd = cmdbase.controlterm([
    motioncmd.moveto,
    motioncmd.movespeed,
    motioncmd.findchip,
    motioncmd.fscan,
    getset.set,
    getset.get,
    ])

  """
  Duplicating the session to allow for default override.
  """
  prog_parser = copy.copy(cmd.set.parser)

  # Augmenting help messages
  prog_parser.prog = "control.py"
  prog_parser.add_argument(
    '-h','--help',action='store_true',
    help='print help message and exit')

  # Overriding default values
  for action in prog_parser._actions:
    if '-printerdev' in action.option_strings:
      action.default = '/dev/ttyUSB0'

  args = prog_parser.parse_args()

  if args.help :
    prog_parser.print_help()
    sys.exit(0)

  try:
    cmd.set.run(args)
  except Exception as err:
    logger.printerr(str(err))
    logger.printwarn("There was error in the setup process, program will " "continue but will most likely misbehave! Use at your own risk!")

  cmd.cmdloop()
