from ...cli.format import logrecord_to_dict
from ..session import GUISession
from . import action, hardware, telemetry


def sync_full_session(session: GUISession):
    """
    Synchronising all items. This should be run when a new client is connection
    """
    telemetry.sync_telemetry_full(session)
    sync_logging_full(session)
    action.sync_action_full(session)
    hardware.sync_hardware_status(session)
    sync_board_status(session)


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
        session.socket.emit("sync-board", session.board.to_json())
