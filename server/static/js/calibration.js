/**
 * The main function of the calibration monitoring routine.
 *
 * The function first request the tileboard layout and the expected progress
 * using a AJAX. This is used to generated the HTML elements that make up the
 * monitoring page. The the function initiates a timed loop for monitoring. The
 * ending criteria for the loop that the session.state variables returns
 * to ideal. At which point the update function is called again to ensure all
 * data is collected and the function exits.
 */
var board_layout = {} // Global object for board layout
var progress = {} // Global object for progress.

// constant flags for the return status of a code
const CMD_PENDING = 1
const CMD_RUNNING = 2
const CMD_COMPLETE = 0
const CMD_ERROR = -1

const calibration_update_interval = 1000; // Update interval in milliseconds

// Processes flag that can be
const plot_processes = ['zscan', 'lowlight', 'lumialign'];
const can_rerun_process = ['zscan', 'lowlight'];
const can_extend_process = ['zscan', 'lowlight'];

/**
 * The main sequence for starting the calibration display. First the tileboard
 * layout and the expected processes are requested from the server. Then the HTML
 * elements used for monitoring the processes is generated. Finally, a loop
 * begins to monitor the updated progress until the calibration session returns
 * to an idle state.
 */
function load_tileboard_and_update() {
  ajax_update_board_layout(); // Moving ajax call to recursion to retry if failed
  ajax_update_progress(); // Updating the progress
  // For the first pass, let make the progress be completely pending to make sure
  // that any process is update.
  for (const tag in progress) {
    // This is used exclusively for the the progress of the current command.
    if (tag == "current") { continue; }
    for (const detid in progress[tag]) {
      progress[tag][detid] = CMD_PENDING;
    }
  }

  // Function relative to making the HTML DOM elements for calibration monitoring
  // display. This should only be called once.
  make_calibration_monitor_html();
  console.log(`Completed making HTML elements`);


  // The main looping function. This function will call itself until the board
  // session returns to an idle state.
  monitor_progress();

  // On completion run a second time just to make sure all data is flushed to
  // client side.
  for (const tag in progress) {
    // This is used exclusively for the the progress of the current command.
    if (tag == "current") { continue; }
    for (const detid in progress[tag]) {
      progress[tag][detid] = CMD_PENDING;
    }
  }

  monitor_progress();
}

/**
 * Ajax function for getting the tileboard layout. Notice that even if there is
 * no tileboard in the current session, the ajax request should still succeed and
 * initialize the board layout to a near empty map.
 */
function ajax_update_board_layout() {
  $.ajax({
    async: false,
    // Forcing to be asynchronous because future routines relies on this to be
    // completed.
    dataType: 'json',
    mimeType: 'application/json',
    url: `report/tileboard_layout`,
    success: function (json) {
      board_layout = json;
    },
    error: function () {
      console.log('Failed to get board layout');
    }
  });
}

/**
 * Ajax function for getting the expected process container. Notice that even if
 * no calibration process in running, the ajax request should still succeed and
 * initialize the progress variable with a empty map.
 */
function ajax_update_progress() {
  $.ajax({
    async: false,
    // Forcing to be asynchronous because future routines relies on this to be
    // completed.
    dataType: 'json',
    mimeType: 'application/json',
    url: `report/progress`,
    success: function (json) {
      progress = json;
    },
    error: function () {
      console.log('Failed to get board layout');
    }
  });
}

/**
 * This is largely split into 2 parts:
 * 1. The SVG section for displaying the tile layout.
 * 2. A table containing all the processes of a the calibration session.
 * 2. the Tabular part displaying the per-detector information and plots.
 *
 * Because new elements can be added on by request, we are leaving this function
 * as a list of other function.
 */
function make_calibration_monitor_html() {
  make_tileboard_html();
  make_table_html();
  make_detector_summary_html();
}

/**
 * Function for making the HTML components required for a tileboard display.
 *
 * Here there are two methods of display:
 * - If a geometry/tileboard.json file exists, the display generating function
 *   the board will be displayed as a true arc segments, fully displaying the
 *   expected tileboard geometry, as defined in the HGCAL documents.
 * - If such a file doesn't exists, then the displays assumes a calibration level
 *   board layout. Detectors elements will be discontinuous blocks in the SVG
 *   canvas.
 *
 * The stark contrast aims to force the user to become aware of the tile identity
 * differences.
 */
