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
  var socket
    = io.connect('http://' + window.location.hostname + ':9100/monitor');

  // List of all socket update functions
  socket.on('connect', function (msg) { console.log('Connected to monitor socket!'); });
  socket.on('confirm', connect_update);
  socket.on('monitor-update', monitor_update);
  socket.on('visual-settings-update', visual_settings_update);
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
      y: monitor_temperature1,
      type: 'scatter',
      name: 'Pulser pull-up'
    },
    {
      x: monitor_time,
      y: monitor_temperature2,
      type: 'scatter',
      name: 'PD Bias'
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
      title: "Measured Voltage [V]",
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