import cmod.logger as log
import numpy as np
import time

class readout(object):
  """
  Object for defining readout interface
  """

  def __init__(self, parent):
    self.parent = parent
    try:
      import Adafruit_ADS1x15
      self.adc = Adafruit_ADS1x15.ADS1115()
    except:
      self.adc = None
      log.printwarn(
          ("You are not working in a I2C compatible environment, Readout "
           "values for ADC will use a predefined model instead"))

  def read_adc(self, channel=0, sample=60):
    "Large sampling read"
    val = [0] * sample
    for i in range(sample):
      val[i] = self.read_adc_raw(channel)
    val = val[int(sample/4):]
    return np.mean(val), max(np.std(val), 0.5)

  def read_adc_raw(self, channel):
    if self.adc:
      return self.adc.read_adc(channel, gain=1)
    else:
      return self.modelval()

  def modelval(self):
    x = self.parent.gcoder.opx
    y = self.parent.gcoder.opy
    z = self.parent.gcoder.opz

    x0 = 210
    y0 = 140
    z0 = 10

    D = (x-x0)**2 + (y-y0)**2 + (z+z0)**2
    return (100000 * (z+z0) / D**(3/2)) + 100 + 10 * np.random.random()