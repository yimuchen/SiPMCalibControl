function image_settings_update() {
  const new_settings = {
    'threshold': $('#image-threshold-text').val(),
    'blur': $('#image-blur-text').val(),
    'lumi': $('#image-lumi-text').val(),
    'size': $('#image-size-text').val(),
    'ratio': $('#image-ratio-text').val(),
    'poly': $('#image-poly-text').val(),
  }

  emit_action_cmd('image-settings', new_settings);
}

function image_settings_clear() {
  socketio.emit('get-report', 'image-settings');
}

function sync_image_settings(msg) {
  $('#image-threshold-text').val(msg.threshold);
  sync_range_to_text_by_id(`image-threshold-text`);

  $('#image-blur-text').val(msg.blur);
  sync_range_to_text_by_id(`image-blur-text`);

  $('#image-lumi-text').val(msg.lumi);
  sync_range_to_text_by_id(`image-lumi-text`);

  $('#image-size-text').val(msg.size);
  sync_range_to_text_by_id(`image-size-text`);

  $('#image-ratio-text').val(msg.ratio);
  sync_range_to_text_by_id(`image-ratio-text`);

  $('#image-poly-text').val(msg.poly);
  sync_range_to_text_by_id(`image-poly-text`);
}


function split_string_to_float_array(input_string) {
  input_string = input_string.split(' ');
  var ans = []
  for (var index = 0; index < input_string.length; ++index) {
    var token = parseFloat(input_string[index]);
    if (!token.isNaN()) {
      ans.append(token)
    }
  }
  return ans;
}


function zscan_settings_update() {
  const new_settings = {
    'samples': $('#zscan-settings-samples').val(),
    'pwm': split_string_to_float_array($('#zscan-settings-pwm').val()),
    'zlist_dense':
      split_string_to_float_array('#zscan-settings-zval-dense').val(),
    'zlist_sparse':
      split_string_to_float_array('#zscan-settings-zval-sparse').val(),
  }

  emit_action_cmd('zscan-settings', new_settings);
}

function zscan_settings_clear() {
  socketio.emit('get-report', 'zscan-settings');
}

function sync_zscan_settings(msg) {
  $('#zscan-settings-samples').val(msg['samples']);
  $('#zscan-settings-pwm').val(msg['pwm'].join(' '));
  $('#zscan-settings-zval-dense').val(msg['zlist-dense'].join(' '));
  $('#zscan-settings-zval-sparse').val(msg['zlist-sparse'].join(' '));
}

function lowlight_settings_update() {
  const new_settings = {
    'samples': $('#lowlight-settings-samples').val(),
    'pwm': $('#lowlight-settings-pwm').val(),
    'zval': $('#lowlight-settings-zval').val(),
  }

  emit_action_cmd('lowlight-settings', new_settings);
}

function lowlight_settings_clear() {
  socketio.emit('get-report', 'lowlight-settings');
}

function sync_lowlight_settings(msg) {
  $('#lowlight-settings-samples').val(msg['samples']);
  $('#lowlight-settings-pwm').val(msg['pwm']);
  $('#lowlight-settings-zval').val(msg['zval']);
}


function lumialign_settings_update() {
  const new_settings = {
    'samples': $('#lumialign-settings-samples').val(),
    'pwm': $('#lumialign-settings-pwm').val(),
    'zval': $('#lumialign-settings-zval').val(),
    'range': $('#lumialign-settings-range').val(),
    'distance': $('#lumialign-settings-distance').val(),
  }

  emit_action_cmd('lumialign-settings', new_settings);
}

function lumialign_settings_clear() {
  socketio.emit('get-report', 'lumialign-settings');
}

function sync_lumialign_settings(msg) {
  $('#lumialign-settings-samples').val(msg['samples']);
  $('#lumialign-settings-pwm').val(msg['pwm']);
  $('#lumialign-settings-zval').val(msg['zval']);
  $('#lumialign-settings-range').val(msg['range']);
  $('#lumialign-settings-distance').val(msg['distance']);
}


function picoscope_settings_update() {
  const trigger_level = value_from_adc($('#trigger-level-text').val()
    , $('input[name="trigger-channel"]:checked').val());

  const new_settings = {
    'channel-a-range': $('#channel-a-range').val(),
    'channel-b-range': $('#channel-b-range').val(),
    'trigger-channel': $('input[name="trigger-channel"]:checked').val(),
    'trigger-level': trigger_level,
    'trigger-direction': $('input[name="trigger-direction"]:checked').val(),
    'trigger-delay': $('#trigger-delay').val(),
    'presample': $('#trigger-presample').val(),
    'postsample': $('#trigger-postsample').val(),
    'blocksize': $('#trigger-blocksize').val()
  }

  emit_action_cmd('picoscope-settings', new_settings);
}

function picoscope_settings_clear() {
  socketio.emit('get-report', 'picoscope-settings');
}

function sync_picoscope_settings(msg) {
  $('#channel-a-range').val(msg['channel-a-range']);
  $('#channel-b-range').val(msg['channel-b-range']);

  $(`input[name="trigger-channel"][value="${msg['trigger-channel']}"]`).prop("checked", true);
  $('#trigger-level-text').val(adc_from_value(msg['trigger-value']));
  $('#trigger-level-range').val(adc_from_value(msg['trigger-value']));
  $(`input[name="trigger-direction"][value="${msg['trigger-direction']}"]`).prop('checked', true);

  $('#trigger-delay').val(msg['trigger-delay']);

  console.log(msg);
  $('#trigger-presample').val(msg['trigger-presample']);
  $('#trigger-postsample').val(msg['trigger-postsample']);
  $('#trigger-blocksize').val(msg['blocksize']);

  sync_pico_range();
  sync_pico_trigger();
}

