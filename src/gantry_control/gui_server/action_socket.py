"""

Defining how the server should response to various client side action requests.
Here we rely on the decorator pattern, so the register session function will
need to be called after the GUISession object is initialized


"""
import json

from .session import GUISession  # For typing
from .sync_socket import sync_full_session


def register_action_sockets(session: GUISession):
    @session.socket.on("connect")
    def connect():
        print("Connected!!")

    @session.socket.on("disconnect")
    def disconnect():
        print("Disconnected")
