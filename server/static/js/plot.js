var monitor_time = []
var monitor_temperature1 = []
var monitor_temperature2 = []
var monitor_voltage1 = []
var monitor_voltage2 = []




$(document).ready(function () {
  var socket = io.connect("http://localhost:9100");

  socket.on('connect', function (msg) {
    console.log('Connected!');
    var time_now = new Date()
    $()
  });

  socket.on('confirm', function (msg) {
    console.log('Confirmed!');
    $('#up-time-since').html (
      'Since:' + msg.start
    );
  });

  socket.on('monitor-update', function (msg) {

    $('#up-time').html(
      'Uptime:' + msg.time + '[sec]'
    )


    if (monitor_time.length >= 600) { // at most keeping 10minutes on display
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

    var temperature_data = [
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

    var temperature_layout = {
      xaxis: {
        title: "Time (since system start) [sec]",
        nticks: 10,
        range: [monitor_time[0], parseInt(monitor_time[0]) + 10]
      },
      yaxis: {
        title: "Temperature [C]",
        range: [
          Math.min(15, Math.min(Math.min(...monitor_temperature1),
            Math.min(...monitor_temperature2))),
          Math.max(25, Math.max(Math.max(...monitor_temperature1)+5,
            Math.max(...monitor_temperature2)+5))
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
    }

    var layout_update = {
      'xaxis.range': [
        monitor_time[0],
        Math.max(parseInt(monitor_time[0]) + 10,
          parseInt(monitor_time[monitor_time.length - 1]) + 0.1)
      ],
      'yaxis.range': [
        Math.min(15, Math.min(Math.min(...monitor_temperature1),
          Math.min(...monitor_temperature2))),
        Math.max(24, Math.max(Math.max(...monitor_temperature1)+4,
          Math.max(...monitor_temperature2)+4))
      ]
    };

    if ($('#temperature-plot').hasClass('updated')) {
      Plotly.redraw('temperature-plot', temperature_data)
      Plotly.relayout('temperature-plot', layout_update);
    } else {
      Plotly.newPlot('temperature-plot', temperature_data, temperature_layout);
      $('#temperature-plot').addClass('updated');
    }
  })
});