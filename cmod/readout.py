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
    elif self.mode == readout.MODE_ADC:
      # Model readout is modelled directly into the adc function.
      return self.read_adc(channel, samples)
    else:
      return self.read_model(channel, samples)

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
    return np.mean(val), np.std(val)

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
    N_mean = readout.GetNumPixels(r0=r0, z=z)

    pe_list = readout.GetGPList(N_mean, samples)

    return readout.GAIN * np.mean(pe_list), readout.GAIN * np.std(pe_list)

  def read_pico(self, channel=0, samples=10000):
    """
    Averaged readout of the picoscope
    """

    ## Running the large capture routine
    self.pico.setblocknums(samples, self.pico.postsamples, self.pico.presamples)
    self.pico.startrapidblocks()
    while not self.pico.isready():
      self.parent.gpio.pulse(self.pico.ncaptures, 100)
    self.pico.flushbuffer()
    val = [self.pico.waveformsum(channel, x) for x in range(samples)]
    return np.mean(val), np.std(val) / np.sqrt(samples)

  # Constants for fake model
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

  def GetNumPixels(r0, z):
    N0 = 2000 * 10
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

  def calc_general_poisson(x, mean, Lambda):
    y = mean + x * Lambda
    ans = 0
    for index in range(1, int(x) + 1):
      ans = ans + np.log(y) - np.log(index)
    ans = ans + np.log(mean) - np.log(y)
    return np.exp(-y + ans)


if __name__ == "__main__":
  import matplotlib.pyplot as plt

  N_Points = 100000
  k_list = readout.GetGPList(2.5, N_Points)
  r_list = readout.GetSmearedGP(k_list)

  fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
  axs[0].hist(k_list, bins=100, log=True)
  axs[1].hist(r_list, bins=100, log=True)
  plt.show()
