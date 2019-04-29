import ctlcmd.cmdbase as cmdbase
import cmod.comarg as comarg
import cmod.pico as pico
import timeit  ##
import time


class picoset(cmdbase.controlcmd):
  """
  Setting session parameters
  """

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument(
        '--range',
        type=int,
        help=
        'Voltage range by index, use command "get --pico" for the list of available numbers'
    )

    self.parser.add_argument(
        '--triggerchannel',
        type=int,
        help=
        'Index representing which channel to trigger on. See the outputs of "get --pico" for the  available numbers'
    )

    self.parser.add_argument(
        '--triggerdirection',
        type=int,
        help=
        'Index representing the direction of the trigger. See the outputs of "get --pico" for the available numbers'
    )
    self.parser.add_argument(
        '--triggerlevel',
        type=float,
        help=
        'Trigger level in mV. Note that the value will be rounded to the closest corresponding ADC value.'
    )

    self.parser.add_argument(
        '--triggerdelay',
        type=int,
        help=
        'Delay between trigger and data acquisition, units in 10 time intervals (see the outputs of "get --pico" to get time intervals in nanoseconds)'
    )
    self.parser.add_argument(
        '--waittrigger',
        type=int,
        help=
        'Maximum wait time for a single trigger fire, units in (ms). Set to 0 for indefinite trigger wait.'
    )

    self.parser.add_argument(
        '--presamples',
        type=int,
        help='Number of samples to collect before the trigger')
    self.parser.add_argument('--postsamples',
                             type=int,
                             help='Number of samples to collect after trigger')
    self.parser.add_argument(
        '--ncaptures',
        type=int,
        help='Number of triggered capture to perform in a single block')

  def run(self, arg):
    ## Voltage range stuff
    if arg.range:
      self.pico.setrange(arg.range)

    if (arg.triggerdelay != None or arg.waittrigger != None
        or arg.triggerchannel != None or arg.triggerdirection != None
        or arg.triggerlevel != None):
      if arg.triggerchannel == None:
        arg.triggerchannel = self.pico.triggerchannel
      if arg.triggerdirection == None:
        arg.triggerdirection = self.pico.triggerdirection
      if arg.triggerlevel == None:
        arg.triggerlevel = self.pico.triggerlevel
      if arg.triggerdelay == None:
        arg.triggerdelay = self.pico.triggerdelay
      if arg.waittrigger == None:
        arg.waittrigger = self.pico.triggerwait
      if (arg.triggerchannel != self.pico.triggerchannel
          or arg.triggerdirection != self.pico.triggerdirection
          or arg.triggerlevel != self.pico.triggerlevel
          or arg.triggerdelay != self.pico.triggerdelay
          or arg.waittrigger != self.pico.triggerwait):
        self.pico.settrigger(arg.triggerchannel, arg.triggerdirection,
                             arg.triggerlevel, arg.triggerdelay, arg.waittrigger)

    ## Run block stuff
    if arg.presamples or arg.postsamples or arg.ncaptures:
      if arg.presamples == None:
        arg.presamples = self.pico.presamples
      if arg.postsamples == None:
        arg.postsamples = self.pico.postsamples
      if arg.ncaptures == None:
        arg.ncaptures = self.pico.ncaptures
      if (arg.presamples != self.pico.presamples
          or arg.postsamples != self.pico.postsamples
          or arg.ncaptures != self.pico.ncaptures):
        self.pico.setblocknums(arg.ncaptures, arg.postsamples, arg.presamples)


class picorunblock(cmdbase.controlcmd):
  """
  Initiating a single run block instance. This assumes that the program will finish without user intervension (no program fired triggering)
  """

  DEFAULT_SAVEFILE = 'picoblock_<TIMESTAMP>.txt'
  LOG = 'PICOBLOCK'

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    comarg.add_savefile_options(self.parser, picorunblock.DEFAULT_SAVEFILE)
    self.parser.add_argument('--numblocks',
                             type=int,
                             default=1,
                             help='Number of rapid block acquisitions to run')
    self.parser.add_argument('--dumpbuffer',
                             action='store_true',
                             help='Dumping the buffer onto screen')

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    filename = args.savefile if args.savefile != picorunblock.DEFAULT_SAVEFILE \
              else comarg.timestamp_filename('picoblock', args )

    args.savefile = self.sshfiler.remotefile(filename, args.wipefile)
    return args

  def run(self, args):
    ## First line in file contains convertion information
    if args.savefile.tell() == 0:
      args.savefile.write("{0} {1} {2} {3} {4}\n".format(
          self.pico.timeinterval, self.pico.ncaptures, self.pico.presamples,
          self.pico.postsamples, self.pico.adc2mv(1)))

    for i in range(args.numblocks):
      self.update("Collecting block...[{0:5d}/{1:d}]".format(
          i,
          args.numblocks,
      ))
      self.pico.startrapidblocks()
      self.pico.waitready()

      # Writing each capture as a single line.
      for cap in range(self.pico.ncaptures):
        buf = [
            "{0:02x}".format(
                int(self.pico.buffer(0, cap, x) / 256) & (2**8 - 1))
            for x in range(self.pico.presamples + self.pico.postsamples)
        ]
        line = "".join(buf)
        args.savefile.write(line + "\n")

    # Closing
    args.savefile.close()

    if args.dumpbuffer:
      self.pico.dumpbuffer()
