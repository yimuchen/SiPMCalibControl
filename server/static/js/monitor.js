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
 * Global variable for monitoring socket
 */
var monitor_socket = null

/**
 * Global variable for progress monitoring
 */
var progress = {}

/**
 * The main function for real-time status monitoring
 */
$(document).ready(function () {
  monitor_socket
    = io.connect('http://' + window.location.hostname + ':9100/monitor');

  monitor_socket.on('connect', function (msg) {
    console.log('Connected to monitor socket!');
    monitor_socket.emit('get-configuration', 'progress');
    monitor_socket.emit('get-configuration', 'tileboard-layout');
    monitor_socket.emit('get-configuration', 'readout');
  });

  // List of all socket update functions
  monitor_socket.on('confirm', connect_update);
  monitor_socket.on('monitor-update', monitor_update);
  monitor_socket.on('visual-settings-update', visual_settings_update);
  monitor_socket.on('tileboard-layout', init_tileboard_layout);
  monitor_socket.on('update-readout-results', update_readout_result);
  monitor_socket.on('display-message', display_message);
  monitor_socket.on('progress-update', progress_update);
  monitor_socket.on('clear-display', clear_display);
});

function connect_update(msg) {
  console.log('Confirmed!');
  $('#up-time-since').html('Since: ' + msg.start);
  // Wiping exiting monitoring data incase of server restart
  monitor_time = [];
  monitor_temperature1 = [];
  monitor_temperature2 = [];
  monitor_voltage1 = [];
  monitor_voltage2 = [];
}

function clear_display(msg) {
  $('#display-message').html('');
  $('#tile-layout-gird').html('');
  $('#single-chip-summary').html('');
  $('#chip-details-content').html('');
}

function display_message(msg) {
  $('#display-message').html(msg);
}

