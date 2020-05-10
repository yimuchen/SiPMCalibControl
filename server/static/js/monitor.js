/**
 * Global variables for monitor-variable plotting.
 */
var monitor_time = [];
var monitor_temperature1 = [];
var monitor_temperature2 = [];
var monitor_voltage1 = [];
var monitor_voltage2 = [];

/**
 * Global variables for tileboard layout stuff
 */
var chip_id_list = [];
var chip_coordinates = {};

/**
 * Global variable for progress monitoring
 */
var progress = {}


/**
 * Gloabl object for cached data
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
  $('#single-chip-summary').html('');
  $('#chip-details-content').html('');
}

function display_message(msg) {
  $('#display-message').html(msg);
}

function monitor_update(msg) {
  update_time(msg);
  update_raw_data(msg);

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

function update_raw_data(msg) {
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
  chip_id_list = []
  chip_coordinates = JSON.parse(String(msg));

  for (var chipid in chip_coordinates) {
    var push = false;

    if (chip_id_list.length == 0) {
      push = true;
    } else {
      if (chipid >= 0) {
        push = true;
      } else if (chip_id_list[0] < 0) {
        push = true;
      }
    }

    if (push) {
      chip_id_list.push(chipid);
    }
  }

  update_tileboard_layout_summary();
}

function make_tileboard_grid_html() {
  if (chip_id_list.length == 64) {
    $('#tile-layout-grid').css('grid-template-columns',
      'auto auto auto auto auto auto auto auto');
  } else {
    $('#tile-layout-grid').css('grid-template-columns', 'auto');
  }

  chip_sort_list = []

  for (var i = 0; i < chip_id_list.length; ++i) {
    chip_sort_list.push({
      'id': chip_id_list[i],
      'x': chip_coordinates[chip_id_list[i]]['orig'][0],
      'y': chip_coordinates[chip_id_list[i]]['orig'][1]
    });
  }

  chip_sort_list.sort((a, b) => (b.y - a.y) * 5000 + (a.x - b.x));

  var new_html = ''

  for (var i = 0; i < chip_sort_list.length; ++i) {
    const chipid = chip_sort_list[i].id
    new_html += `<div id="chip-on-grid-${chipid}"
                      onclick="show_chip_summary(${chipid})">
                  ${chipid}
                </div>`;
  }

  $('#tile-layout-grid').html(new_html);
}

function make_coordinate_string(chipid, tag) {
  if (chip_coordinates[chipid][tag][0] < 0) {
    return 'NOT DONE';
  } else {
    const x = chip_coordinates[chipid][tag][0];
    const y = chip_coordinates[chipid][tag][1];
    return `(${x},${y})`;
  }
}


function make_single_chip_summary_html() {
  // Making a bunch of hidden divs
  new_html = '';
  const plot_processes = ['zscan', 'lowlight'];


  for (var i = 0; i < chip_id_list.length; ++i) {
    const chipid = chip_id_list[i];
    const orig_string = make_coordinate_string(chipid, 'orig');
    const lumi_string = make_coordinate_string(chipid, 'lumi');
    const vis_string = make_coordinate_string(chipid, 'vis');


    var coord_html = ''
    coord_html += `<div class="input-row">
                  <span class="input-name">Chip ID:</span>
                  <span class="input-units"> ${chipid} </span>
                  </div>`;

    coord_html += `<div class="input-row">
                  <span class="input-name">Coordinates:</span>
                  <span class="input-units" id="coord_orig">${orig_string}</span>
                  </div>`;

    coord_html += `<div class="input-row">
                  <span class="input-name">Lumi. coord:</span>
                  <span class="input-units" id="coord-lumi">${lumi_string}</span>
                  </div>`;

    coord_html += `<div class="input-row">
                  <span class="input-name">Vis. coord:</span>
                  <span class="input-units" id="coord-lumi">${vis_string}</span>
                  </div>`;

    var progress_html = '';
    var plot_html = '';

    for (const tag in progress) {
      if (tag == 'current') { continue; }
      if (!(String(chipid) in progress[tag])) { continue; }

      const status = Status_String(progress[tag][chipid]);
      const color = Status_Color(progress[tag][chipid]);
      const fullname = ProcessFullname(tag);
      progress_html += `<div class="input-row">
                        <span class="input-name"
                              id="process-${tag}"
                              style="background-color:${color};">
                              ${status}
                        </span >
                        <span class="input-units">${fullname}</span>
                        </div>\n`;


      if (!plot_processes.includes(tag)) { continue; }
      plot_html += `<div class="plot"
                         id="single-chip-summary-plot-${chipid}-${tag}">
                    </div>`;
    }

    new_html += `<div class="hidden" id="single-chip-summary-${chipid}" >
                   <div class="input-align">
                    ${coord_html} ${progress_html}
                   </div>
                   ${plot_html}
                </div>`
  }

  $('#single-chip-summary').html(new_html);
}

function update_tileboard_layout_summary() {
  if ($('#tile-layout-grid').html() == '') {
    make_tileboard_grid_html();
  }

  if ($('#single-chip-summary').html() == '') {
    make_single_chip_summary_html();
  }
}

function show_chip_summary(chipid) {
  $('#single-chip-summary').children().each(function () {
    $(this).addClass('hidden');
  });

  $('#single-chip-summary').children('#single-chip-summary-' + chipid).removeClass('hidden');
}

function update_readout_result(msg) {
  for (const chipid in msg['zscan']) {
    make_zscan_plot(chipid, msg['zscan'][chipid]);
  }

  for (const chipid in msg['lowlight']) {
    make_lowlight_plot(chipid, msg['lowlight'][chipid]);
  }

  // Waiting 1 seconds before updating the images
  setTimeout(function () {
    socketio.emit('get-configuration', 'readout');
  }, 1000);
}


function make_zscan_plot(chipid, data) {
  var x = []
  var y = []

  for (var i = 0; i < data.length; ++i) {
    x.push(data[i][0]);
    y.push(data[i][1]);
  }

  var plot_data = [{
    x: x,
    y: y,
    type: 'scatter',
    mode: 'markers',
    name: 'Readout value'
  }];


  const plotname = `single-chip-summary-plot-${chipid}-zscan`;
  $('#' + plotname).css('height', '300px');
  $('#' + plotname).css('width', '400px');


  Plotly.newPlot(plotname,
    plot_data,
    Layout_IntensityScan_Plot(),
    Layout_Default_Config());
}

function make_lowlight_plot(chipid, data) {
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
    name: 'Readout value'
  }];


  var plotname = `single-chip-summary-plot-${chipid}-lowlight`;

  $('#' + plotname).css('height', '300px');
  $('#' + plotname).css('width', '400px');

  Plotly.newPlot(plotname,
    plot_data,
    Layout_LowLight_Plot(),
    Layout_Default_Config());
}

function progress_update(prog) {

  // updating the global variable
  progress = prog

  var total_jobs = 0;
  var error_jobs = 0;
  var complete = 0;
  var running_chip = 2147483647;
  var wait_jobs = 0;
  var chip_total = {};
  var chip_complete = {};

  // Calculating the summary percentage.
  for (const tag in progress) {
    if (tag == "current") {
      continue;
    }
    for (const chipid in progress[tag]) {
      if (!(chipid in chip_total)) {
        chip_total[chipid] = 0;
        chip_complete[chipid] = 0;
      }
      total_jobs++;
      chip_total[chipid]++;
      if (progress[tag][chipid] == 1) { wait_jobs++; }
      else if (progress[tag][chipid] == 2) { running_chip = chipid; }
      else if (progress[tag][chipid] == 0) {
        complete++;
        chip_complete[chipid]++;
      }
      else { error_jobs++; }

      // Updating the per chip information
      var element = $('#single-chip-summary-' + chipid).find('#process-' + tag);
      const color = Status_Color(progress[tag][chipid]);
      const status = Status_String(progress[tag][chipid]);
      element.css('background-color', color);
      element.html(status);
    }
  }


  // Updating the total session progress.
  var complete_percent = 100.0 * complete / total_jobs;
  var error_percent = 100.0 * error_jobs / total_jobs;
  var running_percent = running_chip != 2147483647 ? 100.0 / total_jobs : 0;

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
  for (var i = 0; i < chip_id_list.length; ++i) {
    var chipid = chip_id_list[i];
    if (String(chipid) == String(running_chip)) {
      $('#chip-on-grid-' + chipid).css('background-color', 'yellow');
    } else if (chipid in chip_total) {
      const total = chip_total[chipid];
      const comp = chip_complete[chipid];

      const base_color = '#00FF00';
      const lighten = 200.0 * (total - comp) / total;

      $('#chip-on-grid-' + chipid).css('background-color',
        LightenDarkenColor(base_color, lighten));
    }
  }

  // Waiting 0.5 seconds before updating the images
  if (complete + error_jobs != total_jobs) {
    setTimeout(function () {
      socketio.emit('get-configuration', 'progress');
    }, 500);
  }
}

