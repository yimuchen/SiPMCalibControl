import ctlcmd.cmdbase as cmdbase
import cmod.logger as log


class picoset(cmdbase.controlcmd):
  """
  Setting session parameters
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('--range',
                             type=int,
                             help=('Voltage range by index, use command '
                                   '"get --pico" for the list of available '
                                   'numbers'))

    ## Trigger related settings
    self.parser.add_argument('--triggerchannel',
                             type=int,
                             help=('Index representing which channel to trigger '
                                   'on. See the outputs of "get --pico" for the'
                                   ' available numbers'))
    self.parser.add_argument('--triggerdirection',
                             type=int,
                             help=('Index representing the direction of the '
                                   'trigger. See the outputs of "get --pico" '
                                   'for the available numbers'))
    self.parser.add_argument('--triggerlevel',
                             type=float,
                             help=('Trigger level in mV. Note that the value '
                                   'will be rounded to the closest '
                                   'corresponding ADC value.'))
    self.parser.add_argument('--triggerdelay',
                             type=int,
                             help=('Delay between trigger and data acquisition, '
                                   'units in 10 time intervals (see the outputs '
                                   'of "get --pico" to get time intervals in '
                                   'nanoseconds)'))
    self.parser.add_argument('--waittrigger',
                             type=int,
                             help=('Maximum wait time for a single trigger '
                                   'fire, units in (ms). Set to 0 for '
                                   'indefinite trigger wait.'))

    ## Data collection settings
    self.parser.add_argument('--presamples',
                             type=int,
                             help=('Number of samples to collect before data '
                                   'collection trigger (takes into account '
                                   'delay)'))
    self.parser.add_argument('--postsamples',
                             type=int,
                             help=('Number of samples to collect after data '
                                   'collection trigger (takes into account '
                                   'delay)'))
    self.parser.add_argument('--ncaptures',
                             type=int,
                             help=('Number of triggered capture to perform in '
                                   'a single block'))

  def set_trigger(self, args):
    if args.triggerchannel == None:
      args.triggerchannel = self.pico.triggerchannel
    if args.triggerdirection == None:
      args.triggerdirection = self.pico.triggerdirection
    if args.triggerlevel == None:
      args.triggerlevel = self.pico.triggerlevel
    if args.triggerdelay == None:
      args.triggerdelay = self.pico.triggerdelay
    if args.waittrigger == None:
      args.waittrigger = self.pico.triggerwait
    if (args.triggerchannel != self.pico.triggerchannel
        or args.triggerdirection != self.pico.triggerdirection
        or args.triggerlevel != self.pico.triggerlevel
        or args.triggerdelay != self.pico.triggerdelay
        or args.waittrigger != self.pico.triggerwait):
      self.pico.settrigger(args.triggerchannel, args.triggerdirection,
                           args.triggerlevel, args.triggerdelay,
                           args.waittrigger)

  def set_blocks(self, args):
    if args.presamples == None:
      args.presamples = self.pico.presamples
    if args.postsamples == None:
      args.postsamples = self.pico.postsamples
    if args.ncaptures == None:
      args.ncaptures = self.pico.ncaptures
    if (args.presamples != self.pico.presamples
        or args.postsamples != self.pico.postsamples
        or args.ncaptures != self.pico.ncaptures):
      self.pico.setblocknums(args.ncaptures, args.postsamples, args.presamples)

  def run(self, args):
    ## Voltage range stuff
    if args.range:
      self.pico.setrange(args.range)

    self.set_trigger(args)
    self.set_blocks(args)


class picorunblock(cmdbase.controlcmd):
  """
  Initiating a single run block instance. This assumes that the program will
  finish without user intervension (no program fired triggering)
  """

  DEFAULT_SAVEFILE = 'picoblock_<TIMESTAMP>.txt'
  LOG = log.GREEN('[PICOBLOCK]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.add_savefile_options(picorunblock.DEFAULT_SAVEFILE)
    self.parser.add_argument('--numblocks',
                             type=int,
                             default=1,
                             help='Number of rapid block acquisitions to run')
    self.parser.add_argument('--dumpbuffer',
                             action='store_true',
                             help='Dumping the buffer onto screen')
    self.parser.add_argument('--channel',
                             type=int,
                             default=0,
                             help='Channel to collect input from')
    self.parser.add_argument('--sum',
                             action='store_true',
                             help=('Store the sum of the waveform values '
                                   'instead of waveforms itself'))

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_savefile(args)
    return args

  def run(self, args):
    self.init_handle()
    ## First line in file contains convertion information
    if args.savefile.tell() == 0:
      args.savefile.write("{0} {1} {2} {3} {4} {5}\n".format(
          self.pico.timeinterval, self.pico.ncaptures, self.pico.presamples,
          self.pico.postsamples, self.pico.adc2mv(1), self.cmd.ndfilter))
      args.savefile.flush()

    for i in range(args.numblocks):
      self.update('Collecting block...[{0:5d}/{1:d}]'.format(
          i,
          args.numblocks,
      ))
      self.pico.startrapidblocks()

      while not self.pico.isready():
        self.check_handle(args)
        self.gpio.pulse(int(self.pico.ncaptures / 10), 500)

      self.pico.flushbuffer()

      lines = [
          self.pico.waveformstr(args.channel, cap)
          for cap in range(self.pico.ncaptures)
      ]
      args.savefile.write("\n".join(lines))

    # Closing
    args.savefile.flush()
    args.savefile.close()

    if args.dumpbuffer:
      self.pico.dumpbuffer()


class picorange(cmdbase.controlcmd):
  """
  Automatically setting the voltage range of the pico-scope based on a few waveforms of data.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('--captures',
                             type=int,
                             default=500,
                             help='Number of captures for base the calculation')
    self.parser.add_argument('--channel',
                             type=int,
                             default=0,
                             help='Input channel to base the calculation')

  def run(self, args):
    # Setting the new number of block to run
    self.pico.setblocknums(args.captures, self.pico.postsamples,
                           self.pico.presamples)

    while 1:
      self.pico.startrapidblocks()
      while not self.pico.isready():
        self.gpio.pulse(self.pico.ncaptures, 500)
      self.pico.flushbuffer()

      wmax = self.pico.waveformmax(args.channel)

      if wmax < 100 and self.pico.range > self.pico.rangemin():
        self.pico.setrange(self.pico.range - 1)
      elif wmax > 200 and self.pico.range < self.pico.rangemax():
        self.pico.setrange(self.pico.range + 1)
      else:
        break
