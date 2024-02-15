from ..session import GUISession
from ..sync import sync_board_status


def start_new_session(session: GUISession, board_type: str, board_id: str):
    session._init_board(f"++{board_type}@{board_id}")
    sync_board_status(session)


def load_session(session: GUISession, session_id: str):
    session._init_board(f"+{session_id}")
    sync_board_status(session)
