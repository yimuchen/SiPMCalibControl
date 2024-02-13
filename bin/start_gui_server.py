import logging

import gantry_control.gui_server as server

if __name__ == "__main__":
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger("GUISession")

    session = server.session.GUISession(logger=logger)
    server.view.register_view_methods(session)
    server.action_socket.register_action_sockets(session)
    server.run_server(session)
