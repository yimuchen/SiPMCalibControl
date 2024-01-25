from .session import GUISession  # For typing


def sync_full_session(session: GUISession):
    sync_telemetry(session)


def sync_telemetry(session: GUISession):
    session.socket.emit(
        "update-session-telemetry",
        [x.__dict__ for x in session.telemetry_logger],
    )
