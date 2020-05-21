/**
 * Global variables for monitor-variable plotting.
 */
var monitor_time = [];
var monitor_temperature1 = [];
var monitor_temperature2 = [];
var monitor_voltage1 = [];
var monitor_voltage2 = [];
var gantry_coordinate = [];

/**
 * Global variables for tileboard layout stuff
 */
var det_id_list = [];
var det_coordinates = {};

/**
 * Global variable for progress monitoring
 */
var progress = {}


/**
 * Global object for cached data
 */
var zscan_data = {}
var lowlight_data = {}


function connect_update(msg) {
  console.log('Confirmed!');
  $('#up-time-since').html('Since: ' + msg.start);
  // Wiping exiting monitoring data
  monitor_time = [];
  monitor_temperature1 = [];
  monitor_temperature2 = [];
  monitor_voltage1 = [];
  monitor_voltage2 = [];
}

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

function status_update(msg) {
  update_time(msg);
  update_adc_data_display(msg);

  // Re-releasing action buttons if status is idle
  if (msg.state == 0) {
    $('.action-button').each(function () {
      $(this).prop('disabled', false);
    });
  }

  // Waiting 0.5 seconds requesting another update of system status
  setTimeout(function () {
    socketio.emit('get-report', 'status');
  }, 500);

}

function update_time(msg) {
  var time = parseInt(msg.time);

  var time_hour = parseInt(time / 3600);
  var time_min = parseInt((time / 60) % 60);
  var time_sec = parseInt(time % 60);

  $('#up-time').html(
    'Uptime: '
    + time_hour.toString().padStart(2, '0') + ':'
    + time_min.toString().padStart(2, '0') + ':'
    + time_sec.toString().padStart(2, '0')
  );
}

function update_adc_data_display(msg) {
  // at most keeping 10 minutes on display
  if (monitor_time.length >= 600) {
    monitor_time.shift();
    monitor_temperature1.shift();
    monitor_temperature2.shift();
    monitor_voltage1.shift();
    monitor_voltage2.shift();
  }

  monitor_time.push(msg.time);
  monitor_temperature1.push(msg.temp1);
  monitor_temperature2.push(msg.temp2);
  monitor_voltage1.push(msg.volt1);
  monitor_voltage2.push(msg.volt2);

  temperature_data = [{
    x: monitor_time,
    y: monitor_temperature1,
    type: 'scatter',
    name: 'Pulser'
  }, {
    x: monitor_time,
    y: monitor_temperature2,
    type: 'scatter',
    name: 'Tileboard'
  }];

  voltage_data = [{
    x: monitor_time,
    y: monitor_voltage1,
    type: 'scatter',
    name: 'Pulser Bias'
  }, {
    x: monitor_time,
    y: monitor_voltage2,
    type: 'scatter',
    name: 'Secondary'
  }];

  Plotly.newPlot('temperature-plot',
    temperature_data,
    Layout_Temperature_Plot(),
    Layout_Default_Config());

  Plotly.newPlot('voltage-plot',
    voltage_data,
    Layout_Voltage_Plot(),
    Layout_Default_Config());
}


/**
function visual_settings_update(msg) {
  var settings_list = [
    'threshold', 'blur', 'lumi', 'size', 'ratio', 'poly'
  ]

  settings_list.forEach(function (setting) {
    var id = '#image-' + setting + '-text';
    $(id).val(msg[setting]);
    sync_range_to_text(id);
  });
}
*/

function init_tileboard_layout(msg) {
  // Resetting global variables
  det_id_list = []
  det_coordinates = JSON.parse(String(msg));

  for (var detid in det_coordinates) {
    var push = false;

    if (det_id_list.length == 0) {
      push = true;
    } else {
      if (detid >= 0) {
        push = true;
      } else if (det_id_list[0] < 0) {
        push = true;
      }
    }

    if (push) {
      det_id_list.push(detid);
    }
  }

  update_tileboard_layout_summary();
  update_tileboard_layout_coordinates();
}

