"""

  readoutmodel.py

  A numpy/scipy based method for generation pseudo realistic readout data given
  the some seperation parameters and powering configuration.

"""
import time

import numpy as np
from scipy import special, stats


### Helper function and classes
def _pwm_multiplier(pwm):
    """
    A very simplified models of how the PWM duty cycle should affect the total
    number of photons. Here we are using a very simple quadratic model, so that
    there will be a non-linear variation when changing duty cycles, just for
    testing the system offline.
    """
    return 0.5 * (1 + pwm**2)


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
