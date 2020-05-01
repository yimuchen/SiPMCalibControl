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
var chip_x_list = []
var chip_y_list = []
var chip_lumi_x_list = []
var chip_lumi_y_list = []
var chip_vis_x_list = []
var chip_vis_y_list = []

/**
 * Global variable for monitoring socket
 */
var monitor_socket = null

/**
 * The main function for real-time status monitoring
 */
$(document).ready(function () {
  monitor_socket
    = io.connect('http://' + window.location.hostname + ':9100/monitor');

  monitor_socket.on('connect', function (msg) {
    console.log('Connected to monitor socket!');
    monitor_socket.emit('get-configuration', 'tileboard-layout');
    monitor_socket.emit('get-configuration', 'readout');
  });

  // List of all socket update functions
  monitor_socket.on('confirm', connect_update);
  monitor_socket.on('monitor-update', monitor_update);
  monitor_socket.on('visual-settings-update', visual_settings_update);
  monitor_socket.on('tileboard-layout', init_tileboard_layout);
  monitor_socket.on('update-readout-results', update_readout_result);
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
      title: "Temperature [C]",
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
      r: '0',
      b: '40',
      t: '10',
      pad: 0
    },
    width: 400,
    height: 400,
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
      l: '40',
      r: '0',
      b: '40',
      t: '10',
      pad: 0
    },
    width: 400,
    height: 400,
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
  var coord = JSON.parse(msg);

  // Resetting global variables
  chip_id_list = []
  chip_x_list = []
  chip_y_list = []
  chip_lumi_x_list = []
  chip_lumi_y_list = []
  chip_vis_x_list = []
  chip_vis_y_list = []
  chip_info_text = []
  for (const chipid in coord['orig_x']) {
    chip_id_list.push(chipid);
    var chip_x = coord['orig_x'][chipid];
    var chip_y = coord['orig_y'][chipid];
    var lumi_x = coord['lumi_x'][chipid] != -100 ?
      coord['lumi_x'][chipid] : NaN;
    var lumi_y = coord['lumi_x'][chipid] != -100 ?
      coord['lumi_y'][chipid] : NaN;
    var vis_x = coord['vis_x'][chipid] != -100 ?
      coord['vis_x'][chipid] : NaN;
    var vis_y = coord['vis_x'][chipid] != -100 ?
      coord['vis_y'][chipid] : NaN;

    chip_x_list.push(chip_x);
    chip_y_list.push(chip_y);
    chip_lumi_x_list.push(lumi_x);
    chip_lumi_y_list.push(lumi_y);
    chip_vis_x_list.push(vis_x);
    chip_vis_y_list.push(vis_y);

    chip_info_text.push('Chip ID: ' + chipid + '<br />'
      + 'Vis: (' + vis_x + ',' + chip_y + ') <br />'
      + 'Lumi: (' + lumi_x + ',' + lumi_y + ') <br />'
    );
  }

  update_chip_details_content(coord);
  update_tileboard_layout_plot();
}

function update_tileboard_layout_plot() {
  var plot_data = [{
    x: chip_x_list,
    y: chip_y_list,
    hovertemplate: 'Est: (%{x:.1f},%{y:.1f})<br />' + '%{text}',
    text: chip_info_text,
    type: 'scatter',
    mode: 'markers',
    name: 'In-built'
  }, {
    x: chip_lumi_x_list,
    y: chip_lumi_y_list,
    hoverinfo: 'skip',
    type: 'scatter',
    mode: 'markers',
    name: 'Lumi. pos.'
  }, {
    x: chip_vis_x_list,
    y: chip_vis_y_list,
    hoverinfo: 'skip',
    type: 'scatter',
    mode: 'markers',
    name: 'Vis. pos.'
  }]

  var layout = {
    xaxis: {
      title: "x [mm]",
      nticks: 10,
      range: [0, 500]
    },
    yaxis: {
      title: "y [mm]",
      nticks: 10,
      range: [0, 500]
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {
      l: '40',
      r: '0',
      b: '40',
      t: '10',
      pad: 0
    },
    width: 400,
    height: 400,
    legend: {
      x: 1,
      y: 1
    }

  }

  Plotly.newPlot('tile-layout-plot', plot_data, layout);

  // Plotly uses vanilla javascript to access page elements
  var layout_plot = document.getElementById('tile-layout-plot');

  layout_plot.on('plotly_click', function (data) {
    var id = data.points[0].pointNumber;
    var elem = '#chip' + id + '-detail';
    if ($(elem).length) {
      $(document).scrollTop($(elem).offset().top);
    }
  });
}

function chip_id_attr(tag, id) {
  return tag + id;
}


var zscan_data = {}
var lowlight_data = {}

function update_chip_details_content(orig_coord) {
  // Clearin the content
  $('#chip-details-content').html('');

  var list_html = '<div id="chip-list">';
  var chip_html = '';
  for (const chipid in orig_coord['orig_x']) {
    list_html += '<a href="#chip' + chipid + '-detail">' + chipid + '</a>\n';
    chip_html += '<div id="chip' + chipid + '-detail" class="chip-details-content">'
      + '<div class="chip-name">Chip ID: ' + chipid + '</div><br/>'
      + '<div class="calib-plot-container">'
      + '<div '
      + ' class="calib-plot" '
      + ' id="intensity_plot_' + chipid + '" '
      + '/>'
      + '<div '
      + ' class="calib-plot" '
      + ' id="lowlight_plot_' + chipid + '" '
      + ' />'
      + "</div>"
      + '<div id="chip' + chipid + '-status"></div>'
      + '</div>'
  }

  $('#chip-details-content').html(list_html + chip_html);
}


function update_readout_result(msg) {
  console.log('Chip updates recieved', msg);

  console.log(msg['zscan']);
  console.log(msg['lowlight']);

  for (const chipid in msg['zscan']) {
    console.log('Making zscan plot', chipid)
    make_zscan_plot(chipid, msg['zscan'][chipid]);
  }

  for (const chipid in msg['lowlight']) {
    console.log('Making lowlight plot', chipid);
    make_lowlight_plot(chipid, msg['lowlight'][chipid]);
  }

  // Waiting 1 seconds before updating the images
  setTimeout(function () {
    console.log('Requesting update')
    monitor_socket.emit('get-configuration', 'readout');
  }, 1000);
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

  Plotly.newPlot('intensity_plot_' + chipid, plot_data, layout, config);
}

function make_lowlight_plot(chipid, data) {
  console.log('In make_lowlight_plot function...');
  console.log(data);
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
    'displayModeBar': false
  }


  Plotly.newPlot('lowlight_plot_' + chipid, plot_data, layout, config);
}