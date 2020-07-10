function sync_text_to_range_by_id(range_id) {
  const text_id = range_id.replace('-range', '-text');
  $(`#${text_id}`).val($(`#${range_id}`).val());
}

function sync_range_to_text_by_id(text_id) {
  var range_id = text_id.replace('-text', '-range');
  var max_val = parseFloat($(`#${range_id}`).attr('max'));
  var min_val = parseFloat($(`#${range_id}`).attr('min'));

  // Truncating the range.
  if ($(`#${text_id}`).val() > max_val) {
    $(`#${text_id}`).val(max_val);
  } else if ($(`#${text_id}`).val() < min_val) {
    $(`#${text_id}`).val(min_val);
  }

  $(`#${range_id}`).val($(`#${text_id}`).val());

}


function sync_text_to_range(event) {
  sync_text_to_range_by_id(event.target.id);
}

function sync_range_to_text(event) {
  sync_range_to_text_by_id(event.target.id);
}


function range_to_mv(range) {
  switch (range) {
    case '3': return 100;
    case '4': return 200;
    case '5': return 500;
    case '6': return 1000;
    case '7': return 2000;
    case '8': return 5000;
    case '9': return 10000;
    case '10': return 20000;
    default: return 0;
  }
}

function value_from_adc(adc, channel) {
  const range_idx
    = parseInt(channel) == 0 ? $('#channel-a-range').val() :
      parseInt(channel) == 1 ? $('#channel-b-range').val() :
        '10';
  return adc * range_to_mv(range_idx) / 32768.;
}

function adc_from_value(value, channel) {
  const range_idx
    = parseInt(channel) == 0 ? $('#channel-a-range').val() :
      parseInt(channel) == 1 ? $('#channel-b-range').val() :
        '10';
  return parseInt(value * 32768. / range_to_mv(range_idx));

}


function sync_pico_range() {
  const id_list = ['channel-a-range', 'channel-b-range'];

  for (var i = 0; i < 2; ++i) {
    var id = id_list[i];
    var myval = $(`#${id}`).val();
    var range_mv = range_to_mv(myval);
    var out = $(`#${id}-value`);
    var html = range_mv >= 1000 ? parseInt(range_mv / 1000) + 'V' :
      parseInt(range_mv) + 'mV';
    out.html(html);
  }
}




function sync_pico_trigger() {
  var adc = $('#trigger-level-text').val()
  var channel = $("input[name='trigger-channel']:checked").val();
  var level = value_from_adc(parseInt(adc), channel);
  var unit = 'mV'
  if (level > 1000) {
    unit = 'V';
    level /= 1000;
  } else if (level < -1000) {
    unit = 'V';
    level /= 1000;
  }

  $('#trigger-level-converted').html(
    '(' + level.toFixed(1) + unit + ')');
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
