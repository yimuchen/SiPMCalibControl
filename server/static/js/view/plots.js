/**
 * Parsing the return from the server of a parse request.
 *
 * The return should be in the json format of
 *
 * ```
 * {
 *    'filename': 'file that is used to generate the data',
 *    'type': 'Type of plot used for the reduction of data',
 *    'update': A true/false flag indicating whether the target file is
 *              expecting more updates.
 *    'data': arbitrarily complicated function used for plotting all the
 *            information needed.
 * }
 * ```
 *
 * In case update is set to true, the function will wait for 100ms before
 * resubmitting a data request to the server. As no data caching will be handled
 * on the server, extensive resubmission will be very computationally expensive.
 */
async function parse_plot_data(data, div_id) {
  token = data.token;
  filename = data.filename;
  type = data.type;
  update = data.update;
  plotdata = data.data;

  if ($(`#${div_id}`).length == 0) {
    console.log(`DIV doesn't exist for plotting`);
    console.log(plotdata);
  } else {
    switch (type) {
      case 'xyz':
        plot_heat_map(div_id, plotdata);
        break;
      case 'hist':
        plot_histogram(div_id, plotdata);
        break;
      case 'zscan':
        plot_zscan(div_id, plotdata);
        break;
      case 'time':
        plot_tscan(div_id, plotdata);
      default:
        console.log('Unknown plot type', type);
    }
  }
  await sleep(200);
  console.log('Requesting plot update!', update);
  if (update) {
    // Rerunning the plot request
    request_plot_by_file(filename, type, div_id);
  }
}

/**
 * Plotting the output x-y-z data format.
 */
function plot_heat_map(div, data) {
  const plotly_data = [
    {
      x: data.x,
      y: data.y,
      z: data.z,
      type: 'contour',
      colorscale: 'RdBu',
    },
  ];

  const layout = {
    autosize: true,
    xaxis: {
      title: 'x position [mm]',
      autorange: true,
    },
    yaxis: {
      title: 'y position [mm]',
      autorange: true,
    },
    colorbar: {
      title: 'Readout [mV-ns]',
      titleside: 'right',
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {
      l: 60,
      r: 20,
      b: 40,
      t: 20,
      pad: 5,
    },
    title: false,
  };

  $(`#${div}`).css('height', '300px');
  $(`#${div}`).css('width', '400px');
  Plotly.newPlot(div, plotly_data, layout, layout_default_config);
}

/**
 * Plotting the output in histogram format.
 */
function plot_histogram(div, data) {
  var x = [];
  for (var i = 0; i < data.values.length; ++i) {
    x.push((data.edges[i] + data.edges[i + 1]) / 2.0);
  }

  const plotly_data = [
    {
      x: x,
      y: data.values,
      type: 'bar',
      mode: 'markers',
      name: `Mean: ${data.mean.toFixed(2)} RMS:${data.rms.toFixed(2)}`,
      marker: {
        color: 'rgb(41,55,199)',
      },
    },
  ];

  const layout = {
    autosize: true,
    xaxis: {
      title: 'Readout value [mV-ns]',
      autorange: true,
    },
    yaxis: {
      type: 'log',
      title: 'Events',
      autorange: true,
    },
    showlegend: true,
    legend: {
      x: 1,
      y: 1,
      xanchor: 'right',
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    bargap: 0, // For a continuous block histogram
    margin: {
      l: 60,
      r: 20,
      b: 40,
      t: 20,
      pad: 5,
    },
    title: false,
  };

  $(`#${div}`).css('height', '300px');
  $(`#${div}`).css('width', '400px');

  Plotly.newPlot(div, plotly_data, layout, layout_default_config);
}

function plot_zscan(div, data) {
  var plotly_data = [
    {
      x: data.z,
      y: data.v,
      error_y: {
        type: 'data',
        array: data.vu,
        visible: true,
      },
      marker: {
        size: 5,
        color: data.p,
        colorscale: 'Bluered',
        colorbar: {
          title: 'Bias [mV]',
        },
      },
      type: 'scatter',
      mode: 'markers',
      name: 'Readout value',
    },
  ];

  layout = {
    autosize: true,
    xaxis: {
      type: 'log',
      title: 'Gantry z [mm]',
      autorange: true,
    },
    yaxis: {
      type: 'log',
      title: 'Readout [mV-ns]',
      autorange: true,
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {
      l: 60,
      r: 20,
      b: 40,
      t: 20,
      pad: 5,
    },
    title: false,
  };

  $(`#${div}`).css('height', '300px');
  $(`#${div}`).css('width', '400px');
  Plotly.newPlot(div, plotly_data, layout, layout_default_config);
}

function plot_tscan(div, data) {
  console.log('plotting tscan', data);
}
