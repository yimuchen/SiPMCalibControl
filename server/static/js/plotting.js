/**
 * plotting.js
 *
 * Functions for handling all plotting routines.
 *
 * Here we will be using jQuery ajax request to get the data required for
 * plotting, as this ensures the the plotting request is unique for the client
 * side and ensures that there will be no cross talk across the multiple
 * connected clients.
 *
 * Two high-level functions will be provided for the other javascript files to
 * use:
 * - request_plot_by_file: Generating a plot directly by the filename on the
 *   server side. Mainly used for debugging.
 * - request_plot: The standard plot requesting method by the process type and
 *   detector id.
 *
 * In both cases, the return payload is expected in the format of as json object
 * in the format:
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
 * The update flag is then used to recall the function to replot after the data
 * collection is updated.
 */

/**
 * Function for requesting plot data directly by filename.
 *
 * The following inputs is required:
 * - The filename used to extract plotting information.
 * - The plot-type to reduce the information.
 * - The element id to store the plot.
 *
 * The file name needs to be adjusted to replace the slashed with a unique
 * character not typically used for file naming while being URL safe (ex. using
 * @ for now).
 */
async function request_plot_by_file(filename, type, id) {
  ufile = filename.replaceAll('/', '@');

  $.ajax({
    dataType: 'json',
    mimeType: 'application/json',
    url: `databyfile/${type}/${ufile}`,
    success: async function (json) {
      if (!jQuery.isEmptyObject(json)) {
        parse_plot_data(json, id);
      } else {
        console.log(`no data available for ${filename}`);
      }
    },
    error: function () {
      console.log(`Failed to get data for filename:${filename}, type ${type}`);
    }
  });
}

async function request_plot_by_detid(detid, type, id) {
  $.ajax({
    dataType: 'json',
    mimeType: 'application/json',
    url: `data/${type}/${detid}`,
    success: async function (json) {
      if (!jQuery.isEmptyObject(json)) {
        parse_plot_data(json, id);
      } else {
        console.log(`no data available for ${detid}, ${type}`);
      }
    },
    error: function () {
      console.log(`Failed to get data for detector ID:${detid}, type ${type}`);
    }
  });
}

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
    console.log(`DIV doesn't exist for plotting`)
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
  await sleep(1000);
  if (update) { // Rerunning the plot request
    request_plot_by_file(filename, type, div_id);
  }
}

/**
 * Plotting the output x-y-z data format.
 */
function plot_heat_map(div, data) {
  const plotly_data = [{
    x: data.x,
    y: data.y,
    z: data.z,
    type: 'contour',
    colorscale: 'RdBu',
  }];

  const layout = {
    autosize: true,
    xaxis: {
      title: "x position [mm]",
      autorange: true
    },
    yaxis: {
      title: "y position [mm]",
      autorange: true
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
      pad: 5
    }, title: false
  };

  $(`#${div}`).css('height', '300px');
  $(`#${div}`).css('width', '400px');
  Plotly.newPlot(div,
    plotly_data,
    layout,
    layout_default_config);
}

/**
 * Plotting the output in histogram format.
 */
function plot_histogram(div, data) {
  var x = [];
  for (var i = 0; i < data.values.length; ++i) {
    x.push((data.edges[i] + data.edges[i + 1]) / 2.0);
  }

  const plotly_data = [{
    x: x,
    y: data.values,
    type: 'bar',
    mode: 'markers',
    name: `Mean: ${data.mean.toFixed(2)} RMS:${data.rms.toFixed(2)}`,
    marker: {
      color: 'rgb(41,55,199)',
    }
  }];

  const layout = {
    autosize: true,
    xaxis: {
      title: "Readout value [mV-ns]",
      autorange: true
    },
    yaxis: {
      type: 'log',
      title: "Events",
      autorange: true
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
      pad: 5
    }, title: false
  }

  $(`#${div}`).css('height', '300px');
  $(`#${div}`).css('width', '400px');

  Plotly.newPlot(div,
    plotly_data,
    layout,
    layout_default_config);
}

function plot_zscan(div, data) {
  var plotly_data = [{
    x: data.z,
    y: data.v,
    error_y: {
      type: 'data',
      array: data.vu,
      visible: true
    },
    marker: {
      size: 5,
      color: data.p,
      colorscale: 'Bluered',
      colorbar: {
        title: "Bias [mV]"
      }
    },
    type: 'scatter',
    mode: 'markers',
    name: 'Readout value'
  }];

  layout = {
    autosize: true,
    xaxis: {
      type: 'log',
      title: "Gantry z [mm]",
      autorange: true
    },
    yaxis: {
      type: 'log',
      title: "Readout [mV-ns]",
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
    },
    title: false
  };

  $(`#${div}`).css('height', '300px');
  $(`#${div}`).css('width', '400px');
  Plotly.newPlot(div,
    plotly_data,
    layout,
    layout_default_config);
}

function plot_tscan(div, data) {
  console.log('plotting tscan', data);
}