function make_tileboard_html() {
  $.ajax({
    async: false,
    // Forcing to be asynchronous because future routines relies on this to be
    // completed.
    dataType: 'json',
    mimeType: 'application/json',
    url: `geometry/${board_layout.boardtype}`,
    success: make_tileboard_segment_html,
    error: make_tileboard_default_html
  })
}

// couple of constant variables to help with the conversion of the data scaling
const canvas_target = 500;
const corner_offset = 25;

/**
 * By default, the display of the SVG will plot out the detector elements using
 * rectangular blocks. The rectangular blocks can be clicked to bring up the
 * per-detector summary information.
 */
function make_tileboard_default_html() {
  const x_max = 500;
  const scale = canvas_target / x_max;

  let shape_html = ``;
  let text_html = ``
  if (Object.keys(board_layout.detectors).length > 0) {
    for (var detid in board_layout.detectors) {
      const x_raw = board_layout.detectors[detid]['orig'][0];
      const y_raw = board_layout.detectors[detid]['orig'][1];

      const x = x_raw * scale + corner_offset;
      const y = x_max - y_raw * scale + corner_offset;
      // Needs to reverse the y axis scale for conversion
      shape_html += `<rect
                    x="${x - 20}" y="${y - 20}" width="40" height="40"
                    id="tile-layout-${detid}"
                    onclick="show_det_summary(${detid})"
                    />` ;
      text_html += `<text x="${x}" y="${y}"
                   text-anchor="middle"
                   onclick="show_det_summary(${detid})"
                  >${detid}</text>`
    }
  } else {
    text_html = `<text x="275" y="275"
                       text-anchor="middle">
                   NO TILEBOARD LOADED
                 </text>`
  }

  $(`#tile-layout-svg`).html(`${shape_html} ${text_html}`);
}


/**
 * Generating the SVG path string required for a regular tile board segment.
 *
 * Both tileboards and the SiPM selection (a.k.a the shape of typical
 * scintillating tiles)  are composed to two concentric circular arcs spanning a
 * common angle. This function generates the path required for this display. All
 * styling would be handle by CSS and other functions.
 *
 * Here r1 and r2 are in units of pixels. While t1 and t2 are in units of degrees
 * (since the HGCAL is segmented into args of exactly 10 degrees). ox, and oy
 * refers to the where the center of the circles used for the concentric arcs
 * should be placed in pixel coordinates.
 *
 * Here we need to handle the reversal of the y coordinates. The use is the one
 * responsible for ensuring the offsets are handles properly.
 */
function make_regular_segment(r1, r2, t1, t2, ox, oy) {
  t2 = -(t1 + t2) * Math.PI / 180;
  t1 = -t1 * Math.PI / 180;
  let x1 = ox + r1 * Math.cos(t1);
  let y1 = oy + r1 * Math.sin(t1);
  let x2 = ox + r1 * Math.cos(t2);
  let y2 = oy + r1 * Math.sin(t2);
  let x3 = ox + r2 * Math.cos(t2);
  let y3 = oy + r2 * Math.sin(t2);
  let x4 = ox + r2 * Math.cos(t1);
  let y4 = oy + r2 * Math.sin(t1);

  let path_str = `M ${x1} ${y1} a ${r1},${r1} 0 0,0 ${x2 - x1},${y2 - y1} `;
  path_str += `L ${x3} ${y3} a ${r2},${r2} 0 0,1 ${x4 - x3},${y4 - y3} `;
  path_str += `z`;
  return path_str;
}

/**
 * Generating the SVG/HTML tags for the segment display of a tile board. Since
 * there the objects themselves will not be handled.
 */
