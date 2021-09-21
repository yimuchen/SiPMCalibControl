/**
 * main.js
 *
 * Defining the socket, how the socket should initializing the document on load,
 * and various interface initializing processes.
 */

$(document).ready(function () {
  // Disable all buttons by default. Buttons will be released by action-complete
  // signal from the server.
  $('button.action-button').each(function () {
    $(this).prop('disabled', true);
  });

  // Drawing the common elements of the tileboard layout.
  draw_tileboard_view_common();

  // Connect to the network socket
  socketio = io.connect(
    'http://' + window.location.hostname + ':9100/sessionsocket',
  );

  // The display will always be asynchronous, with the client is responsible for
  // asking for the current state of the server. This allows for multiple
  // clients to be connected to the same session for easier on-site debugging.
  socketio.on('connect', function (msg) {
    console.log('Connected to socket!');
    // Updating static elements.
    update_tileboard_types();
    request_valid_reference();

    // Starting the status monitor engine
    session.client_engines.monitor_interval = 500;
    clear_status_data(); // For first run clear the status data.
    request_status_update();

    // Sync signals is automatically handled by the server on client connect
  });

  // On disconnect, either because for network errors or host session errors,
  // Stop the continuous monitoring stuff to avoid crashing the client machine
  socketio.on('disconnect', function () {
    // Stopping the monitor engine
    session.client_engines.monitor_interval = -1; // Turning off.
    session.state = STATE_IDLE;
  });

  /**
   * Here are bunch of function that will be run when receiving a sync signal
   * from the server session. These functions will be listed in the sync.js file.
   */
  socketio.on('sync-system-state', sync_system_state);
  socketio.on('sync-session-type', sync_session_type);
  socketio.on('sync-cmd-progress', sync_cmd_progress);
  socketio.on('sync-calib-progress', sync_calib_progress);
  socketio.on('sync-tileboard-type', sync_tileboard_type);
  socketio.on('sync-settings', sync_setting);

  /**
   * Listing socket actions to perform on specific button presses
   * And responding to action-response commands.
   * Functions here will be implemented in the action.js file
   */
  $('#run-system-calibration').on('click', run_system_calibration);
  $('#run-std-calibration').on('click', run_std_calibration);
  $('#user-action-complete').on('click', complete_user_action);
  $('#system-calib-signoff').on('click', system_calibration_signoff);
  $('#standard-calib-signoff').on('click', standard_calibration_signoff);
  $('#debug-request-plot').on('click', debug_request_plot);
  $('#image-settings-update').on('click', image_settings_update);
  $('#zscan-settings-update').on('click', zscan_settings_update);
  $('#lowlight-settings-update').on('click', lowlight_settings_update);
  $('#lumialign-settings-update').on('click', lumialign_settings_update);
  $('#picoscope-settings-update').on('click', picoscope_settings_update);
  $('#drs-settings-update').on('click', drs_settings_update);
  $('#drs-settings-calib').on('click', drs_settings_calib);
  $('#image-settings-clear').on('click', clear_settings);
  $('#zscan-settings-clear').on('click', clear_settings);
  $('#lumialign-settings-clear').on('click', clear_settings);
  $('#lowlight-settings-clear').on('click', clear_settings);
  $('#picoscope-settings-clear').on('click', clear_settings);
  $('#drs-settings-clear').on('click', clear_settings);
  clear_settings(); // Clearing settings when document first loads

  /**
   * Input display syncing
   *
   * In a bunch of inputs, we have both slider (semi-analog) and text inputs We
   * need to allow for client side syncing of the two inputs. Details of these
   * function inputs are placed in the file styling.js. This file also include
   * various animation and eye candy stuff to help improve the UX.
   */
  show_monitor_column();
  $('#action-column-toggle').on('click', toggle_action_column);
  $('#monitor-column-toggle').on('click', toggle_monitor_column);
  $('.input-row > input[type="range"]').on('input', unify_text_to_range);
  $('.input-row > input[type="text"]').on('input', unify_range_to_text);
  $('input[id^="channel-"][id$="-range"]').on('input', unify_pico_range);
  $('input[id^="trigger-level"]').on('input', unify_pico_trigger);
  $('.tab-title').on('click', function () {
    tab_click($(this));
  });
  $('.add-comment-line').on('click', function () {
    add_comment_line($(this));
  });
  update_indicator(); /** Updating all the close-tag icons */

  /**
   * Handling of the terminal interface should it exists. The HTML elements are
   * defined the templates/macro/actions.html file in the terminal_control_tab
   * macro. Terminal related signal handling is defined in the sync.js file
   */
  if ($('#terminal-content').length > 0) {
    // Setting up the terminal to the standard container
    session.terminal.open(document.getElementById('terminal-content'));
    // locking the terminal on start-up
    session.terminal_lock = true;

    // On input
    session.terminal.onData((key) => {
      parse_terminal_keystroke(key);
    });

    // On output.
    socketio.on('xtermoutput', parse_terminal_response);

    // Setting the terminal log
    $('#terminal_lock').on('click', check_terminal_lock);
  }
});
