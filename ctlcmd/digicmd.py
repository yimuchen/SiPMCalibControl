import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
import time


class pulse(cmdbase.controlcmd):
  """
  Running the pulser over some set value
  """

  LOG = log.GREEN('[PULSE]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('-n',
                             type=int,
                             default=100000,
                             help='number of times to pulse the signal')
    self.parser.add_argument('--wait',
                             type=int,
                             default=500,
                             help='Time (in microseconds) between triggers')

  def run(self, args):
    self.init_handle()

    for i in range(args.n):
      self.check_handle(args)
      self.gpio.pulse(1, args.wait)


class pwm(cmdbase.controlcmd):
  """
  Changing the pwm duty cycle and frequency
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('--channel',
                             '-c',
                             type=int,
                             choices=[0, 1],
                             help='PWM channel to alter')
    self.parser.add_argument('--duty', '-d', type=float, help='Duty cycle')
    self.parser.add_argument('--frequency',
                             '-f',
                             type=float,
                             default=1000000,
                             help='Base frequency of the PWM')

  def parse(self, line):
    args = cmdbase.controlcmd.parse(self, line)
    if args.channel == None:
      raise Exception('Channel required')
    if args.duty == None:
      raise Exception('Duty cycle required')
    return args

  def run(self, args):
    self.gpio.pwm(args.channel, args.duty, args.frequency)


class showadc(cmdbase.controlcmd):
  """
  Printing the ADC values that are stored in memory
  """

  LOG = log.GREEN("[SHOWADC]")

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)
    self.parser.add_argument('--time',
                             '-t',
                             default=10,
                             type=float,
                             help='Time to run command [seconds]')
    self.parser.add_argument('--interval',
                             '-i',
                             type=float,
                             default=1,
                             help='Time interval between updates [seconds]')

  def run(self, args):
    self.init_handle()
    start_time = time.time()
    end_time = time.time()
    while (end_time - start_time) < args.time:
      self.check_handle(args)
      self.update('{0} | {1} | {2} | {3}'.format(
          'LED TEMP:{0:5.2f}C ({1:5.1f}mV)'.format(self.gpio.ntc_read(0),
                                                   self.gpio.adc_read(0)),
          'SiPM TEMP:{0:5.2f}C ({1:5.1f}mV)'.format(self.gpio.rtd_read(1),
                                                    self.gpio.adc_read(1)),
          'PWM0: {0:6.4f}V'.format(
              self.gpio.adc_read(2) / 1000), 'PWM1: {0:6.4f}V'.format(
                  self.gpio.adc_read(3) / 1000)))
      time.sleep(args.interval)
      end_time = time.time()
