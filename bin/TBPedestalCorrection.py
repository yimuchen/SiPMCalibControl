"""
Practice script for pedestal correction.
"""
from cmod.TBController import TBController
import numpy as np
import awkward as ak
from scipy.optimize import curve_fit


def get_pedestal(tbc, n_events=2000):
  """
  Getting the current pedestal values. Returning values as a dictionary of
  channel to pedestal/RMS tuple. Currently we will only be keeping results from
  channels 1 to 11
  """
  arr = tbc.acquire(n_events=10000)  # Getting 10K events

  return {
      channel: (np.mean(arr.adc[arr.channel == channel]),
                np.std(arr.adc[arr.channel == channel]))
      for channel in range(1, 12)
  }


def get_dacb(tbc):
  """
  Returning the DACB channels as a dictionary of channel to bit value
  """
  return {
      channel: tbc.i2c_socket.yaml_config['roc_s0']['sc']['ch'][channel]['Dacb']
      for channel in range(1, 12)
  }


def set_dacb(tbc, new_dacb):
  for channel in new_dacb.keys():
    tbc.i2c_socket.yaml_config['roc_s0']['sc']['ch'][channel]['Dacb'] = new_dacb[
        channel]

  tbc.i2c_socket.configure()  # Flushing settings to


def find_corrected_dacb(scan, target=70.0):
  def lin_f(x, a, b):
    return a * x + b

  ret = {}

  for ch in range(1, 12):
    x = [b for b in scan[ch].keys()]
    y = [v[0] for v in scan[ch].values()]
    ye = [v[1] for v in scan[ch].values()]

    p, c = curve_fit(lin_f, x, y, sigma=ye)

    ret[ch] = round((target - p[1])/p[0])

  return ret


if __name__ == '__main__':
  tbc = TBController()
  # Obtain these numbers from the server start up instance.
  tbc.init('10.42.0.63',
           daq_port=6000,
           cli_port=6001,
           i2c_port=5555,
           config_file='cfg/tbc_yaml/roc_config_ConvGain4.yaml')

  # Additional settings for the data acquisition fast controls
  tbc.daq_socket.enable_fast_commands(random=1)
  tbc.daq_socket.l1a_settings(bx_spacing=45)

  default_dacb = get_dacb(tbc)

  scan = {ch: {} for ch in range(1, 12)}

  for shift in range(-3, 4):
    print('Testing for shift value', shift)
    updated_dacb = {c: v + shift for c, v in default_dacb.items()}
    set_dacb(tbc, updated_dacb)
    ped_vals = get_pedestal(tbc)
    for ch in range(1, 12):
      scan[ch][updated_dacb[ch]] = ped_vals[ch]

  corrected_dacb = find_corrected_dacb(scan)


  set_dacb(tbc, default_dacb)
  print('Orig Ped', get_pedestal(tbc))

  set_dacb(tbc, corrected_dacb)
  print('Correct Ped', get_pedestal(tbc))
