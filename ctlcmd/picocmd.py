import ctlcmd.cmdbase as cmdbase
import cmod.logger as log


class picoset(cmdbase.controlcmd):
  """
  Setting session parameters
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument(
        '--range',
        type=int,
        help=('Voltage range by index, use command "get --pico" for the list '
              'of available numbers'))
    self.parser.add_argument(
        '--triggerchannel',
        type=int,
        help=('Index representing which channel to trigger on. See the outputs '
              'of "get --pico" for the  available numbers'))
    self.parser.add_argument(
        '--triggerdirection',
        type=int,
        help=('Index representing the direction of the trigger. See the outputs '
              'of "get --pico" for the available numbers'))
    self.parser.add_argument(
        '--triggerlevel',
        type=float,
        help=('Trigger level in mV. Note that the value will be rounded to the '
              'closest corresponding ADC value.'))

    self.parser.add_argument(
        '--triggerdelay',
        type=int,
        help=('Delay between trigger and data acquisition, units in 10 time '
              'intervals (see the outputs of "get --pico" to get time intervals '
              'in nanoseconds)'))
    self.parser.add_argument(
        '--waittrigger',
        type=int,
        help=('Maximum wait time for a single trigger fire, units in (ms). Set '
              'to 0 for indefinite trigger wait.'))

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
    self.parser.add_argument(
        '--sum',
        action='store_true',
        help='Store the sum of the waveform values instead of waveforms itself')

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    self.parse_savefile(args)
    return args

  def run(self, args):
    self.init_handle()
    ## First line in file contains convertion information
    if args.savefile.tell() == 0:
      args.savefile.write("{0} {1} {2} {3} {4}\n".format(
          self.pico.timeinterval, self.pico.ncaptures, self.pico.presamples,
          self.pico.postsamples, self.pico.adc2mv(1)))
      args.savefile.flush()

    for i in range(args.numblocks):
      self.update('Collecting block...[{0:5d}/{1:d}]'.format(
          i,
          args.numblocks,
      ))
      self.pico.startrapidblocks()

      while not self.pico.isready():
        self.check_handle(args)
        self.trigger.pulse(int(self.pico.ncaptures / 10), 500)

      self.pico.flushbuffer()

      for cap in range(self.pico.ncaptures):
        line = self.pico.waveformstr(args.channel, cap)
        args.savefile.write(line + '\n')

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
        self.trigger.pulse(self.pico.ncaptures, 500)
      self.pico.flushbuffer()

      wmax = self.pico.waveformmax(args.channel)

      if wmax < 100 and self.pico.range > self.pico.rangemin():
        self.pico.setrange(self.pico.range - 1)
      elif wmax > 200 and self.pico.range < self.pico.rangemax():
        self.pico.setrange(self.pico.range + 1)
      else:
        break
