"""
Practice script for sampling scan correction.
"""
from cmod.TBController import TBController
import numpy as np
import awkward as ak
import uproot


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


if __name__ == '__main__':
  tbc = TBController()
  # Obtain these numbers from the server start up instance.
  tbc.init('10.42.0.63',
           daq_port=6000,
           cli_port=6001,
           i2c_port=5555,
           config_file='cfg/tbc_yaml/roc_config_ConvGain4.yaml')

  # Additional settings for the data acquisition fast controls

  calibreq = 0x10
  tbc.daq_socket.enable_fast_commands(A=1)
  tbc.daq_socket.l1a_generator_settings(name='A',
                                        BX=calibreq,
                                        length=1,
                                        cmdtype='CALIBREQ',
                                        prescale=0,
                                        followMode='DISABLE')

  data = None

  #for BX in range(calibreq + 19, calibreq + 20):
  for BX in range(calibreq + 19, calibreq + 24):
    tbc.daq_socket.l1a_generator_settings(name='B',
                                          BX=BX,
                                          length=1,
                                          cmdtype='L1A',
                                          prescale=0,
                                          followMode='A')

    for phase in range(0, 16):
      tbc.i2c_socket.yaml_config['roc_s0']['sc']['Top']['all']['Phase'] = phase
      tbc.i2c_socket.configure()
      tbc.i2c_socket.reset_tdc()  # Reset MasterTDCs

      data_single = tbc.acquire(500)
      data_single['time'] = 25. * (BX - calibreq - 20) + 25. / 16. * phase
      if data is None:
        data = data_single
      else:
        data = ak.concatenate([data, data_single], axis=0)
      print('Completed scan for ', (BX, phase))

  with uproot.recreate('mytest.root') as f:
    f['hgcroc'] = {k: data[k] for k in data.fields}

  print(data)