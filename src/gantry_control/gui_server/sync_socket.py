from ..cli.format import logrecord_to_dict
from ..cli.progress_monitor import TqdmCustom
from .session import (ActionEntry, ActionStatus, GUISession, HardwareStatus,
                      TelemetryEntry)


def sync_full_session(session: GUISession):
    """
    Synchronising all items. This should be run when a new client is connection
    """
    sync_telemetry_full(session)
    sync_logging_full(session)
    sync_action_full(session)
    sync_hardware_status(session)
    sync_board_status(session)


"""
Updating related actions triggered either by the GUI client user.
"""


def sync_action_full(session: GUISession):
    """
    Updating the the entire action list. This should probably only be ran when
    a new client is connected.
    """
    session.socket.emit(
        "update-session-action-full", [x.__dict__ for x in session.action_log]
    )


def sync_action_append(session: GUISession, action: ActionEntry):
    """Sending the final action to the client"""
    session.action_log.append(action)
    session.socket.emit("update-session-action-append", action.__dict__)


def sync_action_status_update(session: GUISession, status: ActionStatus):
    """Updating the action status"""
    session.action_log[-1].log.append(status)
    session.socket.emit("update-session-action-status", status.__dict__)


def sync_action_progress(session: GUISession, progress_bar: TqdmCustom):
    """Updating the action progress"""
    session.action_log[-1].progress = [progress_bar.n, progress_bar.total]
    session.socket.emit(
        "update-session-action-progress", session.action_log[-1].progress
    )


"""
Related in the telemetry data stream
"""


def sync_telemetry_full(session: GUISession):
    session.socket.emit(
        "update-session-telemetry-full",
        [x.__dict__ for x in session.telemetry_logger],
    )


def sync_telemetry_append(session: GUISession, entry: TelemetryEntry):
    session.telemetry_logger.append(entry)
    session.socket.emit("update-session-telemetry-append", entry.__dict__)


"""
Syncing the hardware control status mode
"""


def sync_hardware_status(session: GUISession):
    """
    Simple string for connecting to summarize the hardware connection status
    """

    def _make_gantryHW_status():
        hw = session.hw
        if hw is None:
            return None
        if hw.socket.closed:
            return None
        return f"{hw._host}:{hw._port}"

    def _make_tileboard_status():
        # TODO properly implement tileboard testing status
        return None
        tbt = session.tbt
        if tbt is None:
            return None
        if tbt.socket.closed():
            return None
        return None

    session.socket.emit(
        "update-session-hardware-status",
        HardwareStatus(
            gantryHW=_make_gantryHW_status(), tileboardHW=_make_tileboard_status()
        ).__dict__,
    )


"""
Syncing the logging message entries
"""


def sync_logging_full(session: GUISession):
    """Individual messages will be handled by the SocketHandler instance"""
    session.socket.emit(
        "update-message-logging-full",
        [logrecord_to_dict(x) for x in session._mem_handlers.record_list],
    )


"""
Synchronizing the board status. To avoid misdiagnosing on the user side, the
board will always be fully synchronized if board changed.
"""


def sync_board_status(session: GUISession):
    if session.board is None:
        session.socket.emit("sync-board", None)
    else:
        session.socket.emit("sync-board", session.board.__dict__)