function make_tileboard_grid_html() {
  if (det_id_list.length == 64) {
    $('#tile-layout-grid').css('grid-template-columns',
      'auto auto auto auto auto auto auto auto');
  } else {
    $('#tile-layout-grid').css('grid-template-columns', 'auto');
  }

  det_sort_list = []

  for (var i = 0; i < det_id_list.length; ++i) {
    det_sort_list.push({
      'id': det_id_list[i],
      'x': det_coordinates[det_id_list[i]]['orig'][0],
      'y': det_coordinates[det_id_list[i]]['orig'][1]
    });
  }

  det_sort_list.sort((a, b) => (b.y - a.y) * 5000 + (a.x - b.x));

  var new_html = ''

  for (var i = 0; i < det_sort_list.length; ++i) {
    const detid = det_sort_list[i].id
    new_html += `<div id="det-on-grid-${detid}"
                      onclick="show_det_summary(${detid})">
                  ${detid}
                </div>`;
  }

  $('#tile-layout-grid').html(new_html);
}

function make_coordinate_string(detid, tag) {
  if (det_coordinates[detid][tag][0] < 0) {
    return 'NOT DONE';
  } else {
    const x = det_coordinates[detid][tag][0].toFixed(2);
    const y = det_coordinates[detid][tag][1].toFixed(2);
    return `(${x},${y})`;
  }
}


function make_single_det_summary_html() {
  // Making a bunch of hidden divs
  var summary_html = '';
  var plot_figure_html = '';
  const plot_processes = ['zscan', 'lowlight', 'lumialign'];
  const can_rerun_process = ['zscan', 'lowlight'];


  for (var i = 0; i < det_id_list.length; ++i) {
    const detid = det_id_list[i];
    const orig_string = make_coordinate_string(detid, 'orig');
    const lumi_string = make_coordinate_string(detid, 'lumi');
    const vis_string = make_coordinate_string(detid, 'vis');


    var coord_html = ''
    coord_html += `<div class="input-row">
                  <span class="input-name">Det ID:</span>
                  <span class="input-units"> ${detid} </span>
                  </div>`;

    coord_html += `<div class="input-row">
                  <span class="input-name">Coordinates:</span>
                  <span class="input-units" id="coord-orig">${orig_string}</span>
                  </div>`;

    coord_html += `<div class="input-row">
                  <span class="input-name">Lumi. coord:</span>
                  <span class="input-units" id="coord-lumi">${lumi_string}</span>
                  <span class="input-units">
                  <button id="rerun-lumi-scan-${detid}"
                          class="action-button",
                          onclick="rerun_single('lumialign','${detid}')"
                          disabled>
                          Rerun</button>
                  </span>
                  </div>`;

    coord_html += `<div class="input-row">
                  <span class="input-name">Vis. coord:</span>
                  <span class="input-units" id="coord-vis">${vis_string}</span>
                  <span class="input-units">
                  <button class="action-button"
                          id="rerun-vis-scan-${detid}"
                          onclick="rerun_single('visalign','${detid}')"
                          disabled>
                          Rerun</button>
                  </span>
                  </div>`;

    var progress_html = '';
    var plot_html = '';

    for (const tag in progress) {
      if (tag == 'current') { continue; }
      if (!(String(detid) in progress[tag])) { continue; }

      const status = Status_String(progress[tag][detid]);
      const color = Status_Color(progress[tag][detid]);
      const fullname = ProcessFullname(tag);
      progress_html += `<div class="input-row">
                        <span class="input-name"
                              id="process-${tag}"
                              style="background-color:${color};">
                              ${status}
                        </span >
                        <span class="input-units">${fullname}</span>`
      if (can_rerun_process.includes(tag)) {
        progress_html += `<span class="input-units">
                          <button id="rerun-${tag}-${detid}"
                                  class="action-button"
                                  onclick="rerun_single('${tag}','${detid}')"
                                  disabled>
                                  Rerun
                          </button>
                          </span>`
      }
      progress_html += `</div>\n`;


      if (!plot_processes.includes(tag)) { continue; }
      plot_html += `<div class="plot"
                         id="single-det-summary-plot-${detid}-${tag}">
                    </div>`;
    }

    summary_html += `<div id="single-det-summary-${detid}" class="hidden">
                      <div class="input-align">
                      ${coord_html} ${progress_html}
                     </div>
                     </div>`

    plot_figure_html += `<div class="hidden" id="det-plot-container-${detid}">
                         <div class="plot-container">
                         ${plot_html}
                         </div>
                         </div>`
  }

  $('#single-det-summary').html(summary_html);
  $('#det-plot-and-figure').html(plot_figure_html);
}