function make_tileboard_segment_html(tileboard_json) {
  // Getting the maximum and minimum radius for plotting offset requirements.
  const angle = tileboard_json.angle;
  const deg = Math.PI / 180.0;

  let min = 100000;
  let max = 0;
  for (const detid in tileboard_json.dets) {
    min = Math.min(tileboard_json.dets[detid][1], min);
    max = Math.max(tileboard_json.dets[detid][2], max);
  }

  let new_html = ``;

  // Setting up the scaling factor such that it uses the most of the canvas
  // area, Setting up the offset such that the center matches that of the
  // object is centered on the canvas
  const scale = 1.0;
  const offset_x = max * Math.sin(4 * angle * deg) * scale + corner_offset;
  const offset_y = min * Math.cos(4 * angle * deg) * scale + canvas_target
    + corner_offset;

  // Main loop for plotting all the objects.
  for (detid in tileboard_json.dets) {
    // Getting the various parameters
    const det = tileboard_json.dets[detid];
    const column = det[0]
    const inner = det[1]
    const outer = det[2]
    const det_roffset = det.length >= 4 ? det[3] : 0;
    const det_aoffset = det.length >= 5 ? det[4] : 0;

    // Getting hte plot variables.
    const t1 = 90 + (8 - column - 5) * angle;
    const path_str = make_regular_segment(
      outer * scale, inner * scale, // The radii information,
      t1, angle,
      offset_x, offset_y);
    new_html += `<path
                  id="tile-layout-${detid}"
                  d="${path_str}"
                  onclick="show_det_summary(${detid})"
                  class=""/>\n`

    // Adding text labeling to help with clarity
    const r_det = (inner + outer) / 2 + det_roffset
    const a_det = -(t1 + angle / 2 + det_aoffset);

    const x = r_det * scale * Math.cos(a_det * deg) + offset_x;
    const y = r_det * scale * Math.sin(a_det * deg) + offset_y;

    new_html += `<text x="${x}" y="${y}" text-anchor="middle">${detid}</text>`
  }

  $(`#tile-layout-svg`).html(new_html);
}

/**
 * Making a table that sums shows all the various calibration steps.
 */
function make_table_html() {
  let new_html = ``

  // For the for headers
  new_html = `<tr> <th></th>`
  for (const tag in progress) {
    if (tag == `current`) { continue; }
    new_html += `<th><span>${process_full_name(tag)}</span></th>`
  }
  new_html += `</tr>`;

  // For the grand process
  for (const detid in board_layout.detectors) {
    let row_html = `<td c>${detid}</td>`
    for (const tag in progress) {
      if (tag == `current`) { continue; }
      row_html += `<td id="table-${detid}-${tag}"></td>`;
    }
    new_html += `<tr onclick=show_det_summary(${detid})>${row_html}</tr>`;
  }

  $('#table-view').html(`<table>${new_html}</table>`);
}


/**
 * The detector summary is make of two parts. One is the brief summary of
 * coordinates and calibration action progresses. The other is the container of
 * plots. Since the plot container takes up a lot more space than the expected
 * values. Two functions are used to generated the various html elements.
 *
 * Notice at this stage, there will be no parsing of data just yet. This is left
 * to another function.
 */

function make_detector_summary_html() {
  let coordinate_html = ``;
  let plot_html = ``;
  for (var detid in board_layout.detectors) {
    coordinate_html += make_detector_coordinate_html(detid);
    plot_html += make_detector_plot_html(detid);
  }

  $('#single-det-summary').html(coordinate_html);
  $('#det-plot-and-figure').html(plot_html);
}

/**
 * Making the text-based coordinate summary part of the detector summary display.
 *
 * Here we are only making the base HTML with no data progress parsing. The only
 * apparent parsing would be for the various processes where re-run/extension
 * button will need to be added.
 */
