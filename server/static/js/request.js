/********************************************************************************
 *
 * request.js
 *
 * The handling of the AJAX request to be initiated from client side. Here, the
 * data processing should only be up to the manipulation of the data defined in
 * the global.js related variables, or single line element edits. Any more
 * processing with the manipulation of the display elements should be placed in
 * the corresponding view/*.js files.
 *
 *******************************************************************************/

const { ajax } = require('jquery');

/**
 * Master function for submitting an AJAX request, since most of all return types
 * are JSON object. The user is responsible for providing:
 * - The URL for the request
 * - The function to execute on success.
 * - A retry interval (leave negative if the request should not be done)
 * - A custom fail message (leave blank if default)
 */
async function ajax_request(
  url,
  success,
  retry = -1,
  fail_msg = '',
  max_try = 10,
) {
  $.ajax({
    dataType: 'json',
    mimeType: 'application/json',
    url: url,
    success: success,
    error: async function () {
      // Logging the fail message
      msg = fail_msg == '' ? `AJAX request for URL "${url}" failed.` : fail_msg;
      console.log(msg);

      if (retry > 0 && max_try > 0) {
        if (max_try > 0) {
          await sleep(retry);
          ajax_request(url, success, retry, fail_msg, max_try - 1);
        } else {
          console.log(
            `Failed too many times, not attempting ajax request at ${url}`,
          );
        }
      }
    },
  });
}

/**
 * Clear client side settings. Request a new set of setting from server side and
 * update accordingly.
 */
async function clear_settings() {
  ajax_request('report/settings', update_settings, 500);
}

/**
 * Requesting the latest monitor information.
 *
 * Notice that the global variable in the session.client_engines is used to
 * detected how frequently the monitoring data should be updated or whether a
 * request should be closed. The detailed function requiring DOM manipulations
 * are split defined in the view/monitor.js file.
 */
async function request_status_update() {
  if (session.client_engines.monitor_interval < 0) {
    return; // Early exit is interval is smaller than 0
  }
  ajax_request(
    'report/status',
    async function (json) {
      // Storing the object results
      session.monitor.start = json.start;
      session.monitor.time.push(json.time);
      session.monitor.temperature1.push(json.temp1);
      session.monitor.temperature2.push(json.temp2);
      session.monitor.voltage1.push(json.volt1);
      session.monitor.voltage2.push(json.volt2);
      session.monitor.gantry_position = json.coord;

      // Defined in view/monitor.js
      status_update_time();
      status_update_monitor_data();
      status_update_coordinates();
      await sleep(session.client_engines.monitor_interval);
      request_status_update();
    },
    session.client_engines.monitor_interval,
  );
}

/**
 * Function for requesting plot data directly by filename.
 *
 * The following inputs is required:
 * - The filename used to extract plotting information.
 * - The plot-type to reduce the information.
 * - The element id to store the plot.
 *
 * The file name needs to be adjusted to replace the slashed with a unique
 * character not typically used for file naming while being URL safe (ex. using
 * @ for now).
 */
async function request_plot_by_file(filename, type, id) {
  ajax_request(
    `databyfile/${type}/${filename.replaceAll('/', '@')}`,
    async function (json) {
      parse_plot_data(json, id);
    },
  );
}

/**
 * Function for requesting plot data by some detector ID of the current
 * calibration session.
 *
 * The following inputs is required:
 * - A legal detector ID in the current calibration session.
 * - The plot-type to reduce the information.
 * - The element id to store the plot.
 *
 * In the case that the corresponding data file is not found. A console log is
 * generated.
 */
async function request_plot_by_detid(detid, type, id) {
  ajax_request(
    `data/${type}/${detid}`,
    async function (json) {
      parse_plot_data(json, id);
    },
  );
}

/**
 * Updating the list of tileboards that are available in the calibration server
 * settings. This is done by submitting an ajax request to the tileboard-type.
 * For both the system and standard calibration processes.
 */
function update_tileboard_types() {
  update_tileboard_list(`system`);
  update_tileboard_list(`standard`);
}

function update_tileboard_list(list_type) {
  $.ajax({
    dataType: 'json',
    mimeType: 'application/json',
    url: `report/${list_type}boards`,
    success: function (json) {
      let new_html =
        list_type != 'standard'
          ? ``
          : `<div class="input-row">
                      <span class="input-name">Board ID</span>
                      <span class="input-units"></span>
                      <input type="text"
                             id="std-calibration-boardid"
                             class="input-units" />
                    </div>`;
      let first = true;
      for (var boardtype in json) {
        const prefix = first ? 'Board type' : '';
        first = false;
        new_html += `
          <div class="input-row">
            <span class="input-name">${prefix}</span>
            <input type="radio"
                   name="${list_type}-calibration-boardtype"
                   value="${boardtype}" />
            <span class="input-units">
              ${json[boardtype]['name']}
              (${json[boardtype]['number']})
            </span>
          </div>`;
      }

      $(`#${list_type}-calibration-boardtype-container`).html(new_html);
    },
    error: function () {
      console.log(`Failed to update tile board types`);
    },
  });
}

/**
 * Updating the display of reference calibration results available. This is
 * performed via an AJAX request.
 */
function update_valid_reference() {
  $.ajax({
    dataType: 'json',
    mimeType: 'application/json',
    url: `report/validreference`,
    success: function (json) {
      // clearing the html containers for references
      $('#standard-calibration-boardtype-container')
        .children('.input-row')
        .each(function () {
          if ($(this).find("input[name='ref-calibration']").length > 0) {
            $(this).html(``);
          }
        });

      // Making the new reference calibration objects
      let new_html = $('#standard-calibration-boardtype-container').html();
      for (var i = 0; i < json.valid.length; ++i) {
        const header = i == 0 ? 'Reference' : '';
        const display = json.valid[i];
        new_html += `<div class="input-row">
                       <span class="input-name">${header}</span>
                       <span class="input-units">
                       <input type="radio"
                              name="ref-calibration"
                              value="${json.valid[i].tag}" />
                       </span>
                          <span class="input-units">
                            ${json.valid[i].boardtype}
                            (${json.valid[i].time})
                          </span>
                     </div>`;
      }
      $('#standard-calibration-boardtype-container').html(new_html);
    },
    error: function () {
      console.log(`Failed to update reference sessions`);
    },
  });
}

/**
 * Getting the user action string
 */
function request_user_action() {
  ajax_request('report/useraction', function (json) {
    $('#user-action-msg').html(json);
  });
}
