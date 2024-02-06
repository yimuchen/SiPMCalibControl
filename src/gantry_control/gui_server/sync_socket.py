from ..cli.progress_monitor import TqdmCustom
from .session import ActionEntry, ActionStatus, GUISession, TelemetryEntry


def sync_full_session(session: GUISession):
    """
    Synchronising all items. This should be run when a new client is connection
    """
    sync_telemetry_full(session)
    sync_action_full(session)
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
Synchronizing the board status. To avoid misdiagnosing on the user side, the
board will always be fully synchronized if board changed.
"""


def sync_board_status(session: GUISession):
    if session.board is None:
        session.socket.emit("sync-board", None)
    else:
        session.socket.emit("sync-board", session.board.__dict__)
