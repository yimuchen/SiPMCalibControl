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
    socketio.emit('get-report', 'status');
    // Progress must be initialized before tileboard layout and readout!
    socketio.emit('get-report', 'progress');
    socketio.emit('get-report', 'tileboard-layout');
    socketio.emit('get-report', 'readout');
    socketio.emit('get-report', 'valid-reference')
    socketio.emit('get-report', 'sign-off');

    // Getting the system settings
    socketio.emit('get-report', 'image-settings');
    socketio.emit('get-report', 'zscan-settings');
    socketio.emit('get-report', 'lowlight-settings');
    socketio.emit('get-report', 'lumialign-settings');
    socketio.emit('get-report', 'picoscope-settings');
  });

  /**
   * List of functions regarding the the monitoring tab
   * Functions here will be implemented in the monitor.js file
   */
  socketio.on('confirm', connect_update);
  socketio.on('report-status', status_update);
  // socketio.on('visual-settings-update', visual_settings_update);
  socketio.on('tileboard-layout', init_tileboard_layout);
  socketio.on('update-readout-results', update_readout_result);
  socketio.on('display-message', display_message);
  socketio.on('progress-update', progress_update);
  socketio.on('clear-display', clear_display);
  socketio.on('report-valid-reference', update_valid_reference);
  socketio.on('report-sign-off', show_sign_off);
  socketio.on('signoff-complete', complete_signoff);

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
  $('#image-settings-update').on('click', image_setting_update);
  $('#user-action-complete').on('click', complete_user_action);
  $('#system-calib-signoff').on('click', system_calibration_signoff);
  $('#standard-calib-signoff').on('click', standard_calibration_signoff);

  // Disable all buttons by default
  // Buttons will be released by action-complete signal from the server.
  $('button.action-button').each(function () {
    $(this).prop('disabled', true);
  });

  /**
   * Settings actions
   *
   * Button here will be used to get change the settings used for standard
   * calibration algorithms.
   *
   * Functions defined the settings.js
   */
  $('#image-settings-update').on('click', image_settings_update);
  $('#image-settings-clear').on('click', image_settings_clear);
  socketio.on('report-image-settings', sync_image_settings);
  $('#zscan-settings-update').on('click', zscan_settings_update);
  $('#zscan-settings-clear').one('click', zscan_settings_clear);
  socketio.on('report-zscan-settings', sync_zscan_settings);
  $('#lowlight-settings-update').on('click', lowlight_settings_update);
  $('#lowlight-settings-clear').one('click', lowlight_settings_clear);
  socketio.on('report-lowlight-settings', sync_lowlight_settings);
  $('#lumialign-settings-update').on('click', lumialign_settings_update);
  $('#lumialign-settings-clear').one('click', lumialign_settings_clear);
  socketio.on('report-lumialign-settings', sync_lumialign_settings);
  $('#picoscope-settings-update').on('click', picoscope_settings_update);
  $('#picoscope-settings-clear').on('click', picoscope_settings_clear);
  socketio.on('report-picoscope-settings',sync_picoscope_settings);


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
  $('.add-comment-line').on('click',
    function () { add_comment_line($(this)); });
  update_indicator(); /** Updating all the close-tag icons */


});
