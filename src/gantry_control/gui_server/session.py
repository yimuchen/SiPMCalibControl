"""

This file will add the additional entry containers that is required to for GUI
session hosting. Aside from the items already hosted in the cli session,
additional niceties will be added, as well as the python objects used to
control the web server session.

"""

import collections
import logging
import os
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import gmqclient
import numpy as np
import tqdm
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO

# Additional data classes. Corresponding containers should be implemented in the
# gui_client/src/server_types directory
from ..cli.board import Board, Conditions
from ..cli.format import _timestamp_
from ..cli.session import Session


@dataclass
class TelemetryEntry:
    timestamp: str
    sipm_bias: float
    sipm_temp: float
    gantry_coord: Tuple[float, float, float]


@dataclass
class ActionEntry:
    timestamp: str
    requested_action: str
    action_status: str
    action_message: str
    action_progress: Tuple[int, int]


class GUISession(Session):
    """Overloading to handle sessions for session progress"""

    def __init__(
        self,
        logger: logging.Logger,
        hw: Optional[gmqclient.HWControlClient] = None,
        board: Optional[Board] = None,
        conditions: Optional[Conditions] = None,
        view_method_list: Optional[Dict[str, Callable]] = None,
        action_method_list: Optional[Dict[str, Callable]] = None,
    ):
        super().__init__(logger=logger, hw=hw, board=board, conditions=conditions)
        self._js_client_path = os.path.abspath(
            os.path.dirname(__file__) + "../../../gui_client/build/"
        )
        self.app = Flask(
            "Gantry Control UI",
            template_folder=self._js_client_path,
            static_folder=os.path.join(self._js_client_path, "static"),
        )
        self.socket = SocketIO(self.app, cors_allowed_origins="*")

        # Adding additional messages for the current progress
        self.telemetry_logger = collections.deque([], maxlen=65536)
        self.action_log: List[ActionEntry] = []

        # Additional flags for keeping track of the server loop
        self._server_active = False

        # Registering the URLs allowed for the connection
        self.app.config["SECRET_KEY"] = "secret!"  # Is this a security concern?
        self.app.config["TEMPLATE_AUTO_RELATED"] = True
        ## Available view methods should be implemented in the view.py file

        # What the server should do on socket event is defined in the
        # action_socket module
        # self.socket.on_event("connect", self.connect)

    def run_server(self, host="localhost", port=9100):
        self._server_active = True
        # Starting some additional item
        self._telemetry_thread = self.socket.start_background_task(
            target=self.run_telemetry_heartbeat
        )
        # Debug MUST BE FALSE!! To
        self.socket.run(self.app, debug=False, host=host, port=port)

        # Additional actions to take after the server has been terminated
        self._server_active = False
        self._telemetry_thread.join()

    def make_pbar(self, x):
        return tqdm.tqdm(x)

    def run_telemetry_heartbeat(self) -> None:
        while self._server_active:
            self.telemetry_logger.append(
                TelemetryEntry(
                    timestamp=_timestamp_(),
                    sipm_bias=np.random.normal(45, 0.01),
                    sipm_temp=np.random.normal(25, 2),
                    gantry_coord=(50, 50, 50),
                )
            )
            self.emit_to_client_telemetry()
            self.socket.sleep(2.0)

    def response_data_request(session, sid, msg):
        return {
            "requested_file": msg,
            "x": np.random.random(size=100),
            "y": np.random.random(size=100),
        }

    def terminate_current_action(session, sid, msg):
        pass

    def run_routine(session, sid, msg):
        print("Running routine", routine_name, "with arguments", args)
        for i in session.make_pbar():
            session.check_terminate()
            time.sleep(1)  # Forcing this method to be slow

    def emit_to_client(self):
        self.emit_to_client_telemetry()

    def emit_to_client_telemetry(self):
        self.socket.emit(
            "update-session-telemetry", [x.__dict__ for x in self.telemetry_logger]
        )
