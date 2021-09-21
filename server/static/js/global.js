/**
 * global.js
 *
 * Defining all the global variables/constants and translation function.
 */

// Main socket interface. This will be initialized on document loading
var socketio = null;

// Constants for the session state. This should mirror session.STATE_XXX in the
// sockets.__init__.py file.
const STATE_IDLE = 0;
const STATE_RUN_PROCESS = 1;
const STATE_EXEC_CMD = 2;
const STATE_WAIT_USER = 3;

// Constants for the run session type. These should mirror the
// session.SESSION_TYPE_XXX in the sockets.__init__.py file.
const SESSION_TYPE_NONE = 0;
const SESSION_TYPE_SYSTEM = 1;
const SESSION_TYPE_STANDARD = 2;

// Constants for command return status code. These should mirror the
// session.CMD_XXX in the sockets.__init__.py file.
const CMD_PENDING = 1;
const CMD_RUNNING = 2;
const CMD_COMPLETE = 0;
const CMD_ERROR = 3;

// Container session variable. Values should mirror the server session via the
// various sync methods.
var session = {
  state: STATE_RUN_PROCESS,
  session_type: SESSION_TYPE_NONE,
  board_type: '',

  // Variables used for progress monitoring
  progress_queue: [],
  updating_progress: false,

  /// Variables used for monitoring
  monitor: {
    start: '',
    time: [],
    temperature1: [],
    temperature2: [],
    voltage1: [],
    voltage2: [],
    gantry_position: [],
  },

  // Terminal instance will also be placed here
  terminal_lock: true,
  terminal: new Terminal({
    cols: 80,
    cursorBlink: true,
    macOptionIsMeta: true,
    scrollback: true,
  }),

  // Flags for client-side continuous update requests
  client_engines: {
    monitor_interval: 500, // monitor update interval in ms.
  },
};

/******************************************************************************
 *
 * COMMON HELPER FUNCTION FOR THE CLIENT DATA PROCESSING FUNCTIONS
 *
 *****************************************************************************/

/**
 * Basic function to allow for async functions to sleep for a certain duration.
 * Main reference:
 * https://www.sitepoint.com/delay-sleep-pause-wait/
 */
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Simple function for making DOM elements in a single function call without the
 * need for custom tag handling.
 */
function dom(tag, attr, content = '') {
  let ans = $(`< ${tag}></${tag}>`);
  ans.attr(attr);
  if (typeof content === 'string') {
    ans.html(content);
  } else if (content instanceof Array) {
    content.forEach((element) => {
      ans.append(element);
    });
  }
  return ans;
}
