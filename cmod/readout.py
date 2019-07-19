import cmod.logger as log
import numpy as np
import time

try:
  import board
  import busio
  import adafruit_ads1x15.ads1115 as ads
  import adafruit_ads1x15.ads1x15 as adsset
  from adafruit_ads1x15.analog_in import AnalogIn
except:
  pass  # Errors will be displayed when constructing the objects


class readout(object):
  """
  Object for defining readout interface
  """

  def __init__(self, parent):
    self.parent = parent
    self.pico = parent.pico ## Reference to picoscope for

    try:
      self.i2c = busio.I2C(board.SCL, board.SDA)
      self.adc = ads.ADS1115(
          self.i2c, data_rate=860, mode=adsset.Mode.CONTINUOUS)
    except Exception as err:
      self.i2c = None
      self.adc = None
      log.printerr(str(err))
      log.printwarn(
          ("You are not working in a I2C compatible environment, Readout "
           "values for ADC will use a predefined model instead"))

  def read_adc(self, channel=0, sample=100):
    "Large sampling read"
    val = []
    for i in range(sample):
      val.append( self.read_adc_raw(channel) )
      ## Sleeping for random time in ADC to avoid 60Hz aliasing
      time.sleep(1 / 50 * np.random.random())
    valmean = np.mean(val)
    valstd  = np.std(val)
    valstrip = [ x for x in val if abs(x-valmean) < valstd ]
    # val = val[int(sample / 4):]
    return np.mean(val), np.std(val)


  def read_adc_raw(self, channel):
    """
    Reading a single ADC value from ADC chip
    """
    if self.adc:
      return AnalogIn(self.adc, ads.P0).voltage * 1000
    else:
      return self.modelval()

  def modelval(self):
    x = self.parent.gcoder.opx
    y = self.parent.gcoder.opy
    z = self.parent.gcoder.opz

    x0 = 210
    y0 = 140
    z0 = 10

    D = (x - x0)**2 + (y - y0)**2 + (z + z0)**2
    return (100000 * (z + z0) / D**(3 / 2)) + 100 + 10 * np.random.random()
