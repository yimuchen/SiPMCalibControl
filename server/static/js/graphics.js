/**
 * Commonly used graphics data.
 */

function plot_data(id, data, layout) {
  if ($('#' + id).hasClass('updated')) {
    Plotly.redraw(id, data)
    // Should be stripped down version.... this can be expensive?
    Plotly.relayout(id, layout);
  } else {
    Plotly.newPlot(id, data, layout);
    $('#' + id).addClass('updated');
  }
}