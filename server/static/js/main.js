/**
 * main.js
 *
 * Defining the socket, how the socket should initializing the document on load,
 * and various interface initializing processes.
 */

var socketio = null;

$(document).ready(function () {

  // Disable all buttons by default. Buttons will be released by action-complete
  // signal from the server.
  $('button.action-button').each(function () {
    $(this).prop('disabled', true);
  });

  // Drawing the common elements of the tileboard layout.
  draw_tileboard_view_common();

  // Connect to the network socket
  socketio
    = io.connect('http://' + window.location.hostname + ':9100/sessionsocket');

  // In case the terminal element is found on the page, start the xterm instance.
  // Additional parsing will be done in the terminal.js file.
  current_line = ''
  if ($('#terminal').length > 0) {
    start_terminal();
    socketio.on('xtermoutput', parse_key_response);
  }


  // The display will always be asynchronous, with the client is responsible for
  // asking for the current state of the server. This allows for multiple
  // clients to be connected to the same session for easier on-site debugging.
  socketio.on('connect', function (msg) {
    console.log('Connected to socket!');
    // Updating static elements, since this is requesting objects from the
    // server side. We are going to add this in the monitor.js file
    update_tileboard_types();
    update_valid_reference();

    // Starting the status update engine
    status_update_flag = true;
    clear_status_data(); // For first run clear the status data.
    iterate_status_update();

    // Checking if a calibration run is in progress
    load_tileboard_and_update();
  });

  // On disconnect, either because for network errors or host session errors,
  // Stop the continuous monitoring stuff to avoid crashing the client machine
  socketio.on('disconnect', function () {
    // Stopping the status update engine
    status_update_flag = false;
    // Stopping the monitoring engine.
    session_state = STATE_IDLE;
  });

  /**
   * Here are bunch of function that will be run when receiving a sync signal
   * from the server session. These functions will be listed in the sync.js file.
   */
  socketio.on('sync-system-state', sync_system_state);
  socketio.on('sync-session-type', sync_session_type);
  socketio.on('sync-settings', sync_setting);

  /**
   * Listing socket actions to perform on specific button presses
   * And responding to action-response commands.
   * Functions here will be implemented in the action.js file
   */
  $('#run-system-calibration').on('click', run_system_calibration);
  $('#run-std-calibration').on('click', run_std_calibration);
  $('#raw-cmd-input').on('click', raw_cmd_input);
  $('#user-action-complete').on('click', complete_user_action);
  $('#system-calib-signoff').on('click', system_calibration_signoff);
  $('#standard-calib-signoff').on('click', standard_calibration_signoff);
  $('#debug-drs-run').on('click', debug_drs_run);

  /**
   * Settings actions
   *
   * Button here will be used to get change the settings used for standard
   * calibration algorithms. Clearing the settings at the start of the connection
   * session.
   *
   * Functions defined the settings.js
   */
  clear_settings(); // Clearing settings when document first loads
  $('#image-settings-update').on('click', image_settings_update);
  $('#zscan-settings-update').on('click', zscan_settings_update);
  $('#lowlight-settings-update').on('click', lowlight_settings_update);
  $('#lumialign-settings-update').on('click', lumialign_settings_update);
  $('#picoscope-settings-update').on('click', picoscope_settings_update);
  $('#drs-settings-update').on('click', drs_settings_update);
  $('#image-settings-clear').on('click', clear_settings);
  $('#zscan-settings-clear').on('click', clear_settings);
  $('#lumialign-settings-clear').on('click', clear_settings);
  $('#lowlight-settings-clear').on('click', clear_settings);
  $('#picoscope-settings-clear').on('click', clear_settings);
  $('#drs-settings-clear').on('click', clear_settings);

  // THe DRS calibration setting is a special case function that needs to be
  // handled with an additional sync signal from the server to be notified of
  // when the calibration is complete
  $('#drs-settings-calib').on('click', drs_settings_calib);
  socketio.on('sync-drs-calib-complete', drs_calib_complete);


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
  $('.input-row > input[type="range"]').on('input', sync_text_to_range);
  $('.input-row > input[type="text"]').on('input', sync_range_to_text);
  $('input[id^="channel-"][id$="-range"]').on('input', sync_pico_range);
  $('input[id^="trigger-level"]').on('input', sync_pico_trigger);
  $('.tab-title').on('click', function () { tab_click($(this)); });
  $('.add-comment-line').on('click',
    function () { add_comment_line($(this)); });
  update_indicator(); /** Updating all the close-tag icons */
});
