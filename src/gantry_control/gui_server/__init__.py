# Do nothing but import everyting
import numpy

from ..cli.format import _timestamp_
from . import action_socket, session, sync_socket, view


def run_server(session_instance: session.GUISession, host="localhost", port=9100):
    """
    Book keeping all of the various systems to be handled
    """

    # Addtional function to register to the GUI session
    session_instance._progress_halt_methods.append(action_socket.halt_from_gui_user)
    session_instance._progress_update_methods.append(sync_socket.sync_action_progress)

    def _run_telemetry_heartbeat() -> None:
        while session_instance._server_active:
            sync_socket.sync_telemetry_append(
                session_instance,
                session.TelemetryEntry(
                    timestamp=_timestamp_(),
                    sipm_bias=numpy.random.normal(45, 0.01),
                    sipm_temp=numpy.random.normal(25, 2),
                    gantry_coord=(50, 50, 50),
                ),
            )
            session_instance.sleep(2.0)

    action_socket.start_action(session_instance, name="server-start-up")
    session_instance._server_active = True
    # Starting some additional item
    telemetry_thread = session_instance.socket.start_background_task(
        target=_run_telemetry_heartbeat
    )
    action_socket.complete_action(session_instance)
    print(session_instance.action_log)

    # Debug MUST BE FALSE!! To
    session_instance.socket.run(session_instance.app, debug=False, host=host, port=port)

    # Additional actions to take after the server has been terminated
    session_instance._server_active = False
    telemetry_thread.join()
