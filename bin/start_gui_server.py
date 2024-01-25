import logging

from gantry_control.gui_server.session import GUISession

if __name__ == "__main__":
    s = GUISession(logger=logging.getLogger("GUITest"))
    s.run_server()
