# The GUI Client session

The client side uses socket IO to real-time update a web-page to reflect the
status and results of the existing calibration session. Here are try to keep all
the data as simple JavaScript maps to reduce the complexity required for both
server and client, as JSON parser are the only message parsers needed.

## External dependencies

External JavaScript and CSS libraries required by for the client to function is
handled by the master [`package.json`](../../package.json) file:

- [`socket.io-client`][socketioclient]: socket-io client side implementation.
- [`JQuery`][jquery]: For easy element selection and display animations.
- [`Plotly`][plotly]: For generation of plotting elements.
- [`xterm.js`][xterm]: For the display of the client side terminal
- [`fontawesome`][fontawsome]: For special element display

Display elements are stored in the [templates](../templates) directory, while the
CSS styling file is written in SASS format in the [sass](sass) directory. Those
are expected to be self-explanatory so the bulk of the documentation will be the
logic handling implemented in JavaScript.

## Structure of JavaScript code

The design goal of the code-base is such that there is a rough 1-1 correspondence
of the JavaScript client and the python server side code, with the addition of
plotting and display element manipulation.

- [`global.js`](js/global.js) defines all the global variables as well as a bunch
  of translation functions. While certain elements require the page to be loaded
  before being initialized, the null version of the variable will still be
  defined there.
- [`main.js`](js/main.js) What the client should do after the client document (the
  webpage) is loaded. This file contains the exhaustive list of user/server
  initiated function calls either via a button press/keystroke or via a received
  signal, as well the initialization of global variables.
- [`action.js`](js/action.js) Action to be initiated client side. The function here
  will parse the document elements containing the relevant user inputs, then emit
  a `run-action-cmd` signal to the server instance. Waiting for the action to
  complete should be automatically performed.
- [`request.js`](js/request.js) the collection of AJAX request that is used by the
  client.
- [`sync.js`](js/sync.js) The handling of sync signals sent by the server. This
  includes hard sync and soft syncs. For the sake of consistency, the client
  terminal management will also be handled by this file.
- [`view/*.js`](js/view) The handling of all display elements manipulation and
  parsing. As display element manipulation can be extremely verbose in code, the
  decision is make to split the files into various JavaScript files for eases of
  reading.

[socketioclient]: https://github.com/socketio/socket.io-client
[jquery]: https://jquery.com/
[plotly]: https://plotly.com/javascript/
[xtermjs]: https://xtermjs.org/
[fontawesome]: https://fontawesome.com/
