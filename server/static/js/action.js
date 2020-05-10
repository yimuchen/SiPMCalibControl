function emit_action_cmd(id, msg) {
  $('#display-message').html('');
  socketio.emit('run-action-cmd', {
    'id': id,
    'data': msg
  });
}

function action_received(msg) {
  // Disable every button on start up
  $('button').each(function () {
    $(this).prop('disabled', true);
  });
}

function action_complete(msg) {
  console.log('action-complete received!');
  $('button').each(function () {
    $(this).prop('disabled', false);
  });
}

function run_system_calibration() {
  boardtype = $('input[name="system-calib-boardtype"]:checked').val()
  emit_action_cmd('run_system_calibration', {
    'boardtype': boardtype
  });
}

function run_std_calibration() {
  boardid = $('#std-calibration-boardid').val()
  boardtype = $('input[name="std-calibration-boardtype"]:checked').val();
  emit_action_cmd("run-std-calibration", {
    'boardid': boardid,
    'boardtype': boardtype
  });
  console.log('Calibration sequence started activated');
};

function raw_cmd_input() {
  var line = $('#raw-cmd-input-text').val();
  emit_action_cmd("raw-cmd-input", {
    'input': line
  });
}

function image_setting_update(event) {
  emit_action_cmd(event.target.id, {
    'threshold': $('#image-threshold-text').val(),
    'blur': $('#image-blur-text').val(),
    'lumi': $('#image-lumi-text').val(),
    'size': $('#image-size-text').val(),
    'ratio': $('#image-ratio-text').val(),
    'poly': $('#image-poly-text').val()
  });
}

function display_user_action(msg) {
  $('#user-action').removeClass('invisible');
  $('#user-action-msg').html(msg);
  // Re-enable the button used for completing the user action.
  $('#user-action-complete').prop('disabled', false);
}


function complete_user_action() {
  $('#user-action').addClass('invisible');
  socketio.emit('complete-user-action', '');
}