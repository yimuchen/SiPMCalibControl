# Web-based GUI design

The key tech used in the web based interface is a [web socket][websocket]
communication between a server containing the command line interface described in
the [CLI documentation](../ctlcmd), and a web-page hosting the client javascript
for data display. The GUI is designed mainly for standard calibration sequences,
so do not expect fine controls over the various calibration processes like with
the command line interface.

Since the “GUI” has two logically disconnected components, ther server side that
is used to handle the underlying hardware, and the client side that is used to
display results and controls to the end users. Here we define 3 types of
communications:

- The client sending data to the server side as “action requests”: these are
  small data packages that is used to trigger hardware action. In such cases, all
  future action request will be discarded until the the all requested hardware
  actions have been completed. The creation of such signals can be found in the
  "js/action.js" file, while the corresponding processing of these signals will
  be handled in the "action.py" file.
- The server will send data to the client via a "sync" type data, these are data
  needs the client to see identical values with the data to avoid operation
  errors, or is frequently updated server side. The emission of these
  communications on the server side can be found in the "sync.py" and the
  handling of such signals should be found in the "js/sync.js" file.
- The server will send data to the client via "report" requests. This is data
  that is either expensive to compute server side or is not critical to the
  operation of the calibration, so is only presented to the client on request.
  For the client side, this should be done via ajax URL request, and response of
  thess requests will be handled in the "report.py" file.

The socketio server for handling various signals and communicating user commands
with the underlying command line application is documented in the
[`sockets`](sockets) directory. Client side GUI design element CSS layout is
placed in [static/sass](static), and the javascript for processing data for
display is found in [static/js](static)

[websocket]: https://en.wikipedia.org/wiki/WebSocket