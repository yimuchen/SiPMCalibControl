"""
  report.py

  This files is a list of function related to the generation of objects to be
  passed to the client for display.

  There are two types of information that the server will be pass to the client,
  1. report type information is generated on the fly by client requests. This is
     typically for the continuous monitoring and data display. While nice to have
     completely sync, it will not cause unexpected software behavior if the
     client/server information are not entirely in sync. The client is
     responsible for the interval of update by the selection. The response of
     these function are typically handled by ajax json requests from each client,
     and will not be shared across clients.
  2. sync type information is generate server side to ensure that displayed
     settings on the client side are identical to the server settings. These
     information need to broadcasted to all connect clients to ensure that
     software behavior is synced across all connected clients.
     These objects are defined in the sync.py python file.
"""
import datetime, os, glob, json, re, psutil
from . import session
from .format import *
import numpy as np


def report_system_status():
  """
  This is basically reporting a status that has the user has not directly control
  over and is typically used for system normality diagnostics. Notice that these
  variables are typically not fully logged in the final data storage.
  """
  return {
      'start': session.start_time.strftime('%Y/%m/%d/ %H:%M:%S'),
      'time': int(
          (datetime.datetime.now() - session.start_time).total_seconds()),
      ## Constant monitor variables
      'temp1': session.cmd.gpio.ntc_read(0),
      'temp2': session.cmd.gpio.rtd_read(1),
      'volt1': session.cmd.gpio.adc_read(2),
      'volt2': session.cmd.gpio.adc_read(3),
      'coord':
      [session.cmd.gcoder.cx, session.cmd.gcoder.cy, session.cmd.gcoder.cz],
  }


def report_tileboard_layout():
  """
  Reporting a simplified structure of of the tile board layout. We will not
  construct the full data. instead just passing the tileboard layout type and the
  calibrated cooridnates.
  """
  ans = {
      'boardtype': session.cmd.board.boardtype,
      'detectors': {
          detid: {
              'orig': session.cmd.board.get_det(detid).orig_coord,
              'lumi': session.cmd.board.get_det(detid).orig_coord,
              'vis': session.cmd.board.get_det(detid).orig_coord
          }
          for detid in session.cmd.board.dets()
      }
  }

  for detid in ans['detectors']:
    det = session.cmd.board.get_det(detid)
    ## Updating the visual coordinates if they exists
    if any(det.vis_coord):
      z = min(det.vis_coord.keys())
      ans['detectors'][detid]['vis'] = det.vis_coord[z]
    else:
      ans['detectors'][detid]['vis'] = [-100, -100]

    ## Updating the lumi calibrated coordinates if they exists
    if any(det.lumi_coord):
      z = min(det.lumi_coord.keys())
      ans['detectors'][detid]['lumi'] = [
          det.lumi_coord[z][0], det.lumi_coord[z][2]
      ]
    else:
      ans['detectors'][detid]['lumi'] = [-100, -100]

  return ans


def report_progress():
  """
  Returning the current progress tracking map for the various processes in a
  calibration session.
  """
  return session.progress_check


def report_useraction():
  """
  Returning the message to be displayed in the waiting for user action part.
  """
  return session.waiting_msg


def report_detid_data(process, detid):
  """
  Returning the cached data to be displayed by the client. There is something
  wrong with parsing the input, this function should still respond with a empty map. The display client will be responsible for handling such inputs.
  """
  __default = {}

  try:
    if process == 'zscan':
      fname = calibration_filename('zscan', detid)
      return report_file_data('zscan', fname)
    elif process == 'lowlight':
      fname = calibration_filename('lowlight', detid)
      return report_file_data('hist', fname)
    elif process == 'lumialign':
      fname = calibration_filename('halign', detid)
      return report_file_data('xyz', fname)
    else:
      return __default
  except:
    return __default


