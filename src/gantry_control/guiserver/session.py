from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

import threading
import numpy as np
import time


class GUISession(object):
    """Overloading to handle sessions for session progress"""

    def __init__(self):
        print("Creating object!!")
        self.app = Flask("GantryControlUI_Server")
        self.app.config["SECRET_KEY"] = "secret!"
        # CORS(self.app, resources={r"/*": {"origins": "*"}})
        self.socket = SocketIO(self.app, cors_allowed_origins="*")

        ## Register methods various connection methods
        self.socket.on_event("connect", self.connect)
        self.socket.on_event("disconnect", self.disconnect)

        # Additional flags for keeping track of the server loop
        self._server_active = False
        print("creating thread")

    def run_server(self):
        self._server_active = True
        self._telemetry_thread = self.socket.start_background_task(
            target=self.run_telemetry_heartbeat
        )
        self.socket.run(self.app, debug=False, port=9100)  ## Debug MUST BE FALSE!!

        # Additional actions to take after the server has been terminated
        self._server_active = False
        self._telemetry_thread.join()

    def make_pbar(self, x):
        return tqdm.tqdm(x)

    def run_telemetry_heartbeat(self):
        while self._server_active:
            print(self)
            self.socket.emit("tb", make_telemetry_data(self))
            self.socket.sleep(0.5)

    def connect(self, data):
        print("Connected!!", data)
        self.socket.emit("tb", make_telemetry_data(self))

    def disconnect(self):
        print("Disconnected!!")
        self.socket.emit("tb", make_telemetry_data(self))

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


def make_telemetry_data(session):
    """Just random data for now"""
    return {"Gaussian": np.random.normal(), "Poisson": np.random.poisson()}


if __name__ == "__main__":
    s = GUISession()
    s.run_server()
