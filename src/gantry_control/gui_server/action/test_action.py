from ...cli.progress_monitor import session_iterate
from ..session import GUISession


# Actual methods to processing
def test_single_shot(session: GUISession, line: str):
    """This is a simple test"""
    session.logger.info("Running single shot testing!!")
    for char in session_iterate(session, line):
        session.logger.warn(f"Got characters {char}")
        session.sleep(1)
