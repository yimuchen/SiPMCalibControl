#!/usr/bin/env python3
import ctlcmd.cmdbase as cmdbase
import ctlcmd.motioncmd as motioncmd
import ctlcmd.getset as getset
import ctlcmd.digicmd as digicmd
import ctlcmd.viscmd as viscmd
import ctlcmd.picocmd as picocmd
import cmod.logger as logger
import copy
import sys

if __name__ == '__main__':
  cmd = cmdbase.controlterm([
      motioncmd.moveto,
      motioncmd.movespeed,
      motioncmd.halign,
      motioncmd.zscan,
      motioncmd.showreadout,
      viscmd.visualhscan,
      viscmd.visualzscan,
      viscmd.visualmaxsharp,
      viscmd.visualshowchip,
      viscmd.visualcenterchip,
      getset.set,
      getset.get,
      getset.getcoord,
      getset.savecalib,
      getset.loadcalib,
      digicmd.pulse,
      picocmd.picoset,
      picocmd.picorunblock,
  ])
  """
  Duplicating the session to allow for default override.
  """
  # Weird bug in python 3.4 that doesn't allow deepcopy of argparser
  prog_parser = copy.deepcopy(cmd.set.parser)

  # Augmenting help messages
  prog_parser.prog = "control.py"
  prog_parser.add_argument('-h',
                           '--help',
                           action='store_true',
                           help='print help message and exit')

  ## Using map to store Default values:
  default_overide = {
      '-printerdev': '/dev/ttyUSB0',
      '-camdev': '/dev/video0',
      '-boardtype': 'cfg/static_calib.json',
      '-picodevice': 'MYSERIAL',  #Cannot actually set. Just dummy for now
      #'-remotehost' : ['hepcms.umd.edu', '']
  }

  for action in prog_parser._actions:
    for option, default in default_overide.items():
      if option in action.option_strings:
        action.default = default

  args = prog_parser.parse_args()

  if args.help:
    prog_parser.print_help()
    sys.exit(0)

  try:
    cmd.set.run(args)
  except Exception as err:
    logger.printerr(str(err))
    logger.printwarn(
        "There was error in the setup process, program will "
        "continue but will most likely misbehave! Use at your own risk!")

  cmd.cmdloop()
