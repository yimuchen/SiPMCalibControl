import ctlcmd.cmdbase as cmdbase
import cmod.logger as log
import time

class pulse(cmdbase.controlcmd):
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
      time.sleep(args.wait/1e6)