function make_detector_coordinate_html(detid) {
  const coord = `<div class="input-row">
                    <span class="input-name">Det ID:</span>
                    <span class="input-units"> ${detid} </span>
                  </div>
                  <div class="input-row">
                    <span class="input-name">Coordinates:</span>
                    <span class="input-units" id="coord-orig"></span>
                  </div>
                  <div class="input-row">
                    <span class="input-name">Lumi. coord:</span>
                    <span class="input-units" id="coord-lumi"></span>
                    <span class="input-units">
                      <button id="rerun-lumi-scan-${detid}"
                            class="action-button",
                            onclick="rerun_single('lumialign','${detid}',false)"
                            disabled>
                      Rerun</button>
                    </span>
                  </div>
                  <div class="input-row">
                    <span class="input-name">Vis. coord:</span>
                    <span class="input-units" id="coord-vis"></span>
                    <span class="input-units">
                      <button class="action-button"
                              id="rerun-vis-scan-${detid}"
                              onclick="rerun_single('visalign','${detid}',false)"
                              disabled>
                              Rerun</button>
                      </span>
                   </div>`;

  let prog_html = ``;
  for (const tag in progress) {
    if (tag == 'current') { continue; }
    if (!(String(detid) in progress[tag])) { continue; }

    prog_html += `<div class="input-row">
                    <span class="input-name" id="process-${tag}"></span >
                    <span class="input-units">${process_full_name(tag)}</span>
                    ${check_rerun_button(detid, tag)}
                    ${check_extend_button(detid, tag)}
                  </div>`
  }

  return `<div id="single-det-summary-${detid}" class="hidden">
            <div class="input-align">
              ${coord} ${prog_html}
            </div>
          </div>`;

}

/**
 * Given a process tag, check if the process can be re-run. If it can create the
 * HTML code for the rerun action button. Otherwise return an empty string.
 */
function check_rerun_button(detid, tag) {
  if (can_rerun_process.includes(tag)) {
    return `<span class="input-units">
              <button id="rerun-${tag}-${detid}"
                      class="action-button"
                      onclick="rerun_single('${tag}','${detid}',false)"
                      disabled>
              Rerun</button>
            </span>`
  }
  else {
    return ``;
  }
}

/**
 * Given a process tag, check if the process can be extended. If it can create
 * the HTML code for the rerun action button. Otherwise return an empty string.
 */
function check_extend_button(detid, tag) {
  if (can_extend_process.includes(tag)) {
    return `<span class="input-units">
              <button id="rerun-${tag}-${detid}"
                      class="action-button"
                      onclick="rerun_single('${tag}','${detid}',true)"
                      disabled>
              Extend </button>
            </span>`
  } else {
    return ``;
  }
}

/**
 * Translation of the abbreviated process tag into a fully human readable string.
 */
function process_full_name(tag) {
  switch (tag) {
    case 'vhscan': return 'Visual Matrix';
    case 'visalign': return 'Visual alignment';
    case 'zscan': return 'Intensity scan';
    case 'lowlight': return 'Low light profile';
    case 'lumialign': return 'Luminosity alignment';
    default: return 'Custom';
  }
}


/**
 * Making the dummy detector HTML plot DOM objects
 */
function make_detector_plot_html(detid) {
  let plot_html = ``
  for (const tag in progress) {
    if (tag == 'current') { continue; }
    if (!plot_processes.includes(tag)) { continue; }
    plot_html += `<div class="plot"
                       id="single-det-summary-plot-${detid}-${tag}">
                  </div>`;
  }

  return `<div class="hidden" id="det-plot-container-${detid}">
            <div class="plot-container">
              ${plot_html}
              <div class="plot" id="single-det-summary-plot-${detid}-visalign">
                <img src="static/icon/notdone.jpg"/>
              </div>
            </div>
          </div>`
}

/** ========================================================================== */
/** MAIN MONITOR LOOP AND FUNCTIONS */
/** ========================================================================== */


/**
 * The main looping monitoring process. This function will call itself after.
 * This is monitored by looking at requesting a new version of the progress part.
 * An will only update what is new via additional ajax queries.
 */
function monitor_progress() {
  update_tileboard_coordinates();
  update_progress();

  if (session_state != STATE_IDLE) {
    setTimeout(monitor_progress, calibration_update_interval);
  }
  // Upon existing the state tile. Force run on-more time to avoid any data
  // losses
}

/**
 * Updating the tileboard detector coordinates. Since this is expected to be
 * small, we are not going to write a new sub-routine to get only the updated
 * detector coordinates, we are just going to pull the entire tileboard and
 * update everything.
 */
