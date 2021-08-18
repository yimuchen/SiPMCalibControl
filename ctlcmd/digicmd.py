"""

  digicmd.py

  Commands for raw control and display of GPIO/ADC/PWM related interfaces
  functions

"""
import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
import time


class pulse(cmdbase.controlcmd):
  """
  Running the trigger for a certain about of pulses with alternative wait
  options.
  """

  LOG = log.GREEN('[PULSE]')

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('-n',
                             type=int,
                             default=100000,
                             help='number of times to fire the trigger')
    self.parser.add_argument('--wait',
                             type=int,
                             default=500,
                             help='Time (in microseconds) between triggers')

  def run(self, args):
    # Splitting into 1000 chunks
    for i in range(args.n // 100):
      self.check_handle(args)
      self.gpio.pulse(100, args.wait)


class pwm(cmdbase.controlcmd):
  """
  Changing the pwm duty cycle and frequency
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('--channel',
                             '-c',
                             type=int,
                             choices=[0, 1],
                             required=True,
                             help='PWM channel to alter')
    self.parser.add_argument('--duty',
                             '-d',
                             type=float,
                             required=True,
                             help='Duty cycle of the PWM')
    self.parser.add_argument('--frequency',
                             '-f',
                             type=float,
                             default=1000000,
                             help='Base frequency of the PWM')

  def run(self, args):
    self.gpio.pwm(args.channel, args.duty, args.frequency)


class setadcref(cmdbase.controlcmd):
  """
  Setting the reference voltage of the ADC readout for temperature conversion
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
    self.parser.add_argument('--channel',
                             '-c',
                             type=int,
                             choices=[0, 1, 2, 3],
                             nargs='+',
                             help="""Channel to set reference voltage (can set
                             multiple to same value in a single command call)""")
    self.parser.add_argument('--val',
                             '-v',
                             type=float,
                             default=5000,
                             help="""
                             Reference voltage to specified channels (units: mV)
                             """)

  def run(self, args):
    for channel in args.channel:
      self.gpio.adc_setref(channel, args.val)


class showadc(cmdbase.controlcmd):
  """
  Printing the ADC values that are stored in memory
  """

  LOG = log.GREEN("[SHOWADC]")

  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def add_args(self):
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


class lighton(cmdbase.controlcmd):
  """
  Turning the LED lights on.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def run(self, args):
    self.gpio.light_on()


class lightoff(cmdbase.controlcmd):
  """
  Turning the LED lights on.
  """
  def __init__(self, cmd):
    cmdbase.controlcmd.__init__(self, cmd)

  def run(self, line):
    self.gpio.light_off()