def report_file_data(process, filename):
  """
  Returning the contents of a file in the requested format. This function will be
  used for the generation of the common data format. Additional formatting
  functions will be used to perform that actual file crawling. Here we will be
  using os and psutil to check if there are the current file is being opened by
  the cmd process to see if the update the update flag.
  """
  __default = {}

  ans = {'filename': filename, 'type': process, 'update': False, 'data': None, }

  try:
    with open(filename, 'r') as f:
      p = next(iter([x for x in psutil.process_iter() if x.pid == os.getpid()]))
      u = [x.path for x in p.open_files() if f.name in x.path]
      # In case there are currently more than 1 file object opening the file.
      if len(u) > 1:
        ans['update'] = True
      if process == 'xyz':
        ans['data'] = parse_file_xyz(f)
      elif process == 'hist':
        ans['data'] = parse_file_hist(f)
      elif process == 'zscan':
        ans['data'] = parse_file_zscan(f)
      elif process == 'tscan':
        ans['data'] = parse_file_tscan(f)
      return ans
  except Exception as err:
    print("Error parsing data:", type(err), err)
    ## Returning the empty JSON in case any parsing went wrong
    return __default


"""
File parsing functions. The following parse file function assumes the following
input:
- f is a file object opened in read mode.
- The file object that it is pointed to assumes the format defined in the
  write_standard_line defined in the cmdbase.savefilecmd method, with the
  following standard columns:
  - timestamp
  - detector id
  - gantry x,y,z
  - pulser bias, 2 temperature readouts,
  - length >2 data array.

The function will then parse the file into a simplified format to be plotted
client side. Notice that no or very little data processing will be handled here.
(Do not expect fitting results and such.)
"""


def parse_file_xyz(f):
  """
  The output to be displayed in a x-y-z heat map. because uncertainties in z is
  difficult to display in heat maps, we will be omitting uncertainties in the
  output.
  """
  ans = {'x': [], 'y': [], 'z': []}

  for line in f:
    tokens = line.split()
    if (len(tokens) != 10): continue  # Skipping over line in bad format.
    ans['x'].append(float(tokens[2]))
    ans['y'].append(float(tokens[3]))
    ans['z'].append(float(tokens[8]))

  return ans


def parse_file_hist(f):
  """
  Here we aggregate the results in a histogram. Here we assume the standard
  write-out format with the last N columns being a list of readout values. The
  first line is then used to create an numpy histogram. All other lines will be
  accumulated into this histogram. We choose to create the histogram early to
  reduce the memory footprint of the program.
  """
  ans = {'edges': [], 'values': [], 'mean': 0.0, 'rms': 0.0}

  for line in f:
    tokens = line.split()
    if (len(tokens) < 10): continue  # Skipping over lines with bad format
    array = [float(x) for x in tokens[8:]]
    if ans['edges'] == []:
      ans['values'], ans['edges'] = np.histogram(array, bins=40)
    else:
      v, _ = np.histogram(array, bins=ans['edges'])
      ans['values'] = ans['values'] + v

  cen = 0.5 * (ans['edges'][1:] + ans['edges'][:-1])
  ans['mean'] = np.average(cen, weights=ans['values'])
  ans['rms'] = np.average((cen - ans['mean'])**2, weights=ans['values'])**0.5

  # Converting to python list
  ans['edges'] = ans['edges'].tolist()
  ans['values'] = ans['values'].tolist()

  return ans


def parse_file_zscan(f):
  """
  This assumes an intensity scale using gantry z motion and the varying values in
  the PWM module. The return value will contain 4 columns, the gantry z position,
  the PWM voltage monitor, the readout value and its uncertainty.
  """
  ans = {'z': [], 'p': [], 'v': [], 'vu': []}
  for line in f:
    tokens = line.split()
    if (len(tokens) != 10): continue  # Skipping over lines with bad format
    ans['z'].append(float(tokens[4]))
    ans['p'].append(float(tokens[5]))
    ans['v'].append(float(tokens[8]))
    ans['vu'].append(float(tokens[9]))

  return ans


def parse_file_tscan(f):
  """
  This assumes and intensity scale during for a certain duration of time via the
  timescan command. Notice that the PWM value is intended to vary so it will be
  included in the readout results.
  """
  ans = {'t': [], 'v': [], 'vu': [], 's': [], 'su': []}

  for line in f:
    tokens = line.split()
    if (len(tokens) != 12): continue  # Skipping over lines with bad format
    ans['t'].append(float(tokens[0]))
    ans['v'].append(float(tokens[8]))
    ans['vu'].append(float(tokens[9]))
    ans['s'].append(float(tokens[10]))
    ans['su'].append(float(tokens[11]))

  return ans


