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
            # Getting the various telemetry streams. Set to `NAN for none data` if the data
            # is not retrieveable
            sync_socket.sync_telemetry_append(
                session_instance,
                session.TelemetryEntry(
                    timestamp=_timestamp_(),
                    **get_tbtester_telemetry(session_instance),
                    **get_gmq_telemetry(session_instance),
                    gantry_coord=get_gantry_coord(session_instance),
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


"""
Helper methods for extracting telemetry data sets depending on availability of
underlying hardware
"""
_nan_ = "_nan_"  # NAN float does not get cast correctly, passing NAN string


def get_gantry_coord(session_instance: session.GUISession):
    if session_instance.hw is None:
        return (_nan_, _nan_, _nan_)
    try:
        return session_instance.hw.get_coord()
    except Exception:
        return (_nan_, _nan_, _nan_)


def get_tbtester_telemetry(session_instance: session.GUISession):
    # TODO: Properly implement
    return dict(tb_sipm_bias=_nan_, tb_led_bias=_nan_, tb_temp=_nan_)


def get_gmq_telemetry(session_instance: session.GUISession):
    # TODO: properly implement
    if session_instance.hw is None:
        return dict(gmq_pulser_temp=_nan_, gmq_pulser_lv=_nan_, gmq_pulser_hv=_nan_)
    else:
        return dict(
            gmq_pulser_temp=numpy.random.normal(25, 1),
            gmq_pulser_lv=numpy.random.normal(1200, 5),
            gmq_pulser_hv=numpy.random.normal(60000, 20),
        )
