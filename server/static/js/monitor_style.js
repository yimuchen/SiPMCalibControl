/**
 * This contains the majority of the styling that is used in the monitor part,
 * outside of the raw computation routines.
 */


/********************************************************************************
* Plot layout for temperature monitoring plots
* Must be dynamic since the x,y range is custom.
*******************************************************************************/
function Layout_Temperature_Plot() {
  /**
   * The temperature plot styling. The client is used to calculate the custom
   * range instead of the defaults provided in the plotly library.
   */
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

/********************************************************************************
 * Plot layout for voltage monitoring plots
 * Must be dynamic since the x,y range is custom.
 *******************************************************************************/
function Layout_Voltage_Plot() {
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

/********************************************************************************
 * Intensity scan plot data.
 *******************************************************************************/
const layout_intensityscan_plot = {
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

}

function Layout_IntensityScan_Plot() {
  return layout_intensityscan_plot;
}

/********************************************************************************
 * Plot layout for low-light plots
 *******************************************************************************/
const layout_lowlight_plot = {
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

function Layout_LowLight_Plot() {
  return layout_lowlight_plot;
}

/********************************************************************************
 * Common configurations for plotting
 *******************************************************************************/
const layout_default_config = {
  'displayModeBar': false,
  'responsive': true
}

function Layout_Default_Config() { return layout_default_config; }


/********************************************************************************
 * Status parsing
 *******************************************************************************/
function Status_String(integer) {
  switch (integer) {
    case (0): return 'Complete';
    case (1): return 'Pending';
    case (2): return 'Running';
    default: return 'Error';
  };
}

function Status_Color(integer) {
  switch (integer) {
    case (0): return '#00FF00';
    case (1): return 'none';
    case (2): return 'yellow';
    default: return 'red';
  }
}

/********************************************************************************
 * Process tag to full name conversion
 *******************************************************************************/
function ProcessFullname(tag) {
  switch (tag) {
    case 'vis_align': return 'Visual alignment';
    case 'zscan'    : return 'Intensity scan';
    case 'lowlight' : return 'Low light profile';
    default: return 'Custom';
  }
}

/********************************************************************************
 * Color modification colors
 *******************************************************************************/
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
