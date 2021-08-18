/**
 * Terminal settings
 */

/**
 * Creating the global terminal object.
 */
const term = new Terminal({
  cols: 80,
  cursorBlink: true,
  macOptionIsMeta: true,
  scrollback: true,
});

/**
 * Linking the terminal object to the display element by id
 * Setting up the key-stoke parsing.
 */
function start_terminal() {
  term.open(document.getElementById("terminal"));
  // Sending a signal to refresh the prompt is prompt is available.
  parse_keystroke(String.fromCharCode(1)); // Sending ctl+a
  term.onData((key) => {
    parse_keystroke(key);
  });
}

/**
 * Additional parsing required for passing data. This is required as certain
 * key-strokes requires additional translation into a python friendly format.
 * (Notice that the python backend will not attempt to emulate the entire command
 * line session, keys like tab, history crawling will not be available)
 *
 *  Here we keep the logging function for the sake of adding more key-stroke
 *  parsing down the line.
 */
function parse_keystroke(key) {
  str = ''
  for (i = 0; i < key.length; ++i) {
    str += ' ' + key.charCodeAt(i).toString()
  }
  console.log('combination:', str)

  const code = key.charCodeAt(0);// parsing on first character
  switch (code) {
    case 127: // backspace doesn't trigger backspace character
      socketio.emit("xterminput", { input: '\b' });
      break;
    default:
      socketio.emit("xterminput", { input: key });
      break;
  }
}

/**
 * Displaying the output received from server side
 */
function parse_key_response(data) {
  // Parsing output is relatively simple
  console.log("new output received from server:", data.output);
  term.write(data.output);
};
