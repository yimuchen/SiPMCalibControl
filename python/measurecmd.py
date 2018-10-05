import python.cmdbase as cmdbase
import python.tdaq as tdaq
import python.session as session
import argparse

class measure(cmdbase.controlcmd):
  "Performing a single measurement"

  def __init__(self):
    cmdbase.controlcmd.__init__(self)

  def run(self,arg):
    data = tdaq.measure_once()
    print("RECIEVED DATA: " + data )