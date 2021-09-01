#!/usr/bin/env python3
import ctlcmd.cmdbase as cmdbase
import ctlcmd.motioncmd as motioncmd
import ctlcmd.getset as getset
import ctlcmd.digicmd as digicmd
import ctlcmd.viscmd as viscmd
import ctlcmd.picocmd as picocmd
import ctlcmd.drscmd as drscmd
import cmod.logger as logger
import copy
import sys
import traceback
import re

if __name__ == '__main__':
  cmd = cmdbase.controlterm([
      motioncmd.rungcode,  #
      motioncmd.moveto,  #
      motioncmd.movespeed,  #
      motioncmd.enablestepper,  #
      motioncmd.disablestepper,  #
      motioncmd.sendhome,  #
      motioncmd.halign,  #
      motioncmd.zscan,  #
      motioncmd.lowlightcollect,  #
      motioncmd.timescan,  #
      motioncmd.getcoord,  #
      viscmd.visualset,  #
      viscmd.visualhscan,  #
      viscmd.visualzscan,  #
      viscmd.visualmaxsharp,  #
      viscmd.visualshowdet,  #
      viscmd.visualsaveframe,  #
      viscmd.visualcenterdet,  #
      getset.exit,  #
      getset.set,  #
      getset.get,  #
      getset.history,  #
      getset.wait,  #
      getset.savecalib,  #
      getset.loadcalib,  #
      getset.promptaction,  #
      getset.runfile,  #
      digicmd.pulse,  #
      digicmd.pwm,  #
      digicmd.setadcref,  #
      digicmd.showadc,  #
      digicmd.lighton,  #
      digicmd.lightoff,  #
      picocmd.picoset,  #
      picocmd.picorunblock,  #
      picocmd.picorange,  #
      drscmd.drsset,  #
      drscmd.drscalib,  #
      drscmd.drsrun  #
  ])
  # Duplicating the session to allow for default override.
  prog_parser = copy.deepcopy(cmd.set.parser)

  # Augmenting help messages
  prog_parser.prog = 'control.py'
  prog_parser.add_argument('-h',
                           '--help',
                           action='store_true',
                           help='print help message and exit')

  ## Using map to store Default values:
  default_overide = {
      '--printerdev': '/dev/ttyUSB0',
      '--camdev': '/dev/video0',
      #'-boardtype': 'cfg/static_calib.json',
      '--action': 'cfg/useractions.json',
      '--drsdevice': "MYDRS",  # CANNT actually set
      '--picodevice': 'MYSERIAL',  #Cannot actually set. Just dummy for now
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
    print("Running set command")
    cmd.set.run(args)
    print("Starting GPIO")
    cmd.gpio.init()
  except Exception as err:
    logger.printerr(str(err))
    logger.printwarn(
        'There was error in the setup process, program will '
        'continue but will most likely misbehave! Use at your own risk!')

  cmd.cmdloop()
  print('Exiting out of loop')
