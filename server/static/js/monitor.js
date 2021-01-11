/**
 * Global variables for status monitoring.
 *
 * The structure of this object should mirror the return value of the python
 * script. Except with potential time dependent storage.
 */
var session_status = {
  start: '',
  time: [],
  temperature1: [],
  temperature2: [],
  voltage1: [],
  voltage2: [],
  gantry_position: [],
};

/**
 * Global variable for progress monitoring
 */
var progress = {}


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
 * The continuous status update engine.
 *
 * A boolean flag is used to allow the update to terminate (should be very niche
 * for this particular engine), and a constant variable is used for the update
 * interval. The start function contains just the ajax command, and the bare
 * information parsing. The detailed function requiring DOM manipulations are
 * split out into various functions.
 */
var status_update_flag = false;
const status_update_interval = 500;

function status_update_start() {
  $.ajax({
    dataType: 'json',
    mimeType: 'application/json',
    url: `report/status`,
    async: false,
    success: function (json) {
      // Storing the object results
      session_status.start = json.start;
      session_status.time.push(json.time);
      session_status.temperature1.push(json.temp1);
      session_status.temperature2.push(json.temp2);
      session_status.voltage1.push(json.volt1);
      session_status.voltage2.push(json.volt2);
      session_status.gantry_position = json.coord;

      // Functions called for updating the HTML
      status_update_time();
      status_update_monitor_data();
      status_update_coordinates();
    },
    error: function () {
      console.log('status update failed');
      if (status_update_flag == true) {
        setTimeout(status_update_start, status_update_interval);
      }
    }
  });

  if (status_update_flag) {
    setTimeout(status_update_start, status_update_interval);
  }
}

/**
 * Updating the uptime display container:
 */
function status_update_time() {
  const time = parseInt(session_status.time);
  const time_hour = parseInt(time / 3600).toString().padStart(2, 0);
  const time_min = parseInt((time / 60) % 60).toString().padStart(2, 0);
  const time_sec = parseInt(time % 60).toString().padStart(2, 0);
  const state_str = session_state == STATE_IDLE ? `IDLE` :
    session_state == STATE_RUN_PROCESS ? `RUNNING` :
      session_state == STATE_WAIT_USER ? `WAITING UESR ACTION` :
        ``
  $(`#up-time`).html(`Uptime: ${time_hour}:${time_min}:${time_sec}`);
  $('#up-time-since').html(
    `Session is: ${state_str} </br>
     Since: ${session_status.start}`
  );
}

/**
 * Plotting the the monitoring data. Styling information is placed at the bottom
 * of the file to reduce verbosity.
 */
function status_update_monitor_data() {
  // at most keeping 10 minutes on display
  if (session_status.time.length >= 600) {
    session_status.time.shift();
    session_status.temperature1.shift();
    session_status.temperature2.shift();
    session_status.voltage1.shift();
    session_status.voltage2.shift();
  }

  temperature_data = [{
    x: session_status.time,
    y: session_status.temperature1,
    type: 'scatter',
    name: 'Pulser'
  }, {
    x: session_status.time,
    y: session_status.temperature2,
    type: 'scatter',
    name: 'Tileboard'
  }];

  voltage_data = [{
    x: session_status.time,
    y: session_status.voltage1,
    type: 'scatter',
    name: 'Pulser board Bias'
  }, {
    x: session_status.time,
    y: session_status.voltage2,
    type: 'scatter',
    name: 'Secondary'
  }];

  Plotly.newPlot('temperature-plot',
    temperature_data,
    temperature_plot_layout(),
    layout_default_config);

  Plotly.newPlot('voltage-plot',
    voltage_data,
    voltage_plot_layout(),
    layout_default_config);
}

/**
 * Temperature plot requires dynamic settings for custom range.
 */
function temperature_plot_layout() {
  return {
    autosize: true,
    xaxis: {
      title: "Time (since system start) [sec]",
      nticks: 10,
      range: [
        session_status.time[0],
        Math.max(parseInt(session_status.time[0]) + 10,
          parseInt(session_status.time[session_status.time.length - 1]) + 0.1)
      ]
    },
    yaxis: {
      title: "Temperature [°C]",
      range: [
        Math.min(15, Math.min(...session_status.temperature1),
          Math.min(...session_status.temperature2)),
        Math.max(24, Math.max(...session_status.temperature1) + 4,
          Math.max(...session_status.temperature2) + 4)
      ]
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {
      l: '40',
      r: '5',
      b: '40',
      t: '10',
      pad: 0
    },
    legend: {
      x: 0.5,
      y: 0.9
    }
  };
}

/**
 * Voltage plot requires a custom range
 */
function voltage_plot_layout() {
  return {
    autosize: true,
    xaxis: {
      title: "Time (since system start) [sec]",
      nticks: 10,
      range: [
        session_status.time[0],
        Math.max(parseInt(session_status.time[0]) + 10,
          parseInt(session_status.time[session_status.time.length - 1]) + 0.1)
      ]
    },
    yaxis: {
      title: "Voltage [mV]",
      range: [0, 5000]
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {
      l: '60',
      r: '5',
      b: '40',
      t: '10',
      pad: 0
    },
    legend: {
      x: 0.5,
      y: 0.9
    }
  };
}

const layout_default_config = {
  'displayModeBar': false,
  'responsive': true
}

/**
 * Two parts needs to be updated regarding the values. One is a text based
 * display of the coordinates values in the monitor tab. The other is the
 * graphical elements in the tileboard view.
 */
function status_update_coordinates() {
  const x = session_status.gantry_position[0];
  const y = session_status.gantry_position[1];
  const z = session_status.gantry_position[2];
  $(`#gantry-coordinates`).html(
    `Gantry coordinates: (${x.toFixed(1)}, ${y.toFixed(1)}, ${z.toFixed(1)})`
  );

  var new_html = ``
    new_html += `<polyline points="${x+20},${510-y}
                                   ${x+25},${525-y}
                                   ${x+30},${510-y}"
                  stroke="red"
                  fill="red"
                  stroke-width="1px"/>`
    new_html += `<polyline points="548,${520-z}
                                   538,${525-z}
                                   548,${530-z}"
                  stroke="red"
                  fill="red"
                  stroke-width="1px"/>`

  $("#tile-layout-gantry-svg").html(new_html);

}

/**
 * Function to be called when a new session connection is established. Clearing
 * out all cached monitor data.
 */
function clear_status_data() {
  session_status.start = '';
  session_status.time = [];
  session_status.temperature1 = [];
  session_status.temperature2 = [];
  session_status.voltage1 = [];
  session_status.voltage2 = [];
  session_status.gantry_position = [0, 0, 0];
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
    async: false,
    success: function (json) {
      let new_html = list_type != 'standard' ? `` :
        `<div class="input-row">
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
          </div>`
      }

      $(`#${list_type}-calibration-boardtype-container`).html(new_html);
    },
    error: function () {
      console.log(`Failed to update tile board types`)
      setTimeout(update_tileboard_list(list_type), 500);
    }
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
    async: false,
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
                     </div>`
      }
      $('#standard-calibration-boardtype-container').html(new_html);
    },
    error: function () {
      console.log(`Failed to update reference sessions`)
      setTimeout(update_valid_reference(), 500);
    }
  });
}