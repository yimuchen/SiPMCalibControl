/**
 * sync.js
 *
 * Javascript function for handling the sync signals sent out by the main
 * calibration session.
 */

function request_sync(msg) {
  socketio.emit('resend', msg);
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
  session.state = new_state; // updating the raw system state.

  // Action button locking if state is not idle
  const lock = session.state != STATE_IDLE;
  $('.action-button').each(function () {
    $(this).prop('disabled', lock);
  });

  // Editing the user action HTML DOM elements
  if (session.state === STATE_WAIT_USER) {
    show_action_column();
    $('#user-action').removeClass('hidden');
    $('#user-action-complete').prop('disabled', false);
    request_user_action();
  } else {
    $('#user-action').addClass('hidden');
  }
}

/**
 * Global variables for status monitoring.
 *
 * The structure of this object should mirror the return value of the python
 * script. Except with potential time dependent storage.
 */

function clear_display(msg) {
  $('#display-message').html('');
  $('#tile-layout-grid').html('');
  $('#single-det-summary').html('');
  $('#det-details-content').html('');
  $('#det-plot-and-figure').html('');
}

function display_message(msg) {
  $('#display-message').html(msg);
}

/**
 * When the calibration session type is updated by the main calibration session.
 */
function sync_session_type(new_type) {
  session.session_type = new_type;

  function clear_comment_fields(id_string) {
    $(id_string).children('.signoff-comment-lines').html(``);
  }

  if (session.session_type == SESSION_TYPE_NONE) {
    clear_display();
    $('#system-calib-signoff-container').addClass('hidden');
    $('#standard-calib-signoff-container').addClass('hidden');
    clear_comment_fields('#system-calib-signoff-container');
    clear_comment_fields('#standard-calib-signoff-container');
  } else if (session.session_type == SESSION_TYPE_STANDARD) {
    $('#standard-calib-signoff-container').removeClass('hidden');
    clear_comment_fields('#system-calib-signoff-container');
    clear_comment_fields('#standard-calib-signoff-container');
  } else if (session.session_type == SESSION_TYPE_SYSTEM) {
    $('#system-calib-signoff-container').removeClass('hidden');
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
  $('#command-progress')
    .children('.progress-complete')
    .css('width', `${percent}%`);
}

/**
 * Here we only setup the various used for keeping track of the tileboard view.
 * In case the tileboard type is non-trivial, we setup call the additional
 * functions setup in the tileboard_view.js file to generate the additional
 * display elements.
 */
function sync_tileboard_type(msg) {
  session.board_type = msg;
  // In the case board type is non-trivial setup the document to properly display
  // the a tileboard view elements. These functions are defined in the
  // tileboard_view.js file.
  if (session.board_type != '') {
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

/**
 * Additional parsing required for passing data. This is required as certain
 * key-strokes requires additional translation into a python friendly format.
 * (Notice that the python backend will not attempt to emulate the entire command
 * line session, keys like tab, history crawling will not be available)
 */
function parse_terminal_keystroke(key) {
  const TERMINAL_PARSE_DEBUG = false; // Flag for debugging if needed.

  // Early exit if terminal is locked
  if (session.terminal_lock) {
    return;
  }

  // Generating the helper string to the console to help debug console inputs
  if (TERMINAL_PARSE_DEBUG) {
    str = '';
    for (i = 0; i < key.length; ++i) {
      str += ' ' + key.charCodeAt(i).toString();
    }
    console.log('combination:', str);
  }

  const code = key.charCodeAt(0); // parsing on first character
  switch (code) {
    case 127: // backspace doesn't trigger backspace character
      socketio.emit('xterminput', { input: '\b' });
      break;
    default:
      socketio.emit('xterminput', { input: key });
      break;
  }
}

/**
 * Displaying the output received from server side
 */
function parse_terminal_response(data) {
  // Parsing output is relatively simple
  term.write(data.output);
}

/**
 * Terminal locking toggle
 */
function check_terminal_lock() {
  if (terminal_lock) {
    // unlocking the terminal
    terminal_lock = false;
    $('#terminal_status').html('TERMINAL IS UNLOCKED');
    $('#terminal_lock').html('LOCK');
    // Getting the prompt in case it wasn't generated.
    parse_keystroke(String.fromCharCode(1));
  } else {
    terminal_lock = true; // locking the terminal
    $('#terminal_status').html('TERMINAL IS LOCKED');
    $('#terminal_lock').html('UNLOCK');
  }
}
