#!/bin/env python
import python.cmdbase as cmdbase
import python.motioncmd as motioncmd
import python.getset as getset
import argparse
import copy
import sys

if __name__ == '__main__':
  cmd = cmdbase.controlterm([
    motioncmd.moveto,
    motioncmd.movespeed,
    getset.set,
    getset.get,
    ])

  """
  Duplicating the session to allow for default override.
  """
  prog_parser = copy.deepcopy(cmd.set.parser)

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

  cmd.set.run(args)

  #print(cmd.moveto)
  cmd.cmdloop()
