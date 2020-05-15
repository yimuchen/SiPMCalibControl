# The GUI server session

The server session uses the [flask socketio][flasksocket] for the socket i/o
handling. A single global `SocketIO()` instance is initiated in the package
`__init__.py` file for all sub-routines to emit signals. In the same
`__init__.py` file, a global instance of the `Session` object is used to record
the system status, as well as carrying a striped down version of the collected
data to pass to the client for display. All server interactions are then defined
as functions that interact with these two global objects.

- [`parsing.py`](parsing.py) contains the first function for immediately
  receiving the socket signals and determining whether to process the signal and
  which function to take over the socket signal.
- [`calibration.py`](calibration.py) contains the functions that define the main
  calibration sequences.
- [`report.py`](report.py) contains the functions for processing simplified data
  and system status and emitting the update signals to the client. **TO BE
  REFACTORED**

[flasksocket]: https://flask-socketio.readthedocs.io/en/latest/