function update_tileboard_coordinates() {
  // Helper functions for generating coordinates in a uniform format.
  // Updating tileboard coordinates.

  function make_coordinate_string(detid, tag) {
    if (board_layout.detectors[detid][tag][0] < 0) {
      return 'NOT DONE';
    } else {
      const x = board_layout.detectors[detid][tag][0].toFixed(1);
      const y = board_layout.detectors[detid][tag][1].toFixed(1);
      return `(${x},${y})`;
    }
  }

  // Getting a new form of the ajax coordinates.
  ajax_update_board_layout();

  for (var detid in board_layout.detectors) {
    var cont = $(`#single-det-summary-${detid}`);
    cont.find('#coord-orig').html(make_coordinate_string(detid, 'orig'));
    cont.find('#coord-lumi').html(make_coordinate_string(detid, 'lumi'));
    cont.find('#coord-vis').html(make_coordinate_string(detid, 'vis'));
  }
}

/**
 * Getting a new version of the progress container. We will then compare the old
 * and the new to find which plot elements need to be updated. There are various
 * objects that needs to be updated, which is split out into various helper
 * functions.
 *
 * 1/2. The overall progress bar and the progress indicator for each detector
 *    element.
 * 3. Update the visual image URL if it already complete.
 * 4. A comparison of the old and new progress. Such that the new data can be
 *    requested from the main session to be replotted.
 *
 * Since the main comes from the display of data and passing around data. We are
 * going to have a for loop for each of the sub routines.
 */
function update_progress() {
  const old_progress = progress; // Making an copy of the old progress

  // Running the ajax command to update the progress object.
  ajax_update_progress();

  update_progress_bar();
  update_table();
  update_detector_progress();
  update_visual_image();
  update_data(old_progress);
}

/**
 * Updating the overall progress bar.
 *
 * There are two bars in the calculation part. One is for the overall progress.
 * One is for the current running command progress.
 */
function update_progress_bar() {
  let total = 0;
  let error = 0;
  let running = 0;
  let complete = 0;
  let pending = 0;

  // Calculating the overall percentage
  for (const tag in progress) {
    // This is used exclusively for the the progress of the current command.
    if (tag == "current") { continue; }
    for (const detid in progress[tag]) {
      total++;
      if (progress[tag][detid] == CMD_PENDING) { pending++; }
      else if (progress[tag][detid] == CMD_RUNNING) { running++; }
      else if (progress[tag][detid] == CMD_COMPLETE) { complete++; }
      else { error++; }
    }
  }

  // Updating the overall session progress progress bar.
  const complete_percent = 100.0 * complete / total;
  const error_percent = 100.0 * error / total;
  const running_percent = 100 * running / total;

  var bar_elem = $('#session-progress');
  bar_elem.children('.progress-complete').css('width', `${complete_percent}%`);
  bar_elem.children('.progress-running').css('width', `${running_percent}%`);
  bar_elem.children('.progress-error').css('width', `${error_percent}%`);

  // Making the command progress bar. In the case that commands have not progress
  // monitoring (visual alignment/sharpness maximization), then the progress is
  // simply fixed at 100%.
  if ('current' in progress) {
    const command_total = progress['current'][1];
    const command_completed = progress['current'][0];
    const percent = 100.0 * command_completed / command_total;

    $('#command-progress')
      .children('.progress-complete').css('width', `${percent}%`);
  } else {
    console.log(`Command command currently running!`);
    $('#command-progress')
      .children('.progress-complete').css('width', '100%');
  }
}

function update_table() {
  for (const tag in progress) {
    if (tag == 'current') { continue; }
    for (const detid in progress[tag]) {
      const progress_code = progress[tag][detid];
      $(`#table-${detid}-${tag}`).css(
        'background-color', progress_color(progress_code))
    }
  }
}


/**
 * Updating the per detector progress elements.
 *
 * There are two classes of elements that need to be updated: in the text based
 * summary, change the color of the text such that the user can see the
 * completed/error/ongoing calibration process, and an update to the background
 * of the tileboard layout so that the user can see whether where on the board
 * errors has occurred.
 */
