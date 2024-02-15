import gmqclient

from ..session import GUISession
from ..sync import hardware


def gmq_disconnect(session: GUISession):
    """"""
    session.logger.info("Disconnected from GMQ server")
    if session.hw is not None:
        session.hw.close()
    session.hw = None
    hardware.sync_hardware_status(session)


def gmq_connect(session: GUISession, host: str, port: int):
    """Connection to Gantry MQ system"""
    session.logger.info(f"Attempting to connect to GMQ server {host}:{port}")
    if session.hw is not None:
        session.hw.close()
    session.hw = gmqclient.create_default_client(host, port)
    session.hw.claim_operator()
    hardware.sync_hardware_status(session)


def gantry_move_to(session: GUISession, x: float, y: float, z: float):
    session.hw.move_to(x=x, y=y, z=z)
