"""

Abstractions for extracting readout. Allow for all analysis-level functions to
call the same function for extracting the readout (list), regardless of the
requested readout method

"""

import argparse
import enum
import time

import numpy

from .board import ReadoutMode
from .format import _str_
from .session import Session


def add_readout_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    from .readout import ReadoutMode

    group = parser.add_argument_group(
        "Readout",
        """
        Arguments for changing the behavior of readout without directly
        interacting with the readout interfaces. Options for integration will
        only be used for waveform-like readout and will be ignored otherwise.
        """,
    )
    group.add_argument(
        "--samples",
        type=int,
        default=5000,
        help="""Number of readout samples to take for the luminosity measurement
             (default=%(default)d)""",
    )

    group.add_argument(
        "--intstart",
        type=int,
        default=0,
        help="Time slice to start integration",
    )
    group.add_argument(
        "--intstop",
        type=int,
        default=-1,
        help="Time slice to stop integration",
    )
    group.add_argument(
        "--pedstart",
        type=int,
        default=0,
        help="Time slice to define start of pedestal",
    )
    group.add_argument(
        "--pedstop",
        type=int,
        default=0,
        help="Time slice to define the end of pedestal",
    )
    return parser


def parse_readout_args(
    session: Session, args: argparse.Namespace
) -> argparse.Namespace:
    """Nothing required, kept for parity"""
    return args


def obtain_readout(session, average=True, **kwargs):
    """
    @brief Performing a readout routine with the specified arguments.

    @details Abstracting the readout method for child classes. The `average`
    flag will be used to indicate whether the list return value should be the
    list of readout values of length (args.samples) or be a 2-tuple indicating
    the avearge and (reduced) standard deviation of the raw list.

    For pausing the system we will be splitting the wait into 0.1 second
    interval to allow for the system to detect interuption signals to halt the
    system even during the wait period.
    """
    session.hw.disable_stepper(x=False, y=False, z=True)

    _method_map_ = {
        ReadoutMode.DRS.value: _read_drs,
        ReadoutMode.ADC.value: _read_adc,
        ReadoutMode.Tileboard.value: _read_tileboard,
        ReadoutMode.Model.value: _read_model,
    }

    mode = session.board.detectors[kwargs.get("detid")].mode

    readout_list = _method_map_.get(mode, _read_model)(session, **kwargs)

    session.hw.enable_stepper(x=True, y=True, z=True)

    if average:
        if _is_counting(session, **kwargs):
            return numpy.mean(readout_list), numpy.std(readout_list) / numpy.sqrt(
                len(readout_list)
            )
        else:
            return numpy.mean(readout_list), numpy.std(readout_list)
    else:
        return readout_list


def _read_adc(session, **kwargs):
    """
    @brief Implementation for reading out the ADC
    """
    val = []
    for _ in range(samples):
        val.append(session.hw.monitor_adc.read(channel))
        ## Sleeping for random time in ADC to avoid 60Hz aliasing
        time.sleep(1 / 200 * np.random.random())
    return val


def _read_drs(session, samples, channel, **kwargs):
    """
    @brief Implementation for reading out the DRS4

    @details As the DRS 4 will always effectively be in single shot mode, here we
    will contiously fire the trigger until collections have been completed.
    """
    val = []
    for _ in range(samples):
        session.hw.drs_startcollect()
        while not session.hw.drs_is_ready():
            _fire_trigger(session, n=10, wait=100)
        x = session.hw.drs_get_waveformsum(
            args.channel, args.intstart, args.intstop, args.pedstart, args.pedstop
        )
        val.append(x)

    return val


def _read_tileboard(session, samples, channel, **kwargs):
    raise NotImplementedError("Simplified readout of tileboard not yet implemented!")


def _fire_trigger(session, n=10, wait=100):
    """
    Helper function for firing trigger for the scope-like readouts.
    """
    # TODO: Handling alternate trigger modes
    try:  # For standalone runs with external trigger
        session.hw.gpio.pulse(n, wait)
    except:  # Do nothing if trigger system isn't accessible
        pass