function update_tileboard_layout_summary() {
  if ($('#tile-layout-grid').html() == '') {
    make_tileboard_grid_html();
  }

  if ($('#single-det-summary').html() == '') {
    make_single_det_summary_html();
  }

}

function update_tileboard_layout_coordinates() {
  for (var index = 0; index < det_id_list.length; ++index) {
    const detid = det_id_list[index];
    var cont = $(`#single-det-summary-${detid}`);
    cont.find('#coord-lumi').html(make_coordinate_string(detid, 'lumi'));
    cont.find('#coord-vis').html(make_coordinate_string(detid, 'vis'));
  }
}


function show_det_summary(detid) {
  $('#single-det-summary').children().each(function () {
    $(this).addClass('hidden');
  });

  $('#det-plot-and-figure').children().each(function () {
    $(this).addClass('hidden');
  })

  $('#single-det-summary').children('#single-det-summary-' + detid).removeClass('hidden');

  $('#det-plot-and-figure').children('#det-plot-container-' + detid).removeClass('hidden');
}

function update_readout_result(msg) {
  for (const detid in msg['zscan']) {
    make_zscan_plot(detid, msg['zscan'][detid]);
  }

  for (const detid in msg['lowlight']) {
    make_lowlight_plot(detid, msg['lowlight'][detid]);
  }

  for (const detid in msg['lumialign']) {
    make_lumialign_plot(detid, msg['lumialign'][detid]);
  }

  // Waiting 1 seconds before updating the images
  setTimeout(function () {
    socketio.emit('get-report', 'readout');
  }, 1000);
}


function make_zscan_plot(detid, data) {
  var x = []
  var y = []
  var b = []

  for (var i = 0; i < data.length; ++i) {
    x.push(data[i][0]);
    y.push(data[i][1]);
    b.push(data[i][2] / 1000);
  }

  var plot_data = [{
    x: x,
    y: y,
    marker: {
      size: 5,
      color: b,
      colorscale: 'Bluered',
      colorbar: {
        title: "Bias [V]"
      }
    },
    type: 'scatter',
    mode: 'markers',
    name: 'Readout value'
  }];


  const plotname = `single-det-summary-plot-${detid}-zscan`;

  if ($('#' + plotname).length != 0) {
    $('#' + plotname).css('height', '300px');
    $('#' + plotname).css('width', '400px');


    Plotly.newPlot(plotname,
      plot_data,
      Layout_IntensityScan_Plot(),
      Layout_Default_Config());
  } else {
    console.log("Warning! DIV for plot doesn't exist");
  }
}

function make_lowlight_plot(detid, data) {
  var x = []
  var y = []
  for (var i = 0; i < data[0].length; ++i) {
    y.push(data[0][i]);
    x.push((data[1][i] + data[1][i + 1]) / 2.0);
  }

  var plot_data = [{
    x: x,
    y: y,
    type: 'bar',
    mode: 'markers',
    name: 'Readout value',
    marker: {
      color: lowlight_bar_color
    }
  }];


  var plotname = `single-det-summary-plot-${detid}-lowlight`;


  if ($('#' + plotname).length != 0) {
    $('#' + plotname).css('height', '300px');
    $('#' + plotname).css('width', '400px');
    Plotly.newPlot(plotname,
      plot_data,
      Layout_LowLight_Plot(),
      Layout_Default_Config());
  } else {
    console.log("Warning! DIV for plot doesn't exist");
  }
}

