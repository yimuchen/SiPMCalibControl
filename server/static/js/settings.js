/**
 * settings.js
 *
 * All stuff related to the settings, including the syncing from server-side to
 * client-side and the submission of client-side to server side.
 */

/**
 * Clear client side settings. Request a new set of setting from server side and
 * update accordingly.
 */
async function clear_settings() {
  $.ajax({
    dataType: 'json',
    mimeType: 'application/json',
    url: `report/settings`,
    success: update_settings,
    error: async function () {
      console.log('Failed to sync with system settings');
      await sleep(500);
      clear_settings(); // Trying indefinitely.
    },
  });
}

/**
 * Given a new settings in json format. Update all DOM elements according to the
 * new settings.
 */
function update_settings(json) {
  // Image settings.
  $('#image-threshold-text').val(json.image.threshold);
  $('#image-blur-text').val(json.image.blur);
  $('#image-lumi-text').val(json.image.lumi);
  $('#image-size-text').val(json.image.size);
  $('#image-ratio-text').val(json.image.ratio);
  $('#image-poly-text').val(json.image.poly);

  sync_range_to_text_by_id(`image-threshold-text`);
  sync_range_to_text_by_id(`image-blur-text`);
  sync_range_to_text_by_id(`image-lumi-text`);
  sync_range_to_text_by_id(`image-size-text`);
  sync_range_to_text_by_id(`image-ratio-text`);
  sync_range_to_text_by_id(`image-poly-text`);

  // Z-scan settings
  $('#zscan-settings-samples').val(json.zscan.samples);
  $('#zscan-settings-pwm').val(json.zscan.pwm.join(' '));
  $('#zscan-settings-zval-dense').val(json.zscan.zdense.join(' '));
  $('#zscan-settings-zval-sparse').val(json.zscan.zsparse.join(' '));

  // Low-light settings
  $('#lowlight-settings-samples').val(json.lowlight.samples);
  $('#lowlight-settings-pwm').val(json.lowlight.pwm);
  $('#lowlight-settings-zval').val(json.lowlight.zval);

  // luminosity alignment settings
  $('#lumialign-settings-samples').val(json.lumialign.samples);
  $('#lumialign-settings-pwm').val(json.lumialign.pwm);
  $('#lumialign-settings-zval').val(json.lumialign.zval);
  $('#lumialign-settings-range').val(json.lumialign.range);
  $('#lumialign-settings-distance').val(json.lumialign.distance);

  // DRS settings
  $('#drs-triggerdelay').val(json.drs['triggerdelay']);
  $('#drs-samplerate').val(json.drs['samplerate']);
  $('#drs-samples').val(json.drs['samples']);

  // Picoscope settings.
  $('#channel-a-range').val(json.picoscope['channel-a-range']);
  $('#channel-b-range').val(json.picoscope['channel-b-range']);
  $('#trigger-delay').val(json.picoscope['trigger-delay']);
  $('#trigger-presample').val(json.picoscope['trigger-presample']);
  $('#trigger-postsample').val(json.picoscope['trigger-postsample']);
  $('#trigger-blocksize').val(json.picoscope['blocksize']);

  $('#trigger-level-text').val(adc_from_value(json.picoscope['trigger-value']));
  $('#trigger-level-range').val(
    adc_from_value(json.picoscope['trigger-value']),
  );
  $(
    `input[name="trigger-channel"][value="${json.picoscope['trigger-channel']}"]`,
  ).prop('checked', true);
  $(
    `input[name="trigger-direction"][value="${json.picoscope['trigger-direction']}"]`,
  ).prop('checked', true);
  sync_pico_range();
  sync_pico_trigger();
}

/**
 * Helper function to parse a strings separated by white spaces to an array of
 * floats
 */
function split_string_to_float_array(input_string) {
  let str_array = input_string.split(/(\s+)/).filter((e) => e.length > 1);
  var ans = [];
  for (const str of str_array) {
    const token = parseFloat(str);
    if (!token.isNaN()) {
      ans.append(token);
    }
  }
  return ans;
}

/**
 * Action emitting function for submitting the changes on the image processing
 * changes from the client to the main session manager.
 */
function image_settings_update() {
  const new_settings = {
    threshold: $('#image-threshold-text').val(),
    blur: $('#image-blur-text').val(),
    lumi: $('#image-lumi-text').val(),
    size: $('#image-size-text').val(),
    ratio: $('#image-ratio-text').val(),
    poly: $('#image-poly-text').val(),
  };

  emit_action_cmd('image-settings', new_settings);
}

/**
 * Action emitting function for submitting the changes on the zscan setting to
 * the main session manager.
 */
function zscan_settings_update() {
  const new_settings = {
    samples: $('#zscan-settings-samples').val(),
    pwm: split_string_to_float_array($('#zscan-settings-pwm').val()),
    zlist_dense: split_string_to_float_array(
      $('#zscan-settings-zval-dense').val(),
    ),
    zlist_sparse: split_string_to_float_array(
      $('#zscan-settings-zval-sparse').val(),
    ),
  };

  emit_action_cmd('zscan-settings', new_settings);
}

/**
 * Action emitting function for submitting the changes on the lowlight scan
 * settings to the main session manager.
 */
