from ..session import GUISession, HardwareStatus


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
