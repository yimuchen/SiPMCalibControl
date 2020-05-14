import cmod.logger as log
import numpy as np
import time
from scipy import stats
from scipy import special


## Random number distribution for generating fake data
class APDistribution(stats.rv_continuous):
  """
  After pulsing distribution function (Unsmeared!)
  Smearing can be done by Adding a guassian random number later
  """
  def __init__(self, i, k, beta):
    stats.rv_continuous.__init__(self, a=0, b=5 * beta)
    self.i = i
    self.k = k
    self.beta = beta

  def _cdf(self, x):
    return special.gammainc(self.i, x / self.beta)


class DarkCurrentDistribution(stats.rv_continuous):
  """
  Dark current distribution (Unsmeared!)
  Smearing can be done by adding a Gaussian random number later
  """
  def __init__(self, gain, epsilon):
    stats.rv_continuous.__init__(self, a=epsilon, b=gain - epsilon)

  def _cdf(self, x):
    eps = self.a
    gain = self.a + self.b
    return (np.log(x / (gain - x)) + np.log((gain - eps) / eps)) / (2 * np.log(
        (gain - eps) / eps))


class readout(object):
  """
  Object for defining readout interface
  """

  # Constants for mode configuration
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
    elif mode == readout.MODE_ADC and self.gpio.adc_status():
      self.mode = readout.MODE_ADC
    else:
      self.mode = readout.MODE_NONE

  def read(self, channel=0, samples=1000, average=True):
    """
    Getting the readout of the current configuration with <sample> samples of
    the a specific channel.
    If average is set to true, this function will return the averaged value and
    the RMS of all samples. Otherwise this function will return the full list of
    numbers obtained in the readout.
    For picoscope readouts, this functions integrates over the entire available
    window, so make sure that you have set the correct picoscope settings.
    """

    readout_list = []

    if self.mode == readout.MODE_PICO:
      readout_list = self.read_pico(channel, samples)
    elif self.mode == readout.MODE_ADC:
      readout_list = self.read_adc(channel, samples)
    else:
      readout_list = self.read_model(channel, samples)

    if average:
      return np.mean(readout_list), np.std(readout_list)
    else:
      return readout_list

  def read_adc(self, channel=0, samples=100):
    """
    Getting the averaged readout from the ADC chip
    """
    val = []
    for i in range(samples):
      val.append(self.gpio.adc_read(channel))
      ## Sleeping for random time in ADC to avoid 60Hz aliasing
      time.sleep(1 / 200 * np.random.random())
    return val

  def read_adc_raw(self, channel):
    """
    Reading a single ADC value from ADC chip
    """
    return self.gpio.adc_read(channel)

  def read_model(self, channel, samples):
    x = self.parent.gcoder.opx
    y = self.parent.gcoder.opy
    z = self.parent.gcoder.opz

    chip_x = self.parent.board.orig_coord[str(channel)][0]
    chip_y = self.parent.board.orig_coord[str(channel)][1]

    r0 = ((x - chip_x)**2 + (y - chip_y)**2)**0.5
    pwm_val = self.parent.gpio.pwm_duty(0)

    if channel >= 0 or channel % 2 == 0:
      ## This is a typical readout, expcet a SiPM output,
      N_mean = readout.GetNumPixels(r0=r0, z=z, pwm=pwm_val)
      pe_list = readout.GetGPList(N_mean, samples)
      return readout.GetSmearedGP(pe_list)
    else:
      ## This is a linear photo diode readout
      readout_mean = readout.GetPhotoDiodeValue(r0=r0, z=z, pwm=pwm_val)
      return np.random.normal(readout_mean, readout.GAIN / 2, samples)

  def read_pico(self, channel=0, samples=10000):
    """
    Averaged readout of the picoscope
    """

    val = []
    while len(val) < samples:
      self.pico.setblocknums(1000, self.pico.postsamples, self.pico.presamples)
      self.pico.startrapidblocks()
      while not self.pico.isready():
        self.parent.gpio.pulse(self.pico.ncaptures, 100)
      self.pico.flushbuffer()
      val.extend(self.pico.waveformsum(channel, x) for x in range(1000))
    return val

  # Constants for fake model
  ZMIN = 10
  NPIX = 1000  ## Maximum number of pixels
  GAIN = 120
  LAMBDA = 0.03
  AP_PROB = 0.08
  SIGMA0 = 0.04
  SIGMA1 = 0.01
  BETA = 60
  EPSILON = 0.005
  DCFRAC = 0.04
  ## Defining global dark current distribution for faster computation
  DC_DISTRIBUTION = DarkCurrentDistribution(GAIN, EPSILON)

  def GetNumPixels(r0, z, pwm):
    N0 = readout.NPIX * 3 * readout.ZMIN**2 * readout.PWMMultiper(pwm)
    Nraw = N0 * z / (r0**2 + z**2)**1.5
    return readout.NPIX * (1 - np.exp(-Nraw / readout.NPIX))

  def GetGPList(N_mean, samples):
    """
    Generating a list of discharges using the Generalized poisson function.
    """
    N_sqrt = np.sqrt(N_mean)
    k_min = max([min([0, N_mean - 3 * N_sqrt]), 0])
    k_max = N_mean + 3 * N_sqrt + 10
    k_list = np.arange(k_min, k_max)
    GP_list = [
        readout.calc_general_poisson(k, N_mean, readout.LAMBDA) for k in k_list
    ]
    GP_list = GP_list / np.sum(GP_list)  ## Additional normalization
    GPoisson = stats.rv_discrete('GeneralizedPoisson', values=(k_list, GP_list))
    # Defining the Generalized Poisson distribution

    return GPoisson.rvs(size=samples)

  def GetSmearedGP(GPList):
    """
    Smearing discharge peaks using Gaussian, after pulsing and dark current
    """
    ans = []
    for k in GPList:
      x = readout.GAIN * k
      if k != 0:
        APCount = stats.binom.rvs(k, readout.AP_PROB)
        smear = np.sqrt(readout.SIGMA0**2 + k * readout.SIGMA1**2)

        if APCount == 0:
          x = x + np.random.normal(0, smear)
        else:
          ap = APDistribution(APCount, k, readout.BETA)
          x = x + ap.rvs() + np.random.normal(0, smear)
      else:
        dc = np.random.random()
        if dc < readout.DCFRAC:
          smear = np.sqrt(readout.SIGMA0**2 + readout.SIGMA1**2)
          x = x + readout.DC_DISTRIBUTION.rvs() + np.random.normal(0, smear)
        else:
          x = x + np.random.normal(0, readout.SIGMA0)

      ans.append(x)
    return ans

  def GetPhotoDiodeValue(r0, z, pwm):
    ## Setting this to have the same readout value at the low light end for
    ## Easier comparison.
    N0 = readout.NPIX * 3 * readout.ZMIN * 2 * readout.PWMMultiper(pwm)
    return readout.GAIN * N0 * z / (r0**2 + z**2)**1.5

  def PWMMultiper(duty):
    return 0.5 * (1 + duty**2)

  def calc_general_poisson(x, mean, Lambda):
    y = mean + x * Lambda
    ans = 0
    for index in range(1, int(x) + 1):
      ans = ans + np.log(y) - np.log(index)
    ans = ans + np.log(mean) - np.log(y)
    return np.exp(-y + ans)
