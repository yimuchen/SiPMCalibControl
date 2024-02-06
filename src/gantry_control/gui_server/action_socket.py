"""

Defining how the server should response to various client side action requests.
Here we rely on the decorator pattern, so the register session function will
need to be called after the GUISession object is initialized

"""
import os
import signal

from ..cli.format import _timestamp_
from ..cli.progress_monitor import session_iterate
from .session import (ActionCode, ActionEntry, ActionStatus,  # For typing
                      GUISession)
from .sync_socket import (sync_action_append, sync_action_status_update,
                          sync_full_session)


# Actual methods to processing
def test_single_shot(session: GUISession, line):
    """This is a simple test"""
    print("Got single shot command!!")
    for char in session_iterate(session, line):
        print("Got characters", char)
        session.sleep(1)


# Main methods to keep track of the client-side requested action.
def start_action(session: GUISession, name, **kwargs):
    sync_action_append(
        session,
        ActionEntry(
            name=name,
            log=[
                ActionStatus(
                    status=ActionCode.RUNNING, timestamp=_timestamp_(), message=""
                )
            ],
            **kwargs
        ),
    )


def complete_action(session: GUISession, status=ActionCode.COMPLETE, **kwargs):
    sync_action_status_update(
        session, ActionStatus(timestamp=_timestamp_(), status=status, **kwargs)
    )


# Additional methods for user signal handling
def halt_from_gui_user(session: GUISession):
    """Additional method to recieve a halt signal from the GUI user progress"""
    return session._user_interupt


# Main methods to be exposed via the socket interface
__run_action_method_map__ = {"single-shot-test": test_single_shot}


def register_action_sockets(session: GUISession):
    @session.socket.on("connect")
    def connect():
        print("Connected!!")
        sync_full_session(session)

    @session.socket.on("disconnect")
    def disconnect():
        print("Disconnected")

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
        start_action(session, action_name, args=action_args)
        return_status = ActionCode.COMPLETE
        # Unlocking the session again when starting a new command
        session._user_interupt = False
        try:
            if action_name in __run_action_method_map__:
                __run_action_method_map__[action_name](session, **action_args)
            else:
                print("Got entries", action_name, action_args)
                session.socket.sleep(5)
                raise ValueError("Unrecognized action", action_name)
        except KeyboardInterrupt:
            print("User interupted!!")
            return_status = ActionCode.USER_INTERUPT
        except Exception as err:  # Catch all other exceptions!
            # TODO: pass error message to user
            print("Caught exception", err)
            return_status = ActionCode.SYSTEM_ERROR
        finally:
            print("Completing action", return_status)
            session._user_interupt = False  # Always release!!
            complete_action(session, status=return_status)

    @session.socket.on("user-interupt")
    def user_interupt():
        print("Raising the user interupt flag!!!")
        # os.kill(os.getpid(), signal.SIGINT)
        session._user_interupt = True
