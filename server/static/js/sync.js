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
const STATE_EXEC_CMD = 2;
const STATE_WAIT_USER = 3;

// additional mapping for session types.
var session_type = 0;
const SESSION_TYPE_NONE = 0;
const SESSION_TYPE_SYSTEM = 1;
const SESSION_TYPE_STANDARD = 2;

// progress
var session_board_type = "";

/**
 * Basic function to allow for async functions to sleep for a certain duration.
 * Main reference:
 * https://www.sitepoint.com/delay-sleep-pause-wait/
 */
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function request_sync(msg) {
  socketio.emit("resend", msg);
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
  session_state = new_state; // updating the raw system state.

  // Action button locking if state is not idle
  const lock = session_state != STATE_IDLE;
  $(".action-button").each(function () {
    $(this).prop("disabled", lock);
  });

  // Editing the user action HTML DOM elements
  if (session_state === STATE_WAIT_USER) {
    show_action_column();
    $("#user-action").removeClass("hidden");
    $("#user-action-complete").prop("disabled", false);
    $.ajax({
      dataType: "json",
      mimeType: "application/json",
      url: `report/useraction`,
      success: function (json) {
        $("#user-action-msg").html(json);
      },
      error: function () {
        console.log("Failed to get user action message");
        iterate_status_update();
      },
    });
  } else {
    $("#user-action").addClass("hidden");
  }
}

/**
 * When the calibration session type is updated by the main calibration session.
 */
function sync_session_type(new_type) {
  session_type = new_type;

  function clear_comment_fields(id_string) {
    $(id_string).children(".signoff-comment-lines").html(``);
  }

  if (session_type == SESSION_TYPE_NONE) {
    clear_display();
    $("#system-calib-signoff-container").addClass("hidden");
    $("#standard-calib-signoff-container").addClass("hidden");
    clear_comment_fields("#system-calib-signoff-container");
    clear_comment_fields("#standard-calib-signoff-container");
  } else if (session_type == SESSION_TYPE_STANDARD) {
    $("#standard-calib-signoff-container").removeClass("hidden");
    clear_comment_fields("#system-calib-signoff-container");
    clear_comment_fields("#standard-calib-signoff-container");
  } else if (session_type == SESSION_TYPE_SYSTEM) {
    $("#system-calib-signoff-container").removeClass("hidden");
    clear_comment_fields("#system-calib-signoff-container");
    clear_comment_fields("#standard-calib-signoff-container");
  }
}

/**
 * Handling of the signal from the settings. This function call the update
 * settings function from the settings.js file.
 */
function sync_setting(new_settings) {
  update_settings(new_settings);
}

/**
 * Updating the overall progress bar.
 *
 * There are two bars in the calculation part. One is for the overall progress.
 * One is for the current running command progress.
 */
function sync_cmd_progress(msg) {
  let complete = msg[0];
  let total = msg[1];
  const percent = (100.0 * complete) / total;
  $("#command-progress")
    .children(".progress-complete")
    .css("width", `${percent}%`);
}

/**
 * Here we only setup the various used for keeping track of the tileboard view.
 * In case the tileboard type is non-trivial, we setup call the additional
 * functions setup in the tileboard_view.js file to generate the additional
 * display elements.
 */
function sync_tileboard_type(msg) {
  session_board_type = msg;
  // In the case board type is non-trivial setup the document to properly display
  // the a tileboard view elements. These functions are defined in the
  // tileboard_view.js file.
  if (session_board_type != "") {
    make_tileboard_detector_html();
  } else {
    clear_tileboard_detector_html();
  }

  request_sync('state');
  request_sync('progress');
}

/**
 * As updating the progress is a little more involved with the display elements,
 * required function have been split into the view_tileboard method for better
 * readability. As updating the the progress bars are potentially very taxing on
 * the client side while being rapidly updated on the server side, here we write
 * a very small safe guard. To ensure that the progress updates are performed in
 * sequence of their arrival time.
 */
var progress_queue = [];
var updating_progress = false;

async function sync_calib_progress(progress) {
  progress_queue.push(progress); // Pushing the progress to the stack.
  run_progress_update();
}

function run_progress_update() {
  // early exit if and instance of the update function is already running.
  if (updating_progress) {
    return;
  }

  updating_progress = true;
  while (progress_queue.length) {
    progress = progress_queue[0];
    progress_queue.shift();

    // Functions defined in view_progress.js
    progress_update_bar(progress);
    progress_update_table(progress);
    progress_update_det_summary(progress);
  }
  updating_progress = false;
}
