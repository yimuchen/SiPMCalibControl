"""
Additional logging handlers to retain lossy record in memory
"""
import collections
import logging

from flask_socketio import SocketIO

from ..cli.format import logrecord_to_dict


class MemHandler(logging.Handler):
    """
    Lossy handling logging records in memory using a first-in-first-out
    scheme.
    """

    def __init__(self, capacity: int, level: int = logging.NOTSET):
        super().__init__(level=level)
        self.record_list = collections.deque([], maxlen=capacity)

    def emit(self, record: logging.LogRecord):
        self.record_list.append(record)


class SocketHandler(logging.Handler):
    """
    GUI socketio handler to emit a message to all connect clients when a
    logging information arrives.
    """

    def __init__(
        self, socketio: SocketIO, message_id: str, level: int = logging.NOTSET
    ):
        super().__init__(level=level)
        self.socketio = socketio
        self.message_id = message_id

    def emit(self, record: logging.LogRecord):
        self.socketio.emit(self.message_id, logrecord_to_dict(record))