function monitor_update(msg) {
  update_time(msg);
  update_raw_data(msg);

  plot_data('temperature-plot',
    generate_plotly_temp_data(),
    generate_plotly_temp_layout());
  plot_data('voltage-plot',
    generate_plotly_volt_data(),
    generate_plotly_volt_layout());
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
  // at most keeping 10minutes on display
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

function generate_plotly_temp_data() {
  return [
    {
      x: monitor_time,
      y: monitor_temperature1,
      type: 'scatter',
      name: 'Pulser'
    },
    {
      x: monitor_time,
      y: monitor_temperature2,
      type: 'scatter',
      name: 'Tileboard'
    },
  ];
}

function generate_plotly_temp_layout() {
  return {
    autosize: true,
    xaxis: {
      title: "Time (since system start) [sec]",
      nticks: 10,
      range: [
        monitor_time[0],
        Math.max(parseInt(monitor_time[0]) + 10,
          parseInt(monitor_time[monitor_time.length - 1]) + 0.1)
      ]
    },
    yaxis: {
      title: "Temperature [°C]",
      range: [
        Math.min(15, Math.min(Math.min(...monitor_temperature1),
          Math.min(...monitor_temperature2))),
        Math.max(24, Math.max(Math.max(...monitor_temperature1) + 4,
          Math.max(...monitor_temperature2) + 4))
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

function generate_plotly_volt_data() {
  return [
    {
      x: monitor_time,
      y: monitor_voltage1,
      type: 'scatter',
      name: 'Pulser Bias'
    },
    {
      x: monitor_time,
      y: monitor_voltage2,
      type: 'scatter',
      name: 'Secondary'
    },
  ];
}

function generate_plotly_volt_layout() {
  return {
    autosize: true,
    xaxis: {
      title: "Time (since system start) [sec]",
      nticks: 10,
      range: [
        monitor_time[0],
        Math.max(parseInt(monitor_time[0]) + 10,
          parseInt(monitor_time[monitor_time.length - 1]) + 0.1)
      ]
    },
    yaxis: {
      title: "Measured Voltage [mV]",
      range: [
        Math.min(0, Math.min(Math.min(...monitor_voltage1),
          Math.min(...monitor_voltage1))),
        Math.max(5000, Math.max(Math.max(...monitor_voltage2) + 4,
          Math.max(...monitor_voltage2) + 4))
      ]
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

function visual_settings_update(msg) {
  var settings_list = [
    'threshold', 'blur', 'lumi', 'size', 'ratio', 'poly'
  ]

  settings_list.forEach(function (setting) {
    var id = '#image-' + setting + '-text';
    $(id).val(msg[setting]);
    sync_range_to_text_by_id(id);
  });
}

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
    chipid = chip_sort_list[i].id
    new_html += '<div '
      + ' id="chip-on-grid-' + chipid + '"'
      + ' onclick="show_chip_summary(' + chipid + ')">'
      + chipid + '</div>';
  }

  $('#tile-layout-grid').html(new_html);

}

function make_single_chip_summary_html() {
  // Making a bunch of hidden divs
  new_html = '';
  for (var i = 0; i < chip_id_list.length; ++i) {
    chipid = chip_id_list[i];
    new_html += '<div class="hidden" id="single-chip-summary-' + chipid + '" >'
    new_html += '<div class="input-align">'

    new_html += '<div class="input-row">'
    new_html += '<span class="input-name">Chip ID:</span>'
    new_html += '<span class="input-units">' + chipid + '</span>';
    new_html += '</div>\n'; // END ROW

    new_html += '<div class="input-row">'
    new_html += '<span class="input-name">Coordinates:</span>'
    new_html += '<span class="input-units" id="coord_orig"> ('
      + String(chip_coordinates[chipid]['orig'][0]) + ','
      + String(chip_coordinates[chipid]['orig'][1]) + ')</span>';
    new_html += '</div>\n'; // ENDROW

    new_html += '<div class="input-row">'
    new_html += '<span class="input-name">Lumi. coord:</span>'
    new_html += '<span class="input-units" id="coord-lumi"> (' +
      (chip_coordinates[chipid]['lumi'][0] >= 0 ?
        String(chip_coordinates[chipid]['lumi'][0]) + ','
        + String(chip_coordinates[chipid]['lumi'][1]) :
        'NOT DONE')
      + ')</span>';
    new_html += '</div>\n'; // END ROW

    new_html += '<div class="input-row">'
    new_html += '<span class="input-name">Vis. coord:</span>'
    new_html += '<span class="input-units" id="coord_vis"> (' +
      (chip_coordinates[chipid]['vis'][0] >= 0 ?
        String(chip_coordinates[chipid]['vis'][0]) + ','
        + String(chip_coordinates[chipid]['vis'][1]) :
        'NOT DONE')
      + ')</span>';
    new_html += '</div>\n';

    for (const tag in progress) {
      if (tag == 'current') { continue; }
      if (!(String(chipid) in progress[tag])) { continue; }

      var status = progress[tag][chipid] == 0 ? 'Complete' :
        progress[tag][chipid] == 1 ? 'Pending' :
          progress[tag][chipid] == 2 ? 'Running' :
            'Error'
      var color = progress[tag][chipid] == 0 ? '#00FF00' :
        progress[tag][chipid] == 1 ? 'none' :
          progress[tag][chipid] == 2 ? 'yellow' :
            'red'
      var name = tag == 'vis_align' ? 'Visual alignment' :
        tag == 'zscan' ? 'Intensity scan' :
          tag == 'lowlight' ? 'Low light profile' :
            'Custom'

      new_html += '<div class="input-row">'
      new_html += '<span class="input-name" id="process-' + tag + '"'
        + '  style="background-color:' + color + '"  '
        + ' > ' + status + ' </span > ';
      new_html += '<span class="input-units"> '
        + name + '</span>';
      new_html += '</div>\n'; // END ROW
    }


    new_html += '</div>\n'; // END OF ALIGNED DISPLAY


    // Creating the plots place holders
    for (const tag in progress) {
      if (tag == 'current') { continue; }
      if (!(String(chipid) in progress[tag])) { continue; }

      var plotname = (tag == 'zscan') ? 'intensity-scan' :
        (tag == 'lowlight') ? 'low-light-scan' :
          ''
      console.log(tag, plotname);
      if (plotname == '') { continue; }

      plotname = 'single-chip-summary-plot-' + chipid + '-' + plotname;
      new_html += '<div class="plot" id="' + plotname + '"></div>';
    }

    new_html += '</div>' // END OF SINGLE CHIP DIV
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


function scroll_to_chip_details(chipid) {
  $('html, body').animate({
    scrollTop: $("#chip" + chipid + '-detail').offset().top
  }, 100);
}


function chip_id_attr(tag, id) {
  return tag + id;
}


/**
 * Gloabl object for zscan data
 */
var zscan_data = {}
var lowlight_data = {}


function update_readout_result(msg) {
  for (const chipid in msg['zscan']) {
    make_zscan_plot(chipid, msg['zscan'][chipid]);
  }

  for (const chipid in msg['lowlight']) {
    make_lowlight_plot(chipid, msg['lowlight'][chipid]);
  }

  // Waiting 1 seconds before updating the images
  setTimeout(function () {
    console.log('Requesting update')
    monitor_socket.emit('get-configuration', 'readout');
  }, 500);
}


function make_zscan_plot(chipid, data) {
  x = []
  y = []

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

  var layout = {
    autosize: true,
    xaxis: {
      type: 'log',
      title: "z [mm]",
      autorange: true
    },
    yaxis: {
      type: 'log',
      title: "Readout [V-ns]",
      autorange: true
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {
      l: 60,
      r: 20,
      b: 40,
      t: 20,
      pad: 5
    }, title: false
  };

  var config = {
    'displayModeBar': false
  }
  var plotname = 'single-chip-summary-plot-' + chipid + '-intensity-scan';
  $('#' + plotname).css('height', '300px');
  $('#' + plotname).css('width', '400px');


  Plotly.newPlot(plotname, plot_data, layout, config);
}

function make_lowlight_plot(chipid, data) {
  x = []
  y = []
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

  var layout = {
    autosize: true,
    xaxis: {
      title: "Readout value  [V-ns]",
      autorange: true
    },
    yaxis: {
      type: 'log',
      title: "Events",
      autorange: true
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    bargap: 0,
    margin: {
      l: 60,
      r: 20,
      b: 40,
      t: 20,
      pad: 5
    }, title: false
  };

  var config = {
    'responsive': true,
    'displayModeBar': false
  }

  var plotname = 'single-chip-summary-plot-' + chipid + '-low-light-scan';

  $('#' + plotname).css('height', '300px');
  $('#' + plotname).css('width', '400px');

  Plotly.newPlot(plotname, plot_data, layout, config);
}

function progress_update(prog) {

  // updating the global variable
  progress = prog

  var total_jobs = 0;
  var error_jobs = 0;
  var complete = 0;
  var running_chip = 2147483647;
  var wait_jobs = 0;

  for (const tag in progress) {
    if (tag == "current") {
      continue;
    }
    for (const chipid in progress[tag]) {
      total_jobs++;
      if (progress[tag][chipid] == 1) { wait_jobs++; }
      else if (progress[tag][chipid] == 2) { running_chip = chipid; }
      else if (progress[tag][chipid] == 0) { complete++; }
      else { error_jobs++; }
    }
  }


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
    } else {
      var total_chip_jobs = 0;
      var complete_chip_jobs = 0;
      for (const tag in progress) {
        if (tag == "current") {
          continue;
        }
        if (chipid in progress[tag]) {
          total_chip_jobs++;
          if (progress[tag][chipid] == 0) {
            complete_chip_jobs++;
          }
        }
      }

      var base_color = '#00FF00';
      var lighten = 200.0 * (total_chip_jobs - complete_chip_jobs)
        / total_chip_jobs;

      $('#chip-on-grid-' + chipid).css('background-color',
        LightenDarkenColor(base_color, lighten));

    }
  }

  // Updating the single chip status
  for (const tag in progress) {
    if (tag == 'current') { continue };
    for (const chipid in progress[tag]) {
      var element = $('#single-chip-summary-' + chipid).find('#process-' + tag);
      var color = progress[tag][chipid] == 0 ? '#00FF00' :
        progress[tag][chipid] == 1 ? 'none' :
          progress[tag][chipid] == 2 ? 'yellow' :
            'red';
      var status = progress[tag][chipid] == 0 ? 'Complete' :
        progress[tag][chipid] == 1 ? 'Pending' :
          progress[tag][chipid] == 2 ? 'Running' :
            'Error'
      element.css('background-color', color);
      element.html(status);
    }
  }


  // Waiting 0.5 seconds before updating the images
  if (complete + error_jobs != total_chip_jobs) {
    setTimeout(function () {
      console.log('Requesting progress update')
      monitor_socket.emit('get-configuration', 'progress');
    }, 500);
  }
}


function LightenDarkenColor(col, amt) {
  var usePound = false;
  if (col[0] == "#") {
    col = col.slice(1);
    usePound = true;
  }
  var num = parseInt(col, 16);
  var r = (num >> 16) + amt;
  if (r > 255) r = 255;
  else if (r < 0) r = 0;
  var b = ((num >> 8) & 0x00FF) + amt;
  if (b > 255) b = 255;
  else if (b < 0) b = 0;
  var g = (num & 0x0000FF) + amt;
  if (g > 255) g = 255;
  else if (g < 0) g = 0;
  return (usePound ? "#" : "") + (g | (b << 8) | (r << 16)).toString(16);
}