function update_detector_progress() {
  // Variables that contains a map of
  let det_job_progress = {}
  let running_detid = 65536; // Some impossible id number.

  // Calculating the summary percentage.
  for (const tag in progress) {
    if (tag === "current") { continue; }
    for (const detid in progress[tag]) {
      const progress_code = progress[tag][detid];

      // Creating tally entry if it doesn't already exists.
      if (!(detid in det_job_progress)) {
        det_job_progress[detid] = [0, 0];
      }

      // Updating the status detector tally
      ++det_job_progress[detid][0]
      if (progress_code == CMD_RUNNING) { running_detid = detid; }
      else if (progress_code == CMD_COMPLETE) { ++det_job_progress[detid][1]; }

      // Updating the text based detector information.
      var element = $('#single-det-summary-' + detid).find('#process-' + tag);
      element.css('background-color', progress_color(progress_code));
      element.html(progress_status_string(progress_code));
    }
  }

  for (var detid in board_layout.detectors) {
    if (String(detid) == String(running_detid)) {
      $(`#tile-layout-${detid}`).css('fill', 'yellow');
    } else if (detid in det_job_progress) {
      const total = det_job_progress[detid][0];
      const comp = det_job_progress[detid][1];
      const base_color = `#00FF00`;
      const lighten = 200.0 * (total - comp) / total;
      $(`#tile-layout-${detid}`).css('fill',
        hex_lumi_shift(base_color, lighten));
    }
  }

}

/**
 * Returning a progress status code into a full string used for display.
 */
function progress_status_string(integer) {
  switch (integer) {
    case (CMD_COMPLETE): return 'Complete';
    case (CMD_PENDING): return 'Pending';
    case (CMD_RUNNING): return 'Running';
    default: return 'Error';
  };
}

/**
 * Returning the progress status code as a color
 */
function progress_color(integer) {
  switch (integer) {
    case (CMD_COMPLETE): return 'green';
    case (CMD_PENDING): return 'cyan';
    case (CMD_RUNNING): return 'yellow';
    default: return 'red';
  }
}

/**
 * Since python servers doesn't like to be queried multiple image files within
 * the same time frame, we are going to artificially stagger the process of
 * updating the image urls.
 */
function update_visual_image() {
  if ('visalign' in progress) {
    for (const detid in progress['visalign']) {
      const notfound = $(`#single-det-summary-plot-${detid}-visalign`)
        .children(`img`)[0]
        .getAttribute('src')
        .endsWith('notdone.jpg');
      if (notfound && progress['visalign'][detid] != CMD_PENDING) {
        // Updating
        $(`#single-det-summary-plot-${detid}-visalign`).html(
          `<img src="static/temporary/visual_${detid}.jpg"/>`);
      }
    }
  }
}

/**
 * Given an old progress selection, this compares if there are any difference
 * between this and the current progress and updates the parts where the data has
 * been updated since last time.
 */
function update_data(old_progress) {
  for (const tag in old_progress) {
    if (tag == `current`) { continue; }
    for (const detid in old_progress[tag]) {
      // For processes that are running, update regardless.
      if (progress[tag][detid] == CMD_RUNNING) {
        update_detector_data(detid, tag);
      } else if (progress[tag][detid] != old_progress[tag][detid]) {
        update_detector_data(detid, tag);
      }
    }
  }
}

/**
 * Showing the detector summary is composed of two parts:
 * 1. Pulling the text based summary via CSS manipulation. Since text-based
 *    information is small. One can afford to keep a copy of this on date
 * 2. Plots for each detector is then generated on the fly, this reduces the
 *    amount of time needed to have massive data updates. (in particular the
 *    request for 64 images simultaneously will likely crash the client.)
 *
 * The plot update interval and variables for controlling the data collection is
 * set here.
 */

//var run_plot_update = false;
// const plot_update_interval = 1000;

function show_det_summary(detid) {
  // Showing the text based detector part.
  $('#single-det-summary').children().each(function () {
    $(this).addClass('hidden');
  });

  $('#det-plot-and-figure').children().each(function () {
    $(this).addClass('hidden');
  })

  $('#single-det-summary')
    .children(`#single-det-summary-${detid}`)
    .removeClass('hidden');

  $('#det-plot-and-figure')
    .children(`#det-plot-container-${detid}`)
    .removeClass('hidden');

}


/**
 * Running an ajax command get the data of a detector processes. The tag is then
 * parse to trigger the plotly plotting routines.
 */
