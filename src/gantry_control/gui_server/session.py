"""

This file will add the additional entry containers that is required to for GUI
session hosting. Aside from the items already hosted in the cli session,
additional niceties will be added, as well as the python objects used to
control the web server session.

"""

import collections
import datetime
import enum
import logging
import os
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

import flask
import flask_socketio
import gmqclient

# Additional data classes. Corresponding containers should be implemented in
# the gui_client/src/session.ts type definition
from ..cli.board import Board, Conditions
from ..cli.session import Session


@dataclass
class TelemetryEntry:
    timestamp: str
    sipm_bias: float
    sipm_temp: float
    gantry_coord: Tuple[float, float, float]


class ActionCode(enum.IntEnum):
    COMPLETE = 0
    RUNNING = 1
    SYSTEM_ERROR = 2  # Completed but something when wrong
    WAITING_USER_INPUT = 3
    USER_INTERUPT = 4  # User explicitly force process to stop


@dataclass
class ActionStatus:
    timestamp: str
    message: str = ""
    status: int = ActionCode.RUNNING

    @property
    def __dict__(self):
        return {
            "timestamp": self.timestamp,
            "message": self.message,
            "status": int(self.status),
        }


@dataclass
class ActionEntry:
    name: str
    progress: Tuple[int, int] = (None, None)
    args: Any = None  # The unmodified object of the client side argument
    log: List[ActionStatus] = field(default_factory=lambda: [])

    @property
    def __dict__(self):
        return {
            "name": self.name,
            "progress": self.progress,
            "args": self.args,
            "log": [x.__dict__ for x in self.log],
        }


class GUISession(Session):
    """Overloading to handle sessions for session progress"""

    def __init__(
        self,
        logger: logging.Logger,
        hw: Optional[gmqclient.HWControlClient] = None,
        board: Optional[Board] = None,
        conditions: Optional[Conditions] = None,
    ):
        # Initializing the underlysing session class
        super().__init__(logger=logger, hw=hw, board=board, conditions=conditions)

        # Initializing the addional flask items
        self._js_client_path = os.path.abspath(
            os.path.dirname(__file__) + "../../../gui_client/build/"
        )
        self.app = flask.Flask(
            "Gantry Control UI",
            template_folder=self._js_client_path,
            static_folder=os.path.join(self._js_client_path, "static"),
        )
        self.socket = flask_socketio.SocketIO(self.app, cors_allowed_origins="*")

        # Adding additional messages for the current progress
        self.telemetry_logger = collections.deque([], maxlen=1024)
        self.action_log: List[ActionEntry] = []

        # Additional flags for keeping track of the server loop can global
        # signaling
        self._server_active = False

        # Registering the URLs allowed for the connection. This will be
        # implmented in the view.py module
        self.app.config["SECRET_KEY"] = "secret!"  # Security concern?
        self.app.config["TEMPLATE_AUTO_RELATED"] = True
        # self.app.add_url_rule(XXX)

        # What the server should do on socket event is defined in the
        # action_socket.py module
        # self.socket.on_event("connect", self.connect)

    @property
    def current_action(self) -> Optional[ActionEntry]:
        if len(self.action_log):
            return self.action_log[-1]
        else:
            return None

    @property
    def current_status(self) -> int:
        return self.current_action.log[-1].status

    def sleep(self, t: float):
        """
        Thread sleeping should be handled by the main socket instanct to make
        sure it is not halting other actions. Updating in increments of
        subseconds for better responsiveness.
        """
        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).total_seconds() < t:
            self.socket.sleep(0.05)
