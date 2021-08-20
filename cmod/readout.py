import cmod.logger as log
import numpy as np
import time
from scipy import stats
from scipy import special


class Readout(object):
  """
  Interface for abstracting the readout interface under a simple method calls.
  The idea is that for mass calibration, where pedestal subtraction and such
  should already be optimized, what we would want to do is to have the user call
  readout from a certain channel of a certain readout mode to store a single list
  of numbers, allowing for a unified interface for data collection with readout
  methods.
  """

  # Constants for mode configuration
  MODE_PICO = 1
  MODE_ADC = 2
  MODE_DRS = 3
  MODE_NONE = -1

  def __init__(self, parent):
    self.parent = parent
    # Reference to the readout interfaces to be called.
    self.pico = parent.pico
    self.gpio = parent.gpio
    self.drs = parent.drs
    # For turning of gantry while reading
    self.gcoder = parent.gcoder
    self.mode = Readout.MODE_NONE
    self.i2c = None
    self.adc = None

    # Model readouts
    self.sipm = SiPMModel()
    self.diode = DiodeModel()

  def set_mode(self, mode):
    if mode == Readout.MODE_PICO and self.pico.device:
      self.mode = mode
    elif mode == Readout.MODE_ADC and self.gpio.adc_status():
      self.mode = Readout.MODE_ADC
    elif mode == Readout.MODE_DRS and self.drs.is_available():
      self.mode = Readout.MODE_DRS
    else:
      self.mode = Readout.MODE_NONE

  def read(self, channel=0, samples=1000, average=True, **kwargs):
    """
    Getting the readout of the current configuration with <sample> samples of the
    a specific channel. If average is set to true, this function will return the
    averaged value and the RMS of all samples; otherwise this function will
    return the full list of numbers obtained in the readout.

    For the picoscope and the DRS4 interfaces, additional numbers options are
    available in the keyword argument to modify the integration window and the
    pedestal subtraction window.
    """

    readout_list = []
    try:  # Stopping the stepper motors for cleaner readout
      self.gcoder.disablestepper(False, False, True)
    except:  # In case the gcode interface is not available, do nothing
      pass

    if self.mode == Readout.MODE_PICO:
      readout_list = self.read_pico(channel, samples)
    elif self.mode == Readout.MODE_ADC:
      readout_list = self.read_adc(channel, samples)
    elif self.mode == Readout.MODE_DRS:
      readout_list = self.read_drs(channel, samples)
    else:
      readout_list = self.read_model(channel, samples)

    try:  # Re-enable the stepper motors
      self.gcoder.enablestepper(True, True, True)
    except:  # In the case that the gcode interface isn't availabe, do nothing.
      pass

    if average:
      return np.mean(readout_list), np.std(readout_list)
    else:
      return readout_list

  def read_adc(self, channel=0, samples=100, **kwargs):
    """
    Getting the averaged readout from the ADC. Here we provide a random sleep
    between adc_read call to avoid any aliasing with either the readout rate or
    the slow varying fluctuations in our DC systems.
    """
    val = []
    for _ in range(samples):
      val.append(self.gpio.adc_read(channel))
      ## Sleeping for random time in ADC to avoid 60Hz aliasing
      time.sleep(1 / 200 * np.random.random())
    return val

  def read_pico(self, channel=0, samples=10000, **kwargs):
    """
    Averaged readout of the picoscope. Here we always set the blocksize to be
    1000 captures. This function will continuously fire the trigger system until
    a single rapidblock has been completed.
    """

    val = []
    while len(val) < samples:
      self.pico.setblocknums(1000, self.pico.postsamples, self.pico.presamples)
      self.pico.startrapidblocks()
      while not self.pico.isready():
        try:
          self.parent.gpio.pulse(self.pico.ncaptures, 100)
        except:
          pass
      self.pico.flushbuffer()
      val.extend(self.pico.waveformsum(channel, x) for x in range(1000))
    return val

  def read_drs(self, channel=0, samples=1000, **kwargs):
    """
    Average the readout results from the DRS4. Here we will contiously fire the
    trigger until collections have been completed.
    """
    val = []
    for i in range(samples):
      self.drs.startcollect()
      while not self.drs.is_ready():
        try:  # For standalone runs with external trigger
          self.gpio.pulse(10, 100)
        except:
          pass
      # Decent settings for drs delay 550 and 2.0 GHz sample rate.
      # Try to change programatically.
      val.append(self.drs.waveformsum(channel, 30, 100, 0, 0))

    return val

  def read_model(self, channel, samples):
    """
    Reading from a model. The location is extracted
    """
    x = self.parent.gcoder.opx
    y = self.parent.gcoder.opy
    z = self.parent.gcoder.opz

    det_x = self.parent.board.det_map[str(channel)].orig_coord[0]
    det_y = self.parent.board.det_map[str(channel)].orig_coord[1]

    r0 = ((x - det_x)**2 + (y - det_y)**2)**0.5
    pwm = self.parent.gpio.pwm_duty(0)

    if channel >= 0 or channel % 2 == 0:
      ## This is a typical readout, expect a SiPM output,
      return self.sipm.read_model(r0, z, pwm, samples)
    else:
      ## This is a linear photo diode readout
      return self.diode.read_model(r0, z, pwm, samples)

