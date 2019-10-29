import cmod.logger as log
import numpy as np
import time

class readout(object):
  """
  Object for defining readout interface
  """

  MODE_PICO = 1
  MODE_ADC = 2
  MODE_NONE = -1

  def __init__(self, parent):
    self.parent = parent
    self.pico = parent.pico  ## Reference to picoscope for simplified
    self.gpio = parent.gpio
    self.mode = readout.MODE_NONE
    self.i2c = None
    self.adc = None

  def set_mode(self, mode):
    if mode == readout.MODE_PICO and self.pico.device:
      self.mode = mode
    elif mode == readout.MODE_ADC:
      self.mode == readout.MODE_ADC
    else:
      self.mode = readout.MODE_NONE

  def read(self, channel=0, samples=1000):
    """
    Getting an average value of the readout Note that this is intended to be an
    averaged + RMS return value. If you want a full readout, see the picoscope
    related commands.
    """
    if self.mode == readout.MODE_PICO:
      return self.read_pico(channel, samples)
    else:
      # Model readout is modelled directly into the adc function.
      return self.read_adc(channel, samples)

  def read_adc(self, channel=0, samples=100):
    """
    Getting the averaged readout from the ADC chip
    """
    val = []
    for i in range(samples):
      val.append(self.gpio.adc_read(channel))
      ## Sleeping for random time in ADC to avoid 60Hz aliasing
      time.sleep(1 / 200 * np.random.random())
    valmean = np.mean(val)
    valstd = np.std(val)
    valstrip = [x for x in val if abs(x - valmean) < valstd]
    # val = val[int(sample / 4):]
    return np.mean(val), np.std(val)/np.sqrt(samples)

  def read_adc_raw(self, channel):
    """
    Reading a single ADC value from ADC chip
    """
    if self.mode == readout.MODE_ADC:
      return self.gpio.adc_read( channel )
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

  def read_pico(self, channel=0, samples=10000):
    """
    Averaged readout of the picoscope
    """

    ## Running the large capture routine
    self.pico.setblocknums(samples, self.pico.postsamples, self.pico.presamples)
    self.pico.startrapidblocks()
    while not self.pico.isready():
      self.parent.gpio.pulse(self.pico.ncaptures, 600)
    self.pico.flushbuffer()
    val = [self.pico.waveformsum(channel, x) for x in range(samples)]
    return np.mean(val), np.std(val)/sqrt(samples)
