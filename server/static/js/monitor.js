/**
 * Global variables for monitor-variable plotting.
 */
var monitor_time = [];
var monitor_temperature1 = [];
var monitor_temperature2 = [];
var monitor_voltage1 = [];
var monitor_voltage2 = [];

/**
 * The main function for real-time status monitoring
 */
$(document).ready(function () {
  var socket = io.connect("http://localhost:9100");

  // List of all socket update functions
  socket.on('connect', function (msg) { console.log('Connected!'); });
  socket.on('confirm', connect_update);
  socket.on('monitor-update', monitor_update);
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

  var temperature_data = generate_plotly_temp_data();

  if ($('#temperature-plot').hasClass('updated')) {
    update_plot('temperature-plot', temperature_data
      , generate_plotly_temp_layout_update());
  } else {
    makenew_plot('temperature-plot', temperature_data
      , generate_plotly_temp_layout());
  }
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

function generate_plotly_temp_layout_update() {
  return {
    'xaxis.range': [
      monitor_time[0],
      Math.max(parseInt(monitor_time[0]) + 10,
        parseInt(monitor_time[monitor_time.length - 1]) + 0.1)
    ],
    'yaxis.range': [
      Math.min(15, Math.min(Math.min(...monitor_temperature1),
        Math.min(...monitor_temperature2))),
      Math.max(24, Math.max(Math.max(...monitor_temperature1) + 4,
        Math.max(...monitor_temperature2) + 4))
    ]
  };
}

function generate_plotly_temp_layout() {
  return {
    xaxis: {
      title: "Time (since system start) [sec]",
      nticks: 10,
      range: [monitor_time[0], parseInt(monitor_time[0]) + 10]
    },
    yaxis: {
      title: "Temperature [C]",
      range: [ 15, 24 ]
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


function makenew_plot(plotly_id, plotly_data, plotly_layout) {
  Plotly.newPlot(plotly_id, plotly_data, plotly_layout);
  $('#' + plotly_id).addClass('updated');
}

function update_plot(plotly_id, plotly_data, plotly_layout_update) {
  Plotly.redraw(plotly_id, plotly_data)
  Plotly.relayout(plotly_id, plotly_layout_update);
}