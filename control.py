#!/usr/bin/env python3
import ctlcmd.cmdbase as cmdbase
import ctlcmd.motioncmd as motioncmd
import ctlcmd.getset as getset
import ctlcmd.digicmd as digicmd
import ctlcmd.viscmd  as viscmd
import ctlcmd.picocmd as picocmd
import cmod.logger as logger
import argparse
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
  prog_parser = copy.copy(cmd.set.parser)

  # Augmenting help messages
  prog_parser.prog = "control.py"
  prog_parser.add_argument(
      '-h', '--help', action='store_true', help='print help message and exit')

  # Overriding default values
  for action in prog_parser._actions:
    if '-printerdev' in action.option_strings:
      action.default = '/dev/ttyUSB0'
    if '-camdev' in action.option_strings:
      action.default = '/dev/video0'
    if '-boardtype' in action.option_strings:
      action.default = 'cfg/static_calib.json'
    if '-picodevice' in action.option_strings:
      action.default = 'MYSERIAL' # Cannot actually set setting to dummy for now
    #if '-remotehost' in action.option_strings:
    #  action.default = 'hepcms.umd.edu'

  args = prog_parser.parse_args()

  if args.help:
    prog_parser.print_help()
    sys.exit(0)

  try:
    cmd.set.run(args)
  except Exception as err:
    log.printerr(str(err))
    log.printwarn(
        "There was error in the setup process, program will "
        "continue but will most likely misbehave! Use at your own risk!")

  cmd.cmdloop()
