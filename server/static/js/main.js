/**
 * main.js
 *
 * Defining the socket, how the socket should initializing the document on load,
 * and various interface initializing processes.
 */

var socketio = null;

$(document).ready(function () {
  socketio
    = io.connect('http://' + window.location.hostname + ':9100/sessionsocket');

  socketio.on('connect', function (msg) {
    console.log('Connected to socket!');
    socketio.emit('get-configuration', 'progress');
    socketio.emit('get-configuration', 'tileboard-layout');
    socketio.emit('get-configuration', 'readout');
  });

  /**
   * List of functions regarding the the monitoring tab
   * Functions here will be implemented in the monitor.js file
   */
  socketio.on('confirm', connect_update);
  socketio.on('monitor-update', monitor_update);
  // socketio.on('visual-settings-update', visual_settings_update);
  socketio.on('tileboard-layout', init_tileboard_layout);
  socketio.on('update-readout-results', update_readout_result);
  socketio.on('display-message', display_message);
  socketio.on('progress-update', progress_update);
  socketio.on('clear-display', clear_display);

  /**
   * Listing socket actions to perform on specific button presses
   * And responding to action-response commands.
   * Functions here will be implemented in the action.js file
   */
  socketio.on('useraction', display_user_action);
  socketio.on('action-received', action_received);
  socketio.on('action-complete', action_complete);

  $('#run-system-calibration').on('click', run_system_calibration);
  $('#run-std-calibration').on('click', run_std_calibration);
  $('#raw-cmd-input').on('click', raw_cmd_input);
  $('#image-setting-update').on('click', image_setting_update);
  $('#user-action-complete').on('click', complete_user_action);

  // Disable all buttons by default
  // Buttons will be released by action-complete signal from the server.
  $('button').each(function () { $(this).prop('disabled', true); });


  /**
   * Input display syncing
   *
   * In a bunch of inputs, we have both slider (semi-analog) and text inputs We
   * need to allow for client side syncing of the two inputs. Details of these
   * function inputs are placed in the file input_sync.js. This file also include
   * various animation and eye candy stuff to help improve the UX.
   */
  $('.input-row > input[type="range"]').on('input', sync_text_to_range);
  $('.input-row > input[type="text"]').on('input', sync_range_to_text);
  $('input[id^="channel-"][id$="-range"]').on('input', sync_pico_range);
  $('input[id^="trigger-level"]').on('input', sync_pico_trigger);
  $('.tab-title').on('click', function () { tab_click($(this)); });

  update_indicator(); /** Updating all the close-tag icons */
});
