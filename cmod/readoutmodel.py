"""

  readoutmodel.py

  A numpy/scipy based method for generation pseudo realistic readout data given
  the some seperation parameters and powering configuration.

"""
import numpy as np
import time
from scipy import stats
from scipy import special


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
    self.ap_prob = kwargs.get('ap_prob', 0.05)
    self.sig0 = kwargs.get('sig0', 20)
    self.sig1 = kwargs.get('sig1', 5)
    self.beta = kwargs.get('beta', 120 )
    self.eps = kwargs.get('eps', 0.005)
    self.dcfrac = kwargs.get('dcfrac', 0.04)
    self.dc_dist = DarkCurrentDistribution(self.gain, self.eps)

  def read_model(self, r0, z, pwm, samples):
    """
    Returning a list of readout values as if the SiPM and the lightsource has a
    r0,z separation, and the pwm is set to some duty cycle.
    """
    nfired = self._calc_npixels_fired(r0, z, pwm)
    nfired = self._make_gp_list(nfired, samples)
    return self._smear_values(nfired)

  def _calc_npixels_fired(self, r0, z, pwm):
    N0 = 500 * self.npix * _pwm_multiplier(pwm)
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
    smear = np.sqrt(self.sig0**2 + gp_list * self.sig1**2)  # Smearing the peaks
    smear = np.random.normal(loc=0, scale=smear)

    ## Getting the number of after pulses
    apcount = np.random.binomial(gp_list, self.ap_prob)
    apval = np.random.exponential(self.beta, size=(nevents, np.max(apcount)))
    _, index = np.indices((nevents, np.max(apcount)))
    apval = np.where(apcount[:, np.newaxis] > index, apval, 0)
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
    Simple linear readout model for Diodes. Scaled output to be similar with the
    SiPM model for easy comparison.
    """
    pass

  def read_model(self, r0, z, pwm, samples):
    N0 = 30000 * 1000 * 120 * _pwm_multiplier(pwm)
    mean = N0 * z / (r0**2 + z**2)**1.5
    return np.random.normal(loc=mean, scale=60 / 2, size=samples)


class DarkCurrentDistribution(stats.rv_continuous):
  """
  Unsmeared dark current distribution, as smearing can be done by adding a
  Gaussian random number in numpy
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
  print(s.read_model(0, 10, 0.5, 100))
  d = DiodeModel()
  print(d.read_model(0, 10, 0.5, 100))
