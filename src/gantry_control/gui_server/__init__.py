# Do nothing but import everyting
import numpy as np

from ..cli.format import _timestamp_
from . import action_socket, session, sync_socket, view


def run_server(session_instance: session.GUISession, host="localhost", port=9100):
    def _run_telemetry_heartbeat() -> None:
        while session_instance._server_active:
            session_instance.telemetry_logger.append(
                session.TelemetryEntry(
                    timestamp=_timestamp_(),
                    sipm_bias=np.random.normal(45, 0.01),
                    sipm_temp=np.random.normal(25, 2),
                    gantry_coord=(50, 50, 50),
                )
            )
            sync_socket.sync_telemetry(session_instance)
            session_instance.socket.sleep(2.0)

    session_instance._server_active = True
    # Starting some additional item
    telemetry_thread = session_instance.socket.start_background_task(
        target=_run_telemetry_heartbeat
    )
    # Debug MUST BE FALSE!! To
    session_instance.socket.run(session_instance.app, debug=False, host=host, port=port)

    # Additional actions to take after the server has been terminated
    session_instance._server_active = False
    telemetry_thread.join()
