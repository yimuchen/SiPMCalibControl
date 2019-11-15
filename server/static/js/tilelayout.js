chip_x_list = [120, 240]
chip_y_list = [120, 240]
chip_lumi_x_list = [122, 239]
chip_lumi_y_list = [126, 245]
chip_vis_x_list = [122.5, 239.5]
chip_vis_y_list = [125.5, 245.5]


$(document).ready(function () {
  var plot_data = [{
    x: chip_x_list,
    y: chip_y_list,
    type: 'scatter',
    mode: 'markers',
    name: 'In-built'
  }, {
    x: chip_lumi_x_list,
    y: chip_lumi_y_list,
    type: 'scatter',
    mode: 'markers',
    name: 'Lumi. pos.'
  }, {
    x: chip_vis_x_list,
    y: chip_vis_y_list,
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
  var hover_box = document.getElementById('hoverinfo');
  layout_plot.on('plotly_hover', function (data) {
    var chip_id = data.points[0].pointNumber;
    var infotext = 'Chip:' + chip_id + '<br/>'
      + 'Original   [' + chip_x_list[chip_id] + ','
      + chip_y_list[chip_id] + ']<br/>'
      + 'Luminosity [' + chip_lumi_x_list[chip_id] + ','
      + chip_lumi_y_list[chip_id] + ']<br/>'
      + 'Visual     [' + chip_vis_x_list[chip_id] + ','
      + chip_vis_y_list[chip_id] + ']<br/>';

    $('#tile-layout-chiphoverinfo').html(infotext);
  })
    .on('plotly_unhover', function (data) {
    $('#tile-layout-chiphoverinfo').html('');
    });

  layout_plot.on('plotly_click', function (data) {
    var id = data.points[0].pointNumber;
    var elem = '#chip' + id + '-detail';
    if( $(elem).length ){
      $(document).scrollTop($(elem).offset().top);
    }
  });


});