def report_settings():
  """
  Returning the list of settings to be parsed by the display client. The reason
  why this function is generated on user request is because the user might need
  to clear the client-side settings. This function allows for this to be
  performed without needing to update all other connect clients.
  """
  settings = {
      'image': {
          'threshold': session.cmd.visual.threshold,
          'blur': session.cmd.visual.blur_range,
          'lumi': session.cmd.visual.lumi_cutoff,
          'size': session.cmd.visual.size_cutoff,
          'ratio': session.cmd.visual.ratio_cutoff * 100,
          'poly': session.cmd.visual.poly_range * 100,
      },
      'zscan': {
          'samples': session.zscan_samples,
          'pwm': session.zscan_power_list,
          'zdense': session.zscan_zlist_dense,
          'zsparse': session.zscan_zlist_sparse,
      },
      'lowlight': {
          'samples': session.lowlight_samples,
          'pwm': session.lowlight_pwm,
          'zval': session.lowlight_zval,
      },
      'lumialign': {
          'samples': session.lowlight_samples,
          'pwm': session.lowlight_pwm,
          'zval': session.lowlight_zval,
          'range': session.lumialign_range,
          'distance': session.lumialign_distance,
      },
      'picoscope': {
          # Picoscope settings are availabe regardless of picoscope availability.
          'channel-a-range': session.cmd.pico.rangeA(),
          'channel-b-range': session.cmd.pico.rangeB(),
          'trigger-channel': session.cmd.pico.triggerchannel,
          'trigger-value': session.cmd.pico.triggerlevel,
          'trigger-direction': session.cmd.pico.triggerdirection,
          'trigger-delay': session.cmd.pico.triggerdelay,
          'trigger-presample': session.cmd.pico.presamples,
          'trigger-postsample': session.cmd.pico.postsamples,
          'blocksize': session.cmd.pico.ncaptures
      }
  }

  # DRS settings are only available if a physical board is attached to the
  # machine.
  if session.cmd.drs.is_available():
    settings.update({
        'drs': {
            'triggerdelay': session.cmd.drs.trigger_delay(),
            'samplerate': session.cmd.drs.rate(),
            'samples': session.cmd.drs.samples(),
        }
    })
  else:
    settings.update(
        {'drs': {
            'triggerdelay': 0,
            'samplerate': 0,
            'samples': 0,
        }})

  return settings


def report_system_boards():
  """
  Returning a list a number of boards that can be used for system calibration.
  """
  return get_boards('cfg/system/*.json')


def report_standard_boards():
  """
  Returning a list of board that can be used for standard calibration processes.
  """
  return get_boards('cfg/standard/*.json')


def get_boards(pattern):
  """
  Getting the boards description given a glob pattern
  """
  filelist = glob.glob(pattern)
  ans = {}
  for f in filelist:
    key = os.path.basename(f)
    key = os.path.splitext(key)[0]
    with open(f, 'r') as readfile:
      b = json.load(readfile)
      ans[key] = {
          'name': b['board name'],
          'description': b['board description'],
          'number': len(b['detectors'])
      }
  return ans


def report_valid_reference():
  """
  Returning a list of valid reference with description. This function will look
  in the calib/ directory and find the files that are within 24 hours of the
  request time, for directories that match such a description, the reference
  session formation is packed up into the return json object.
  """
  calib_fmt = re.compile(r'[a-zA-Z\_]+_\d{8}-\d{4}$')
  filelist = [f for f in os.listdir('calib') if calib_fmt.match(f)]

  time_now = datetime.datetime.now()

  ans = []
  for f in filelist:
    time_then = datetime.datetime.strptime(f[-13:], '%Y%m%d-%H%M')
    time_diff = time_now - time_then
    if (time_diff.days + time_diff.seconds / 3600) > 24: continue
    ans.append({
        'tag': f,
        'boardtype': f[:-15],
        'time': time_then.strftime('%Y/%m/%d/ %H:%M:%S')
    })

  # Transformaing into a minimum json folder, since the object needs to be map to
  # be jsonified.
  return {'valid': sorted(ans, key=lambda x: x['time'])}