function update_detector_data(detid, tag) {
  $.ajax({
    dataType: 'json',
    mimeType: 'application/json',
    url: `data/${tag}/${detid}`,
    success: function (json) {
      if (!jQuery.isEmptyObject(json)) {
        if (tag == `zscan`) {
          make_zscan_plot(detid, json);
        } else if (tag == `lowlight`) {
          make_lowlight_plot(detid, json);
        } else if (tag == `lumialign`) {
          make_lumialign_plot(detid, json);
        } else {
          console.log(`Unrecognized plot data`)
          console.log(data);
        }
      }
    },
    error: function () {
      console.log(`Failed to get data for Process:${tag}, Detector ${detid}`);
    }
  });
}

/**
 * Re-formatting the data responded by the ajax data request for z scan process
 * to run the plotly plotting routine.
 */
function make_zscan_plot(detid, data) {
  var x = []
  var y = []
  var b = []

  for (var i = 0; i < data['array'].length; ++i) {
    x.push(data['array'][i][0]);
    y.push(data['array'][i][1]);
    b.push(data['array'][i][2] / 1000);
  }

  var plot_data = [{
    x: x,
    y: y,
    marker: {
      size: 5,
      color: b,
      colorscale: 'Bluered',
      colorbar: {
        title: "Bias [V]"
      }
    },
    type: 'scatter',
    mode: 'markers',
    name: 'Readout value'
  }];


  const plotname = `single-det-summary-plot-${detid}-zscan`;

  if ($(`#${plotname}`).length != 0) {
    // TODO: move css settings to somewhere else.
    $(`#${plotname}`).css('height', '300px');
    $(`#${plotname}`).css('width', '400px');

    Plotly.newPlot(plotname,
      plot_data,
      layout_intensity_scan_plot,
      layout_default_config);
  } else {
    console.log("Warning! DIV for plot doesn't exist");
  }
}

const layout_intensity_scan_plot = {
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
  },
  title: false
}

/**
 * Reprocessing the histograms instance into a format understood by plotly.
 */
function make_lowlight_plot(detid, data) {
  const y = data.bincontent;
  var x = [];
  for (var i = 0; i < data.bincontent.length; ++i) {
    x.push((data.binedge[i] + data.binedge[i + 1]) / 2.0);
  }

  const plot_data = [{
    x: x,
    y: y,
    type: 'bar',
    mode: 'markers',
    name: 'Readout value',
    marker: {
      color: 'rgb(41,55,199)',
    }
  }];

  const plotname = `single-det-summary-plot-${detid}-lowlight`;

  if ($(`#${plotname}`).length != 0) {
    // Move to a different function to handle css formatting?
    $(`#${plotname}`).css('height', '300px');
    $(`#${plotname}`).css('width', '400px');

    Plotly.newPlot(plotname,
      plot_data,
      layout_lowlight_plot,
      layout_default_config);
  } else {
    console.log("Warning! DIV for plot doesn't exist");
  }
}

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

/**
 * Parsing the information to get the luminosity plots for plotly
 */
function make_lumialign_plot(detid, data) {
  var x = []
  var y = []
  var lumi = []
  for (var i = 0; i < data.array.length; ++i) {
    x.push(data.array[i][0]);
    y.push(data.array[i][1]);
    lumi.push(data.array[i][2]);
  }

  var plot_data = [{
    x: x,
    y: y,
    z: lumi,
    type: 'contour',
    colorscale: 'RdBu',
  }];

  const plotname = `single-det-summary-plot-${detid}-lumialign`;
  if ($('#' + plotname).length != 0) {
    $('#' + plotname).css('height', '300px');
    $('#' + plotname).css('width', '400px');
    Plotly.newPlot(plotname,
      plot_data,
      layout_lumialign_plot,
      layout_default_config);
  } else {
    console.log("Warning! DIV for plot doesn't exist")
  }
}

const layout_lumialign_plot = {
  autosize: true,
  xaxis: {
    title: "x position [mm]",
    autorange: true
  },
  yaxis: {
    title: "y position [mm]",
    autorange: true
  },
  zaxis: {
    title: "Readout V-ns",
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
};

