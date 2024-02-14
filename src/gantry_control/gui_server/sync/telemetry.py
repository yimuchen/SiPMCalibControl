from ..session import GUISession, TelemetryEntry


def sync_telemetry_full(session: GUISession):
    session.socket.emit(
        "update-session-telemetry-full",
        [x.__dict__ for x in session.telemetry_logger],
    )


def sync_telemetry_append(session: GUISession, entry: TelemetryEntry):
    session.telemetry_logger.append(entry)
    session.socket.emit("update-session-telemetry-append", entry.__dict__)
