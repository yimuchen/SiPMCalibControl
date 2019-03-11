import ctlcmd.cmdbase as cmdbase

class pulse(cmdbase.controlcmd):
  def __init__(self,cmd):
    cmdbase.controlcmd.__init__(self,cmd)
    self.parser.add_argument( '-n', type=int,
      default=1000000,
      help='number of times to pulse the signal')

  def run(self,arg):
    self.cmd.trigger.pulse(arg.n)
