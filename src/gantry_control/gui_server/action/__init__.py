"""

Defining how the server should response to various client side action requests.
Here we rely on the decorator pattern, so the register session function will
need to be called after the GUISession object is initialized

"""

from ...cli.format import _timestamp_
from ..session import ActionCode, ActionEntry, ActionStatus, GUISession
from ..sync import action, sync_full_session
from . import board, hardware, test_action


# Main methods to keep track of the client-side requested action.
def _start_action(session: GUISession, name, **kwargs):
    action.sync_action_append(
        session,
        ActionEntry(
            name=name,
            log=[
                ActionStatus(
                    status=ActionCode.RUNNING, timestamp=_timestamp_(), message=""
                )
            ],
            **kwargs,
        ),
    )


def _complete_action(session: GUISession, status=ActionCode.COMPLETE, **kwargs):
    action.sync_action_status_update(
        session, ActionStatus(timestamp=_timestamp_(), status=status, **kwargs)
    )


# Additional methods for user signal handling
def halt_from_gui_user(session: GUISession):
    """Additional method to recieve a halt signal from the GUI user progress"""
    return session._user_interupt


# Main methods to be exposed via the socket interface
__run_action_method_map__ = {
    # Testing actions (should probably be removed for production)
    "single-shot-test": test_action.test_single_shot,
    # Connecting to the various hardware controller clients
    "gmq_disconnect": hardware.gmq_disconnect,
    "gmq_connect": hardware.gmq_connect,
    # Simple control instructions
    "gantry_move_to": hardware.gantry_move_to,
    # Starting a new session
    "start-new-session": board.start_new_session,
    "load-session": board.load_session,
}


def register_action_sockets(session: GUISession):
    @session.socket.on("connect")
    def connect():
        session.logger.info("socketio connected!!")
        sync_full_session(session)

    @session.socket.on("disconnect")
    def disconnect():
        session.logger.info("Socketio disconnected.")

    @session.socket.on("run-action")
    def run_action(msg):
        # Check to see that this is nt running
        if session.current_status in [
            ActionCode.RUNNING,
            ActionCode.WAITING_USER_INPUT,
        ]:
            raise RuntimeError(
                "Already processing a user request!! Discarding new request!"
            )
            return

        action_name = msg["name"]
        action_args = msg["args"]
        _start_action(session, action_name, args=action_args)
        return_status = ActionCode.COMPLETE
        # Unlocking the session again when starting a new command
        session._user_interupt = False
        try:
            if action_name in __run_action_method_map__:
                __run_action_method_map__[action_name](session, **action_args)
            else:
                session.logger.info(f"Got entries {msg}")
                session.sleep(5)
                raise ValueError("Unrecognized action", action_name)
        except KeyboardInterrupt:
            session.logger.error("User interupted!!")
            return_status = ActionCode.USER_INTERUPT
        except Exception as err:  # Catch all other exceptions!
            # TODO: pass error message to user
            session.logger.error(f"Caught exception ({type(err)}: {err})")
            session.logger.error(f"User input values ({msg})")
            return_status = ActionCode.SYSTEM_ERROR
        finally:
            session.logger.info(f"Completing action [{action_name}]")
            session._user_interupt = False  # Always release!!
            _complete_action(session, status=return_status)

    @session.socket.on("user-interupt")
    def user_interupt():
        session.logger.error("Raising the user interupt flag!!!")
        session._user_interupt = True
