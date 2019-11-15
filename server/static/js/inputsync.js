$(document).ready(function () {
  $('.input-row > input[type="range"]').on('input', function () {
    var new_id = $(this).attr('id').replace('-range', '-text');
    $('#' + new_id).val($(this).val());
  });

  $('.input-row >input[type="text"]').on('input', sync_range_to_text)

  $('input[id^="channel-"][id$="-range"]').on('input', function (event) {
    var myval = $(this).val();
    var out = $('#' + $(this).attr('id') + '-value')
    var html = ''
    switch (myval) {
      case '3': html = '100mV'; break;
      case '4': html = '200mV'; break;
      case '5': html = '500mV'; break;
      case '6': html = '1V'; break;
      case '7': html = '2V'; break;
      case '8': html = '5V'; break;
      case '9': html = '10V'; break;
      case '10': html = '20V'; break;
      default: html = 'N/A'
    }
    out.html(html);
  });

  $('input[id^="trigger-level"]').on('input', function () {
    var adc = $(this).val();
    var channel = $("input[name='trigger-channel']:checked").attr('id');
    var range_idx
      = (channel == "trigger-channel-A") ? $('#channel-a-range').val() :
        (channel == "trigger-channel-B") ? $('#channel-b-range').val() :
          '10';

    var max = 0;
    var unit = '';
    switch (range_idx) {
      case '3': max = 100; unit = 'mV'; break;
      case '4': max = 200; unit = 'mV'; break;
      case '5': max = 500; unit = 'mV'; break;
      case '6': max = 1; unit = 'V'; break;
      case '7': max = 2; unit = 'V'; break;
      case '8': max = 5; unit = 'V'; break;
      case '9': max = 10; unit = 'V'; break;
      case '10': max = 20; unit = 'V'; break;
      default: max = 0; break;
    }

    $('#trigger-level-converted').html(
      '(' + (max * adc / 128.0).toFixed(1) + unit + ')');
  });
});

function sync_range_to_text(event) {
  sync_range_to_text_by_id(event.target.id)
}

function sync_range_to_text_by_id(id) {
  var range_id = id.replace('-text', '-range');
  var max_val = parseFloat($(range_id).attr('max'));
  var min_val = parseFloat($(range_id).attr('min'));
  if ($(id).val() > max_val) {
    $(id).val(max_val);
  } else if ($(id).val() < min_val) {
    $(id).val(min_val);
  }
  $(range_id).val($(id).val());
}