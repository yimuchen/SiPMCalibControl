import python.cmdbase as cmdbase

class pulse(cmdbase.controlcmd):
  def __init__(self):
    cmdbase.controlcmd.__init__(self)

  def run(self,arg):
    self.cmd.trigger.pulse()
