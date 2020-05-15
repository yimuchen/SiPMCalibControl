# Web-based GUI design

The key tech used in the web based interface is a [web socket][websocket]
communication between a server containing the command line interface described in
the [CLI documentation](../ctlcmd), and a web-page hosting the client javascript
for data display. The GUI is designed mainly for standard calibration sequences,
so do not expect fine controls over the various calibration processes like with
the command line interface.

Since the “GUI” has two logically disconnected components, signal handling at the
server and the client needs special care to ensure that the server doesn't
re-initiate a calibration sequence when the system is busy, and not to update the
GUI display elements when the calculation is semi-completed. As a rule of thumb
in the design philosophy:

- The client should have all “action requests” locked until the server release
  the controls. The client should also have the action requests locked as soon as
  a new action request is initiated to avoid double sending.
- The server will not send display data to the client unless the client
  explicitly requests for it. The client should be the side responsible for
  requesting a data update when display has finished updating.

The socketio server for handling various signals and communicating user commands
with the underlying command line application is documented in the
[`sockets`](sockets) directory. Client side GUI design element CSS layout is
placed in [static/sass](static), and the javascript for processing data for
display is found in [static/js](static)

[websocket]: https://en.wikipedia.org/wiki/WebSocket