function make_lumialign_plot(detid, data) {
  var x = []
  var y = []
  var lumi = []
  for (var i = 0; i < data.length; ++i) {
    x.push(data[i][0]);
    y.push(data[i][1]);
    lumi.push(data[i][2]);
  }

  var plot_data = [{
    x: x,
    y: y,
    z: lumi,
    type: 'contour',
    colorscale: 'RdBu',
  }];

  var plotname = `single-det-summary-plot-${detid}-lumialign`;
  if ($('#' + plotname).length != 0) {
    $('#' + plotname).css('height', '300px');
    $('#' + plotname).css('width', '400px');
    Plotly.newPlot(plotname,
      plot_data,
      Layout_LumiAlign_Plot(),
      Layout_Default_Config());
  } else {
    console.log("Warning! DIV for plot doesn't exist")
  }
}


function progress_update(prog) {
  // updating the global variable
  progress = prog

  var total_jobs = 0;
  var error_jobs = 0;
  var complete = 0;
  var running_det = 2147483647;
  var wait_jobs = 0;
  var det_total = {};
  var det_complete = {};

  // Calculating the summary percentage.
  for (const tag in progress) {
    if (tag == "current") {
      continue;
    }
    for (const detid in progress[tag]) {
      if (!(detid in det_total)) {
        det_total[detid] = 0;
        det_complete[detid] = 0;
      }
      total_jobs++;
      det_total[detid]++;
      if (progress[tag][detid] == 1) { wait_jobs++; }
      else if (progress[tag][detid] == 2) { running_det = detid; }
      else if (progress[tag][detid] == 0) {
        complete++;
        det_complete[detid]++;
      }
      else { error_jobs++; }

      // Updating the per det information
      var element = $('#single-det-summary-' + detid).find('#process-' + tag);
      const color = Status_Color(progress[tag][detid]);
      const status = Status_String(progress[tag][detid]);
      element.css('background-color', color);
      element.html(status);
    }
  }


  // Updating the total session progress.
  var complete_percent = 100.0 * complete / total_jobs;
  var error_percent = 100.0 * error_jobs / total_jobs;
  var running_percent = running_det != 2147483647 ? 100.0 / total_jobs : 0;

  var bar_elem = $('#session-progress').children('.progress-bar-container');

  bar_elem.children('.progress-complete').css('width', complete_percent + '%');
  bar_elem.children('.progress-running').css('width', running_percent + '%');
  bar_elem.children('.progress-error').css('width', error_percent + '%');


  // Making the command progress bar
  if ('current' in progress) {
    var command_total = progress['current'][1];
    var command_completed = progress['current'][0];
    var percent = 100.0 * command_completed / command_total;

    $('#command-progress').children('.progress-bar-container')
      .children('.progress-complete').css('width', percent + '%');
  } else {
    $('#command-progress').children('.progress-bar-container')
      .children('.progress-complete').css('width', '0%');
  }

  // Updating the tile layout summary
  for (var i = 0; i < det_id_list.length; ++i) {
    var detid = det_id_list[i];
    if (String(detid) == String(running_det)) {
      $('#det-on-grid-' + detid).css('background-color', 'yellow');
    } else if (detid in det_total) {
      const total = det_total[detid];
      const comp = det_complete[detid];

      const base_color = '#00FF00';
      const lighten = 200.0 * (total - comp) / total;

      $('#det-on-grid-' + detid).css('background-color',
        LightenDarkenColor(base_color, lighten));
    }
  }

  // Waiting 0.5 seconds before updating the images
  if (complete + error_jobs != total_jobs) {
    setTimeout(function () {
      socketio.emit('get-report', 'progress');
    }, 500);
  }
}


function update_valid_reference(data) {
  var element = $('#reference-system-calibration');
  var new_html = ''
  for (var i = 0; i < data.length; ++i) {
    const header = i == 0 ? 'Reference' : '';
    const display = data[i];
    new_html += `<div class="input-row">
                 <span class="input-name">${header}</span>
                 <span class="input-units">
                 <input type="radio"
                        name="ref-calibration"
                        value="${display}" />
                 </span>
                    <span class="input-units">${display}</span>
                 </div>`
  }
  element.html(new_html);
}

function show_sign_off(data) {
  $(`#${data}-calib-signoff-container`).removeClass("hidden");
}