def _is_counting(session, **kwargs):
    """
    Simple check for whether this the target readout is a counting system
    """
    det = session.board.detectors[kwargs.get("detid")]
    if det.mode == ReadoutMode.DRS.value:
        return True
    elif det.mode == ReadoutMode.ADC.value:
        return False
    elif det.mode == ReadoutMode.Tileboard.value:
        return True
    else:  # For mock readouts
        return det.readout[2]


def _read_model(session, **kwargs):
    """
    Generating a fake readout from a predefined model. Currently the position is
    hard coded into into a grid of [100,100] -- [400,400]. Notice that even
    channels are set to be SiPM-like, while the odd channels are set to be
    LED-like.
    """
    samples = kwargs.get("samples")
    det = session.board.detectors[kwargs.get("detid")]

    x, y, z = session.hw.get_coord()

    # Hard coding the "position" of the dummy inputs
    det_x, det_y = det.default_coords
    r0 = ((x - det_x) ** 2 + (y - det_y) ** 2) ** 0.5

    if _is_counting(session, **kwargs):
        return _read_sipm_model(r0, z, samples)
    else:
        return _read_diode_model(r0, z, samples)


## Static variables for generating fake signal
_MODEL_SIPM_NPIX_ = 1000
_MODEL_SIPM_GAIN_ = 120
_MODEL_SIPM_LAMBDA_ = 0.03  #
_MODEL_SIPM_APPROB = 0.05
_MODEL_SIPM_S0_ = 20
_MODEL_SIPM_S1_ = 3
_MODEL_SIPM_DC_FRAC = 0.04


def _read_sipm_model(r0: float, z: float, samples: int, power_mult: float = 1.0):
    # Getting average number of photons arriving at SiPM
    npe_avg = 1000000 * power_mult * z / (r0**2 + z**2) ** 1.5

    # Generate random number of photons according to average
    # TODO: Add generalized poisson process
    npe = numpy.random.poisson(npe_avg, size=samples)

    # Truncating to no larger than pixel count
    # TODO: Properly model ooccupancy effect
    npe = numpy.minimum(npe, _MODEL_SIPM_NPIX_)

    # Converting to readout
    readout = npe * _MODEL_SIPM_GAIN_

    # Adding simple Gaussian noise
    readout = readout + numpy.random.normal(
        0, scale=(_MODEL_SIPM_S0_**2 + npe * _MODEL_SIPM_S1_**2) ** 2
    )

    # Adding afterpulsing noise
    # TODO:

    # Adding dark current
    # TODO:

    return readout


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
        """ """
        self.npix = kwargs.get("npix", 1000)
        self.gain = kwargs.get("gain", 120)
        self.lamb = kwargs.get("lamb", 0.03)
        self.ap_prob = kwargs.get("ap_prob", 0.05)
        self.sig0 = kwargs.get("sig0", 20)
        self.sig1 = kwargs.get("sig1", 5)
        self.beta = kwargs.get("beta", 120)
        self.eps = kwargs.get("eps", 0.005)
        self.dcfrac = kwargs.get("dcfrac", 0.04)
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
        """
        Getting the number of pixels fired
        """
        N0 = 500 * self.npix * _pwm_multiplier(pwm)
        Nraw = N0 * z / (r0**2 + z**2) ** 1.5
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
        dist = stats.rv_discrete("GeneralizedPoisson", values=(k_arr, gp_prob))
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
        apcount = np.random.binomial(gp_list.astype(np.int64), self.ap_prob)
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


def _read_diode_model(r0, z, samples, power_mult=1.0):
    N0 = 30000 * 1000 * 120 * power_mult
    mean = N0 * z / (r0**2 + z**2) ** 1.5
    return numpy.random.normal(loc=mean, scale=60, size=samples)
