/**
 * Simplified interface for emitting a user action to the socket interface.
 *
 * 'id' is used to classify the action to be carried out by the main session.
 * 'msg' is used for any accompanying data to be used.
 */
function emit_action_cmd(id, msg) {
  $('#display-message').html('');
  socketio.emit('run-action-cmd', {
    'id': id,
    'data': msg
  });
}

/**
 * Process defined to running a system calibration.
 *
 * Check if the inputs are OK. If not then the function will not execute.
 */
function run_system_calibration() {
  console.log(`Starting system calibration`);
  var boardtype = $('input[name="system-calibration-boardtype"]:checked').val()

  if (boardtype == undefined) {
    $('#system-calib-submit-error').html(
      'System calibration board type not selected')
  } else {
    $('#system-calib-submit-error').html('');
    emit_action_cmd('run-system-calibration', {
      'boardtype': boardtype
    });

    hide_action_column();
  }
}

function run_std_calibration() {
  boardid = $('#std-calibration-boardid').val()
  boardtype = $('input[name="standard-calibration-boardtype"]:checked').val();
  reference = $('input[name="ref-calibration"]:checked').val()

  if (boardid === '') {
    $('#standard-calib-submit-error').html(
      'Board ID not specified')
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

    hide_action_column();
  }
};

/**
 * Collecting the additional client-side data required for the calibration
 * sign-off. The comments is set up as a map passed to the main calibration
 * session. The user id and the password of the central processing server is also
 * collected here. This function will not clear anything, and will wait for the
 * system to send the sync signal indicating sign-off completion before wiping
 * the display data.
 */
async function calibration_signoff(session_type) {
  var comment_map = {};

  $(`#${session_type}-calib-signoff-container`)
    .children('.signoff-comment-lines')
    .find('.comment-header').each(function (index) {
      var det_id = $(this).val();
      var comment = $(this).parent().siblings('.comment-content')
        .children('.comment-text').val();
      if (!(det_id in comment_map)) {
        comment_map[det_id] = comment;
      } else {
        comment_map[det_id] += '\n' + comment;
      }
    });

  emit_action_cmd(`${session_type}-calibration-signoff`, {
    'comments': comment_map,
    'user': $(`#${session_type}-calib-user-id`).val(),
    'pwd': $(`#${session_type}-calib-user-pwd`).val()
  });

  await sleep(1000)
  update_valid_reference();
}

function system_calibration_signoff() { calibration_signoff('system'); }
function standard_calibration_signoff() { calibration_signoff('standard'); }

/**
 * Rerunning a calibration process for a single detector, either to extend the
 * amount of data collected or to perform a clean rerun.
 *
 * If the calibration process is tied to a plot, and a hard re-run is requested,
 * then the old plot is first cleared from the existing HTML element.
 */
function rerun_single(action_tag, detid, extend) {
  emit_action_cmd('rerun-single', {
    'action': action_tag,
    'detid': detid,
    'extend': extend,
  });
  const plot_processes = ['zscan', 'lowlight', 'lumialign'];

  // Adding the plotting section if the plotting section didn't already exists
  if (plot_processes.indexOf(action_tag) > 0) {
    console.log(action_tag);
    console.log($(`#single-det-summary-plot-${detid}-${action_tag}`).length);

    if (($(`#single-det-summary-plot-${detid}-${action_tag}`).length == 0)) {
      // Generating a new plot div for data display
      $(`#det-plot-container-${detid}`).children(".plot-container").append(
        `<div class="plot" id="single-det-summary-plot-${detid}-${action_tag}">
       </div>`
      )
    } else {
      if (!extend) {
        Plotly.purge(`single-det-summary-plot-${detid}-${action_tag}`);
        $(`#single-det-summary-plot-${detid}-${action_tag}`).html('');
      }
    }
  }

  request_plot_by_detid(detit, action_tag)
}

/**
 * Asking the session to execute the drs debugging sequence
 */
async function debug_request_plot() {
  file = $('#debug-plot-file').val()
  type = $('input[name="debug-plot-type"]:checked').val();
  console.log(file, type)
  request_plot_by_file(file, type, 'debug-plot-div')
}

/**
 * On completion of the user action part. Hide the tab showing the required user
 * action. Send signal to main calibration session.
 */
function complete_user_action() {
  hide_action_column();
  $('#user-action').addClass('hidden');
  socketio.emit('complete-user-action', '');
}
