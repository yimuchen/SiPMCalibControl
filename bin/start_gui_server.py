import logging

import gantry_control.gui_server as server

if __name__ == "__main__":
    session = server.session.GUISession(logger=logging.getLogger("GUITest"))
    server.view.register_view_methods(session)
    server.action_socket.register_action_sockets(session)
    server.run_server(session)
