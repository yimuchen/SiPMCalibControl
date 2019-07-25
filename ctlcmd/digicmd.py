import ctlcmd.cmdbase as cmdbase

class pulse(cmdbase.controlcmd):
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

  def run(self, arg):
    self.trigger.pulse(arg.n, arg.wait)
