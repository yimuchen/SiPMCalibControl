/**
 * List of functions to execute when a button is clicked on the GUI.
 */
var action_socket = null;


/**
 * Effectively the main function
 */
$(document).ready(function () {
  /**
   * On document ready, disable every button on the GUI until released by the
   * main server, also, for every button pressed, disable all buttons until the
   * board type is released. Release signal will be handled by server side.
   */

  console.log('Document ready!');
  $('button').each(function () {
    $(this).prop('disabled', true);
    $(this).on('click', function () {
      $('button').each(function () {
        $(this).prop('disabled', true);
      });
    });
  });


  console.log('Trying to connect to action socket');
  action_socket
    = io.connect('http://' + window.location.hostname + ':9100/action');


  action_socket.on('connect', function () {
    console.log('action socket connected!');
    console.log('action socket connected!');
  });

  action_socket.on('action-received', function (msg) {
    // Disable every button on start up
    $('button').each(function () {
      $(this).prop('disabled', true);
    });
  });

  action_socket.on('action-complete', function () {
    console.log('action-complete received!');
    $('button').each(function () {
      $(this).prop('disabled', false);
    });
  });



  // Standard calibration actions!
  $('#std-calibration').on('click', function () {
    boardid = $('#std-calibration-boardid').val()
    boardtype = $('input[name="std-calibration-boardtype"]:checked').val();
    emit_action_cmd($(this).prop('id'), {
      'boardid': boardid,
      'boardtype': boardtype
    });
    console.log('Calibration sequence started activated');
  })

  // Standard calibration actions
  $('#raw-cmd-input').on('click', function () {
    var line = $(this).siblings('#raw-cmd-input-text').val();
    emit_action_cmd($(this).prop('id'), {
      'input': line
    });
  })

  // Image settings actions.
  $('#image-setting-clear').on('click', function () {
    emit_action_cmd($(this).prop('id'), {});
  });
  $('#image-setting-update').on('click', image_setting_update);

  // User action related functions
  action_socket.on('useraction', display_user_action);

  // User action complete actions
  $('#user-action-complete').on('click', complete_user_action);
});




function emit_action_cmd(id, msg) {
  action_socket.emit('run-action-cmd', {
    'id': id,
    'data': msg
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

function display_user_action(msg){
  $('#user-action').removeClass('invisible');
  $('#user-action-msg').html(msg);
  // Re-enable the button used for completing the user action.
  $('#user-action-complete').prop('disabled', false );
}


function complete_user_action() {
  $('#user-action').addClass('invisible');
  action_socket.emit('complete-user-action', '');

}