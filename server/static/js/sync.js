/**
 * sync.js
 *
 * Javascript function for handling the sync signals sent out by the main
 * calibration session.
 */

// One main sync target is the current session state.
var session_state = 1; // assumes that something is running by default
// identical mapping for session states.
const STATE_IDLE = 0;
const STATE_RUN_PROCESS = 1;
const STATE_WAIT_USER = 2;

var session_type = 0;
const SESSION_TYPE_NONE = 0;
const SESSION_TYPE_SYSTEM = 1;
const SESSION_TYPE_STANDARD = 2;

/**
 * Basic function to allow for async functions to sleep for a certain duration.
 * Main reference:
 * https://www.sitepoint.com/delay-sleep-pause-wait/
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Updating the session state as seen by the client. In addition to the raw
 * variable used to store the session state, the following are also update:
 * 1. If the new state indicates the system is idle, unlock all action button,
 *    otherwise lock all action buttons.
 * 2. If the new state is "waiting for user", unlock a action button associated
 *    with the user action button and display the wait message as given by
 *    submitting an ajax request.
 */
function sync_system_state(new_state) {
  console.log(`Syncing system state`, new_state);
  session_state = new_state; // updating the raw system state.

  // Action button locking if state is not idle
  const lock = session_state != STATE_IDLE;
  $('.action-button').each(function () {
    $(this).prop('disabled', lock);
  });

  // Editing the user action HTML DOM elements
  if (session_state === STATE_WAIT_USER) {
    show_action_column();
    $('#user-action').removeClass('hidden');
    $('#user-action-complete').prop('disabled', false);
    $.ajax({
      dataType: 'json',
      mimeType: 'application/json',
      url: `report/useraction`,
      success: function (json) {
        $('#user-action-msg').html(json);
      },
      error: function () {
        console.log('Failed to get user action message');
        if (status_update_flag == true) {
          setTimeout(status_update_start, status_update_interval);
        }
      }
    });
  } else {
    $('#user-action').addClass('hidden');
  }
}

/**
 * When the calibration session type is updated by the main calibration session.
 */
function sync_session_type(new_type) {
  console.log(`Syncing system type`, new_type);
  session_type = new_type;

  function clear_comment_fields(id_string){
    $(id_string).children('.signoff-comment-lines').html(``);
  }

  if (session_type == SESSION_TYPE_NONE) {
    clear_display();
    $('#system-calib-signoff-container').addClass("hidden");
    $('#standard-calib-signoff-container').addClass("hidden");
    clear_comment_fields('#system-calib-signoff-container');
    clear_comment_fields('#standard-calib-signoff-container');
  } else if( session_type == SESSION_TYPE_STANDARD ){
    $('#standard-calib-signoff-container').removeClass("hidden");
    clear_comment_fields('#system-calib-signoff-container');
    clear_comment_fields('#standard-calib-signoff-container');
  } else if (session_type == SESSION_TYPE_SYSTEM ){
    $('#system-calib-signoff-container').removeClass("hidden");
    clear_comment_fields('#system-calib-signoff-container');
    clear_comment_fields('#standard-calib-signoff-container');
  }
}


/**
 * Handling of the signal from the settings. This function call the update
 * settings function from the settings.js file.
 */
function sync_setting(new_settings) {
  update_settings(new_settings);
}