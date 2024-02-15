# The GUI control session

This module implements wrapping the control session and related controls to a
GUI using a [`flask`][flask] + [`socketio`][socketio] server. The
implementation of the session handling with additional containers to assist
with GUI control interface can be found in the session interface. The
overarching model of this that the variable representing the session is
mirrored to the client session (implemented in the directory
[`src/gui_client`](../../gui_client)), and various actions that change the
status should be mirrored to the client.

There are 3 types of interaction that can occur between the client and the
session.

- Server side update: Any changes that change the session status should be
  mirrored to the client side for display. This will always be performed via a
  server-side socket emit action. Such actions will be implemented in the
  `sync_socket.py` module.
- Client-side action request: The client can send an action that will change
  how the status of the underlying session. This will always be performed via a
  client-side socket emit action. The server side responses of this will be
  implemented in the `action_socket.py` module.
- Client side data request: this is a read-only request that is noncritical to
  the software operation. Typically, this includes data for result plotting,
  listing available options for action augmentation, and request for file
  download (if they exist). Such actions are implemented as URL request. The
  handling of such request will be implemented in the `views.py` module.


[flask]: https://flask.palletsprojects.com/en/3.0.x/
[socketio]: https://flask-socketio.readthedocs.io/en/latest/
