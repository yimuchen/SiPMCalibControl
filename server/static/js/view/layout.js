/**
 * For the chevron indicators used in the tab displays, ensure that the chevron
 * indicators match the current display state.
 */
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

/**
 * For ech of the tabs, this is the behavior to exhibit when the tab header is
 * clicked.
 */
function tab_click(element) {
  if (element.siblings('.tab-content').is(':hidden')) {
    element.children('i').removeClass('fa-angle-left');
    element.children('i').addClass('fa-angle-down');
  } else {
    element.children('i').removeClass('fa-angle-down');
    element.children('i').addClass('fa-angle-left');
  }
  element.siblings('.tab-content').slideToggle('fast');
}

/**
 * Given the hex-color code, lighten or darken the color by some fixed amount.
 *
 * Effectively, given RGB values (r,g,b) and shift amount a, return the hex code
 * for the color (r+a,g+a,b+a). The return values will be clipped at the nominal
 * 8-bit limit.
 */
function hex_lumi_shift(col, amt) {
  var usePound = false;
  if (col[0] == '#') {
    col = col.slice(1);
    usePound = true;
  }
  var num = parseInt(col, 16);
  var r = (num >> 16) + amt;
  if (r > 255) r = 255;
  else if (r < 0) r = 0;
  var b = ((num >> 8) & 0x00ff) + amt;
  if (b > 255) b = 255;
  else if (b < 0) b = 0;
  var g = (num & 0x0000ff) + amt;
  if (g > 255) g = 255;
  else if (g < 0) g = 0;
  return (usePound ? '#' : '') + (g | (b << 8) | (r << 16)).toString(16);
}

/**
 * Adding a comment line to the calibration sign-off segment.
 */
function add_comment_line(element) {
  var det_select_html = `<select class="comment-header">
                         <option value="general">General</option>`;

  for (const det_id in board_layout.detectors) {
    det_select_html += `<option value="det${det_id}">Det. ${det_id}</option>`;
  }
  det_select_html += '</select>';

  var new_html = `<div class="input-row">
                    <div class="input-name">${det_select_html}</div>
                    <div class="input-units comment-content">
                      <input type="text" class="comment-text"></input>
                    </div>
                  </div>`;
  console.log(element);
  element.siblings('.signoff-comment-lines').append(new_html);
}

/**
 * Drawing column elements of the tile board view
 */
function draw_tileboard_view_common() {
  let new_html = `<defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5"
                            markerWidth="6" markerHeight="6"
                            orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" />
                    </marker>
                  </defs>`;

  new_html += `<rect x="25" y="25"
                     width="500" height="500"
                     fill="none"
                     stroke-width="3px"
                     stroke="#303030"/>`;
  new_html += `<polyline points="12,475 12,537 75,537"
                         stroke-width="2px"
                         fill="none"
                         stroke="#303030"
                         marker-start="url(#arrow)"
                         marker-end="url(#arrow)"/>`;
  new_html += `<text x="85" y="541">x</text>`;
  new_html += `<text x="8" y="465">y</text>`;

  new_html += `<polyline
                 points="537,525 560,525 537,525
                         537,425 560,425 537,425
                         537,325 560,325 537,325
                         537,225 560,225 537,225
                         537,125 560,125 537,125
                         537,25  560,25  537,25"
                 stroke-width="3px"
                 stroke="#303030"
                 fill="none"/>`;

  $(`#tile-layout-common-svg`).html(new_html);
}

/**
 * Function related to the display of the action column
 */
action_column_width = 500;
function toggle_action_column() {
  if ($(`#action-column`).css('right').startsWith('-')) {
    //
    show_action_column();
  } else {
    hide_action_column();
  }
}

function show_action_column() {
  $('#action-column').css('width', `${action_column_width}px`);
  $('#action-column').css('right', '0px');
}

function hide_action_column() {
  $('#action-column').css('width', `${action_column_width}px`);
  $('#action-column').css('right', `-${action_column_width}px`);
}

/**
 * Functions related to the display of the monitor column
 */
monitor_column_width = 400;
function toggle_monitor_column() {
  if ($(`#monitor-column`).css('left').startsWith('-')) {
    show_monitor_column();
  } else {
    hide_monitor_column();
  }
}

function show_monitor_column() {
  $('#monitor-column').css('width', `${monitor_column_width}px`);
  $('#monitor-column').css('left', `0`);
  $('#session-column').css(
    'width',
    `${window.innerWidth - monitor_column_width}px`,
  );
  $('#session-column').css('margin-left', `${monitor_column_width}px`);
}

function hide_monitor_column() {
  $('#monitor-column').css('width', `${monitor_column_width}px`);
  $(`#monitor-column`).css('left', `-${monitor_column_width}px`);
  $('#session-column').css('margin-left', `0px`);
  $(`#session-column`).css('width', `${window.innerWidth}px`);
}
