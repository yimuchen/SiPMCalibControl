/**
 * Updating the uptime display container:
 */
function status_update_time() {
  const time = parseInt(session.monitor.time[session.monitor.time.length - 1]);
  const time_hour = parseInt(time / 3600)
    .toString()
    .padStart(2, 0);
  const time_min = parseInt((time / 60) % 60)
    .toString()
    .padStart(2, 0);
  const time_sec = parseInt(time % 60)
    .toString()
    .padStart(2, 0);
  const state_str =
    session.state == STATE_IDLE
      ? `IDLE`
      : session.state == STATE_EXEC_CMD
      ? `EXECUTING COMMAND`
      : session.state == STATE_RUN_PROCESS
      ? `PROCESSING`
      : session.state == STATE_WAIT_USER
      ? `WAITING UESR ACTION`
      : ``;
  $(`#up-time`).html(`Uptime: ${time_hour}:${time_min}:${time_sec}`);
  $('#up-time-since').html(
    `Session is: ${state_str} </br>
     Since: ${session.monitor.start}`
  );
}

/**
 * Plotting the the monitoring data. Styling information is placed at the bottom
 * of the file to reduce verbosity.
 */
function status_update_monitor_data() {
  // at most keeping 10 minutes on display
  if (session.monitor.time.length >= 600) {
    session.monitor.time.shift();
    session.monitor.temperature1.shift();
    session.monitor.temperature2.shift();
    session.monitor.voltage1.shift();
    session.monitor.voltage2.shift();
  }

  temperature_data = [
    {
      x: session.monitor.time,
      y: session.monitor.temperature1,
      type: 'scatter',
      name: 'Pulser',
    },
    {
      x: session.monitor.time,
      y: session.monitor.temperature2,
      type: 'scatter',
      name: 'Tileboard',
    },
  ];

  voltage_data = [
    {
      x: session.monitor.time,
      y: session.monitor.voltage1,
      type: 'scatter',
      name: 'Pulser board Bias',
    },
    {
      x: session.monitor.time,
      y: session.monitor.voltage2,
      type: 'scatter',
      name: 'Secondary',
    },
  ];

  if ($(`#temperature-plot`).length != 0) {
    Plotly.newPlot(
      'temperature-plot',
      temperature_data,
      temperature_plot_layout(),
      layout_default_config
    );
  } else {
    console.log('temperature-plot DIV does not exist!');
  }

  if ($('#voltage-plot').length != 0) {
    Plotly.newPlot(
      'voltage-plot',
      voltage_data,
      voltage_plot_layout(),
      layout_default_config
    );
  } else {
    console.log('voltage-plot DIV does nto exist!');
  }
}

/**
 * Temperature plot requires dynamic settings for custom range.
 */
function temperature_plot_layout() {
  return {
    autosize: true,
    xaxis: {
      title: 'Time (since system start) [sec]',
      nticks: 10,
      range: [
        session.monitor.time[0],
        Math.max(
          parseInt(session.monitor.time[0]) + 10,
          parseInt(session.monitor.time[session.monitor.time.length - 1]) + 0.1
        ),
      ],
    },
    yaxis: {
      title: 'Temperature [°C]',
      range: [
        Math.min(
          15,
          Math.min(...session.monitor.temperature1),
          Math.min(...session.monitor.temperature2)
        ),
        Math.max(
          24,
          Math.max(...session.monitor.temperature1) + 4,
          Math.max(...session.monitor.temperature2) + 4
        ),
      ],
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {
      l: '40',
      r: '5',
      b: '40',
      t: '10',
      pad: 0,
    },
    legend: {
      x: 0.5,
      y: 0.9,
    },
  };
}

/**
 * Voltage plot requires a custom range
 */
function voltage_plot_layout() {
  return {
    autosize: true,
    xaxis: {
      title: 'Time (since system start) [sec]',
      nticks: 10,
      range: [
        session.monitor.time[0],
        Math.max(
          parseInt(session.monitor.time[0]) + 10,
          parseInt(session.monitor.time[session.monitor.time.length - 1]) + 0.1
        ),
      ],
    },
    yaxis: {
      title: 'Voltage [mV]',
      range: [0, 5000],
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {
      l: '60',
      r: '5',
      b: '40',
      t: '10',
      pad: 0,
    },
    legend: {
      x: 0.5,
      y: 0.9,
    },
  };
}

const layout_default_config = {
  displayModeBar: false,
  responsive: true,
};

/**
 * Two parts needs to be updated regarding the values. One is a text based
 * display of the coordinates values in the monitor tab. The other is the
 * graphical elements in the tile-board view.
 */
function status_update_coordinates() {
  const x = session.monitor.gantry_position[0];
  const y = session.monitor.gantry_position[1];
  const z = session.monitor.gantry_position[2];
  $(`#gantry-coordinates`).html(
    `Gantry coordinates: (${x.toFixed(1)}, ${y.toFixed(1)}, ${z.toFixed(1)})`
  );

  $('#tile-layout-gantry-svg').html('');
  $('#tile-layout-gantry-svg').append(
    dom('polyline', {
      points: `${x + 20},${510 - y} ${x + 25},${525 - y}  ${x + 30},${510 - y}`,
      stroke: 'red',
      fill: 'red',
      'stroke-width': '1px',
    })
  );
  $('#tile-layout-gantry-svg').append(
    dom('polyline', {
      points: `548,${520 - z} 538,${525 - z} 548,${530 - z}`,
      stroke: 'red',
      fill: 'red',
      'stroke-width': '1px',
    })
  );
}

/**
 * Function to be called when a new session connection is established. Clearing
 * out all cached monitor data.
 */
function clear_status_data() {
  session.monitor.start = '';
  session.monitor.time = [];
  session.monitor.temperature1 = [];
  session.monitor.temperature2 = [];
  session.monitor.voltage1 = [];
  session.monitor.voltage2 = [];
  session.monitor.gantry_position = [0, 0, 0];
}
