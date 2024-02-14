from ...cli.progress_monitor import TqdmCustom
from ..session import ActionEntry, ActionStatus, GUISession


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
