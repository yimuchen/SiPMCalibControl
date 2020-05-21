function emit_action_cmd(id, msg) {
  $('#display-message').html('');
  socketio.emit('run-action-cmd', {
    'id': id,
    'data': msg
  });
}

function action_received(msg) {
  // Disable every action button on start up
  $('.action-button').each(function () {
    $(this).prop('disabled', true);
  });
}

function action_complete(msg) {
  console.log('action-complete received!');
  $('.action-button').each(function () {
    $(this).prop('disabled', false);
  });

  // Requesting an update to all the valid reference board in the system
  // This can only be trigger when an action has been completed after all
  socketio.emit('get-report', 'valid-reference');

}

function run_system_calibration() {
  var boardtype = $('input[name="system-calib-boardtype"]:checked').val()

  if (boardtype == undefined) {
    $('system-calib-submit-error').html(
      'System calibration board type not selected')
  } else {
    $('system-calib-submit-error').html('');
    emit_action_cmd('run-system-calibration', {
      'boardtype': boardtype
    });

    // Remove the submission error stuff
    // Waiting 0.5 seconds to see if sign-off should be generated
    setTimeout(function () {
      socketio.emit('get-report', 'sign-off');
    }, 500)
  }
}

function system_calibration_signoff() {
  var comment_lines_element = $('#system-calib-signoff-container').children(
    '.signoff-comment-lines');

  var comment_map = {};

  comment_lines_element.find('.comment-header').each(function (index) {
    var det_id = $(this).val();
    var comment = $(this).parent().siblings('.comment-content')
      .children('.comment-text').val();
    if (!(det_id in comment_map)) {
      comment_map[det_id] = comment;
    } else {
      comment_map[det_id] += '\n' + comment;
    }
  });

  emit_action_cmd('system-calibration-signoff', {
    'comments': comment_map
  });

  clear_display();
}

function standard_calibration_signoff() {
  var comment_lines_element = $('#standard-calib-signoff-container').children(
    '.signoff-comment-lines');

  var comment_map = {};

  comment_lines_element.find('.comment-header').each(function (index) {
    var det_id = $(this).val();
    var comment = $(this).parent().siblings('.comment-content')
      .children('.comment-text').val();
    if (!(det_id in comment_map)) {
      comment_map[det_id] = comment;
    } else {
      comment_map[det_id] += '\n' + comment;
    }
  });

  emit_action_cmd('standard-calibration-signoff', {
    'comments': comment_map
  });

  clear_display();
}


function run_std_calibration() {
  boardid = $('#std-calibration-boardid').val()
  boardtype = $('input[name="std-calibration-boardtype"]:checked').val();
  reference = $('input[name="ref-calibration"]:checked').val()

  if (boardid === '') {
    $('#standard-calib-submit-error').html(
      'Board calibration not placed')
  } else if (boardtype == undefined) {
    $('#standard-calib-submit-error').html(
      'Board type for standard calibration is not selected');
  } else if (reference == undefined) {
    $('#standard-calib-submit-error').html(
      'Reference calibration session is not selected');
  } else {
    $('#standard-calib-submit-error').html('');
    emit_action_cmd('run-std-calibration', {
      'boardid': boardid,
      'boardtype': boardtype,
      'reference': reference
    });


    // Waiting 0.5 seconds to see if sign-off should be generated
    setTimeout(function () {
      socketio.emit('get-report', 'sign-off');
    }, 500)
  }

};


function rerun_single(action_tag, detid) {
  emit_action_cmd('rerun-single', {
    'action': action_tag,
    'detid': detid
  });
  const plot_processes = ['zscan', 'lowlight', 'lumialign'];

  // Adding the plotting section if the plotting section didn't already exists

  if ( plot_processes.indexOf(action_tag) > 0 ) {
    console.log(action_tag);
    console.log($(`#single-det-summary-plot-${detid}-${action_tag}`).length);

    if(($(`#single-det-summary-plot-${detid}-${action_tag}`).length == 0)) {
      $(`#det-plot-container-${detid}`).children(".plot-container").append(
        `<div class="plot" id="single-det-summary-plot-${detid}-${action_tag}">
       </div>`
      )
    }
  }
}

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