### Helper function and classes
def _pwm_multiplier(pwm):
  """
  A very simplified models of how the PWM duty cycle should affect the total
  number of photons. Here we are using a very simple quadratic model, so that
  there will be a non-linear variation when changing duty cycles, just for
  testing the system offline.
  """
  return 0.5 * (1 + pwm**2)


def _general_poisson(x, mean, lamb):
  """
  Calculating the general poisson probability of x events, given the expected
  poisson mean x and the correlating factor lamb. The x can either be an array of
  integer or an array of integer of values.
  """
  if not isinstance(x, np.ndarray):
    return _general_poisson(np.array(x, dtype=np.int64), mean, lamb)
  y = mean + x * lamb
  ans = np.log(y) * (x - 1) - special.gammaln(x + 1) + np.log(mean)
  return np.exp(-y + ans)



class SiPMModel(object):
  """
  Simple class for handling a model readout using a pre-defined model. The only
  method that will be directly exposed to the be readout should be the readout
  """
  def __init__(self, **kwargs):
    """
    """
    self.npix = kwargs.get('npix', 1000)
    self.gain = kwargs.get('gain', 120)
    self.lamb = kwargs.get('lamb', 0.03)
    self.ap_prob = kwargs.get('ap_prob', 0.08)
    self.sig0 = kwargs.get('sig0', 0.04)
    self.sig1 = kwargs.get('sig1', 0.01)
    self.beta = kwargs.get('beta', 60)
    self.eps = kwargs.get('eps', 0.005)
    self.dcfrac = kwargs.get('dcfrac', 0.04)
    self.dc_dist = DarkCurrentDistribution(self.gain,self.eps)

  def read_model(self, r0, z, pwm, samples):
    """
    Returning a list of readout values as if the SiPM and the lightsource has a
    r0,z separation, and the pwm is set to some duty cycle.
    """
    nfired = self._calc_npixels_fired(r0, z, pwm)
    nfired = self._make_gp_list(nfired, samples)
    return self._smear_values(nfired)

  def _calc_npixels_fired(self, r0, z, pwm):
    N0 = 30000 * self.npix * _pwm_multiplier(pwm)
    Nraw = N0 * z / (r0**2 + z**2)**1.5
    return self.npix * (1 - np.exp(-Nraw / self.npix))

  def _make_gp_list(self, mean, samples):
    """
    Generating a list of numbers of pixels discharged based on the total mean
    discharges using the generalized poisson function.
    """
    width = np.sqrt(mean)
    k_min = max([min([0, mean - 3 * width]), 0])
    k_max = mean + 3 * width + 10
    k_arr = np.arange(k_min, k_max)
    gp_prob = _general_poisson(k_arr, mean, self.lamb)
    gp_prob = gp_prob / np.sum(gp_prob)  ## Additional normalization
    dist = stats.rv_discrete('GeneralizedPoisson', values=(k_arr, gp_prob))
    return dist.rvs(size=samples)

  def _smear_values(self, gp_list):
    """
    Given a list of prompt discharge pixel counts. Calculate the estimated
    readout value by scaling the discharge count by the gain, and adding random
    smearing according to discharge.
    """
    nevents = len(gp_list)
    readout = gp_list * self.gain  # Scaling up by gain.
    smear = np.sqrt(self.sig0**2 + gp_list * self.sig1**2) # Smearing the peaks
    smear = np.random.normal(loc=0, scale=smear)

    ## Getting the number of after pulses
    apcount = np.random.binomial(gp_list, self.ap_prob)
    apval = np.random.exponential(self.beta, size=(nevents, np.max(apcount)))
    _, index = np.indices((nevents, np.max(apcount)))
    apval = np.where(apcount[:,np.newaxis] > index, 0, apval)
    apval = np.sum(apval, axis=-1)  # Reducing of the last index

    # Adding the dark current distributions.
    dcval = self.dc_dist.rvs(size=nevents)
    smear = np.sqrt(self.sig0**2 + self.sig1**2)  # Smearing the main peak
    dcval = dcval + np.random.normal(loc=0, scale=smear, size=nevents)
    dc = np.random.random(size=nevents)
    dcval = np.where(dc > self.dcfrac, 0, dcval)

    # Summing everything
    return readout + apval + dcval


class DiodeModel(object):
  def __init__(self, **kwargs):
    """
    This is a tset
    """
    pass

  def read_model(self, r0, z, pwm, samples):
    ## Setting this to have the same readout value at the low light end for
    ## Easier comparison.
    N0 = 30000 * 1000 * 120 * _pwm_multiplier(pwm)
    mean = N0 * z / (r0**2 + z**2)**1.5
    return np.random.normal(loc=mean, scale=60 / 2, size=samples)


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
    num = np.log(x / (gain - x)) + np.log((gain - eps) / eps)
    den = 2 * np.log((gain - eps) / eps)
    return num / den


## Simple cell for helping with unit testing
if __name__ == "__main__":
  s = SiPMModel()
  print(s.read_model(0,10,0.5,100))
  d = DiodeModel()
  print(d.read_model(0,10,0.5,100))