function lowlight_settings_update() {
  const new_settings = {
    samples: $('#lowlight-settings-samples').val(),
    pwm: $('#lowlight-settings-pwm').val(),
    zval: $('#lowlight-settings-zval').val(),
  };

  emit_action_cmd('lowlight-settings', new_settings);
}

/**
 * Action emitting function for submitting the changes on the lumi-alignment
 * calibration settings to the main session manager.
 */
function lumialign_settings_update() {
  const new_settings = {
    samples: $('#lumialign-settings-samples').val(),
    pwm: $('#lumialign-settings-pwm').val(),
    zval: $('#lumialign-settings-zval').val(),
    range: $('#lumialign-settings-range').val(),
    distance: $('#lumialign-settings-distance').val(),
  };

  emit_action_cmd('lumialign-settings', new_settings);
}

/**
 * Action emitting function for submitting the changes on the picoscope readout
 * settings to the main session manager.
 */
function picoscope_settings_update() {
  const trigger_level = value_from_adc(
    $('#trigger-level-text').val(),
    $('input[name="trigger-channel"]:checked').val(),
  );

  const new_settings = {
    'channel-a-range': $('#channel-a-range').val(),
    'channel-b-range': $('#channel-b-range').val(),
    'trigger-channel': $('input[name="trigger-channel"]:checked').val(),
    'trigger-level': trigger_level,
    'trigger-direction': $('input[name="trigger-direction"]:checked').val(),
    'trigger-delay': $('#trigger-delay').val(),
    presample: $('#trigger-presample').val(),
    postsample: $('#trigger-postsample').val(),
    blocksize: $('#trigger-blocksize').val(),
  };

  emit_action_cmd('picoscope-settings', new_settings);
}

/**
 * Action emitting function for submitting changes to the drs readout settings to
 * the main session manager.
 */
function drs_settings_update() {
  const new_settings = {
    'drs-triggerdelay': $('#drs-triggerdelay').val(),
    'drs-samplerate': $('#drs-samplerate').val(),
    'drs-samples': $('#drs-samples').val(),
  };

  emit_action_cmd('drs-settings', new_settings);
}

/**
 * Action emitting function for submitting a calibration call to the DRS manager.
 */
var SEND_CALIB_SIGNAL = 0;
function drs_settings_calib() {
  console.log('Sending the DRS calibration signal', session_state);
  emit_action_cmd('drs-calib', {});
  SENT_CALIB_SIGNAL = 1;
}

/**
 * Additional function used to handle additional processes to run when the
 * calibration is done. Since the calibration changes some of the settings. we
 * are going to rerun the drs_settings_update command if this machine is the one
 * that requested the calibration process to be ran.
 */
function drs_calib_complete() {
  if (SENT_CALIB_SIGNAL == 1) {
    drs_settings_update();
    SENT_CALIB_SIGNAL = 0;
  }
}

/** ========================================================================== */
/** PICOSCOPE SETTING FUNCTIONS */
/** Below are function specific to the step of the picoscope readout system.
 *   Since these function are only used by the picoscope function and nowhere
 *   else. Though these function uses css manipulation, it was decided to put the
 *   following function in the settings.js file.
 */
/** ========================================================================== */

/**
 * Converting the range index to the corresponding mV value.
 */
function range_to_mv(range) {
  switch (range) {
    case '3':
      return 100;
    case '4':
      return 200;
    case '5':
      return 500;
    case '6':
      return 1000;
    case '7':
      return 2000;
    case '8':
      return 5000;
    case '9':
      return 10000;
    case '10':
      return 20000;
    default:
      return 0;
  }
}

/**
 * Given the raw ADC value and a given channel, convert to the corresponding mV
 * value. Not used for readout, only for client side trigger level conversion.
 */
function value_from_adc(adc, channel) {
  const range_idx =
    parseInt(channel) == 0
      ? $('#channel-a-range').val()
      : parseInt(channel) == 1
      ? $('#channel-b-range').val()
      : '10';
  return (adc * range_to_mv(range_idx)) / 32768;
}

/**
 * Given some mV value for a given channel, translate to a raw ADC value (round
 * down). Not used for readout, only for client side trigger level conversion.
 */
function adc_from_value(value, channel) {
  const range_idx =
    parseInt(channel) == 0
      ? $('#channel-a-range').val()
      : parseInt(channel) == 1
      ? $('#channel-b-range').val()
      : '10';
  return parseInt((value * 32768) / range_to_mv(range_idx));
}

/**
 * Showing the (non-input) text of the range for each channel. According to the
 * slider settings.
 */
function sync_pico_range() {
  const id_list = ['channel-a-range', 'channel-b-range'];

  for (const id of id_list) {
    const range_mv = range_to_mv($(`#${id}`).val());
    $(`#${id}-value`).html(
      range_mv < 1000
        ? `${parseInt(range_mv)} mV`
        : `${parseInt(range_mv / 1000)} V`,
    );
  }
}

function sync_pico_trigger() {
  var adc = $('#trigger-level-text').val();
  var channel = $("input[name='trigger-channel']:checked").val();
  var level = value_from_adc(parseInt(adc), channel);
  var unit = 'mV';
  if (level > 1000) {
    unit = 'V';
    level /= 1000;
  } else if (level < -1000) {
    unit = 'V';
    level /= 1000;
  }

  $('#trigger-level-converted').html('(' + level.toFixed(1) + unit + ')');
}
