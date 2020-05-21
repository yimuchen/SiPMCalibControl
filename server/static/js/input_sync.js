function sync_text_to_range(event) {
  var range_id = event.target.id;
  var text_id = range_id.replace('-range', '-text');
  $('#' + text_id).val($('#' + range_id).val());
}

function sync_range_to_text(event) {
  var id = event.target.id;
  var range_id = id.replace('-text', '-range');
  var max_val = parseFloat($('#' + range_id).attr('max'));
  var min_val = parseFloat($('#' + range_id).attr('min'));
  if ($('#' + id).val() > max_val) {
    $('#' + id).val(max_val);
  } else if ($('#' + id).val() < min_val) {
    $('#' + id).val(min_val);
  }
  $('#' + range_id).val($('#' + id).val());
}

function sync_pico_range(event) {
  var id = event.target.id;
  var myval = $('#' + id).val();
  var out = $(`#${id}-value`)
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
}

function sync_pico_trigger(event) {
  var element = $(event.target);
  var adc = element.val();
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
}

function update_indicator() {
  $('.tab-content').each(function () {
    if ($(this).hasClass('hidden')) {
      $(this).removeClass('hidden');
      $(this).siblings('.tab-title').children('i').addClass('fa-angle-left');
      $(this).siblings('.tab-title').children('i').removeClass('fa-angle-down');
    } else {
      $(this).slideToggle('fast');
      $(this).siblings('.tab-title').children('i').removeClass('fa-angle-left');
      $(this).siblings('.tab-title').children('i').addClass('fa-angle-down');
    }
  });
}

function tab_click(element) {
  if (element.siblings('.tab-content').is(":hidden")) {
    element.children('i').removeClass('fa-angle-left');
    element.children('i').addClass('fa-angle-down');
  } else {
    element.children('i').removeClass('fa-angle-down');
    element.children('i').addClass('fa-angle-left');
  }
  element.siblings('.tab-content').slideToggle('fast');
}

function add_comment_line(element) {
  var det_select_html = `<select class="comment-header">
                         <option value="general">General</option>`
  for (var i = 0; i < det_id_list.length; ++i) {
    var det_id = det_id_list[i];
    det_select_html += `<option value="det${det_id}">Det ${det_id}</option>`
  }
  det_select_html += '</select>'

  var new_html = `<div class="input-row">
                <div class="input-name">${det_select_html}</div>
                <div class="input-units comment-content">
                  <input type="text" class="comment-text"></input>
                </div>
              </div>`

  element.siblings('.signoff-comment-lines').append(new_html);
}
