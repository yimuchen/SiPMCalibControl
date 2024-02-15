"""

Containers for storing session information (such as progress to the calibration
system)

"""
import argparse
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Union

import gmqclient

from .board import Board, Conditions
from .format import _str_, str_to_time


@dataclass
class Session(object):
    # Main attribues to for handling the session
    hw: Optional[gmqclient.HWControlClient]
    logger: logging.Logger
    board: Optional[Board]
    conditions: Optional[Conditions]

    # Addtional variable for that is required
    max_x: int = 350
    max_y: int = 350
    max_z: int = 350

    # Addtional methods to handle progress monitoring. Mainly required for the
    # GUI session. The cli-session will likely keep this method blank. Function
    # signature should be (Session, tqdm object)
    _progress_halt_methods: List[Callable] = field(default_factory=lambda: [])
    _progress_update_methods: List[Callable] = field(default_factory=lambda: [])

    def init(self, **kwargs) -> None:
        """
        Initializing the various connections and hardware requirements
        """
        if kwargs.get("session_json"):
            # Early exit if specifying directly from json
            self.init_from_json(kwargs.get("session_json"))
            return
        # Individual parsing
        assert kwargs["hw_connection"], "Required to establish gantry control client"
        self._init_hw(kwargs["hw_connection"])
        self._init_conditions(kwargs["conditions"])
        assert kwargs[
            "board"
        ], "Board is required to be specified if gantry no session_json is given"
        self._init_board(kwargs["board"])

    def init_from_json(self, json_file: str) -> None:
        # Assuming JSON file is written in the format that can be reset
        # according to the
        self.init(json.load(open(json_file, "r")))
        pass

    def _init_hw(self, hw_connection: str) -> None:
        """Setting up the gantry control client"""
        server, port = hw_connection.split(":")
        self.hw = gmqclient.create_default_client(server, int(port))

        # Additional methods defined below
        setattr(type(self.hw), "get_ledlv", _get_ledlv)
        setattr(type(self.hw), "get_ledhv", _get_ledlv)
        setattr(type(self.hw), "get_ledtemp", _get_ledtemp)
        setattr(type(self.hw), "get_dettemp", _get_dettemp)
        setattr(type(self.hw), "get_dethv", _get_dethv)

    def _init_conditions(self, conditions: Optional[str]) -> None:
        if not conditions:
            self.conditions = Conditions()  # Create blank conditions

        else:
            if os.path.isdir(conditions):
                # Pass
                pass
            elif os.path.isfile(conditions):
                self.conditions = Conditions.from_json(conditions)
            else:
                raise ValueError(f"Unknown path type for [{conditions}]")

    def _init_board(self, board_file: Union[List[str], str]) -> None:
        """
        Initializing the board used for the session. This can either be:

        (1) The path to the file storing the board and existing result.
        (2) "+<boardtype>[@<id>]" to search for the latest board result in the
            store directory.
        (3) "++<boardtype>@<id>" to start a new session with board type and id
        """
        if board_file.startswith("+"):
            self.board = Board.auto_resolve_jsonfile(board_file)
        else:
            self.board = Board.from_json(board_file)

    def update_pbar_data(self, **kwargs: Dict[str, str]) -> None:
        self.pbar.set_postfix(
            {
                "Gantry": "({0:0.1f},{1:0.1f},{2:0.1f})".format(*self.hw.get_coord()),
                "LV": f"{self.hw.get_ledlv():5.3f}V",
                "PT": f"{self.hw.get_ledtemp():4.1f}C",
                "ST": f"{self.hw.get_dettemp():4.1f}C",
                **kwargs,
            }
        )

    # TODO: Do we need to check for closing methods on exit?
    # def __del__(self):
    #     if isinstance(self.hw, gmqclient.HWControlClient):
    #         self.hw.socket.close()

    def sleep(self, t: float):
        """
        Method for sleeping the progress thread. This should be handle via the
        session in case there are multi-threaded uses cases. For the
        cli-session, a simple time.sleep call can be used.
        """
        time.sleep(t)


def load_blank_session(logger: logging.Logger):
    """
    Loading a blank session to be initialized manually. This is usually required
    for starting a session for a single-shot command
    """
    return Session(hw=None, logger=logger, board=None, conditions=None)


def add_session_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    group = parser.add_argument_group(
        "Session arguments",
        "Arguments requires to setup the session for the single shot command",
    )
    group.add_argument(
        "--session_json",
        type=str,
        help="""
        JSON file that stores the configuration settings for establishing a
        session. Notice that if this is specified all other arguments in the
        this argument group will be ignored.
        """,
    )
    group.add_argument(
        "--conditions",
        type=str,
        default=".session/conditions/",
        help="""
        Path to the gantry conditions. If explicitly set to an empty path, we
        will load in an empty condition. If this path is a json file, attempt to
        load the specified file. If this path is a directory, attempt to load
        the newest conditions file in that directory.
        """,
    )
    group.add_argument("--board", type=str, help=Session._init_board.__doc__)
    group.add_argument(
        "--hw_connection",
        type=str,
        help="""
        Connection settings for the gantry control client. Should be in the
        format of '<host>:<port>', where "host" and "port" refer to the machine
        hosting the gantry control sever session (usually a RPi).
        """,
    )

    return parser


def parse_session_args(
    session: Session, args: argparse.Namespace
) -> argparse.Namespace:
    """
    This is a unique argument parser that will directly modify the session
    directly. Here we assume that the session will need to be initialized for
    the other argument parsers to make sense.
    """
    session.init(**args.__dict__)
    return args


"""
Additional specialization for getting the monitoring information. All the self
items here should be the HWControlClient instance
"""


def _get_ledlv(self):
    # TODO!!
    return 0


def _get_ledhv(self):
    # TODO!!
    return 0


def _get_ledtemp(self):
    # TODO!!
    return 0


def _get_dettemp(self):
    # TODO!!
    return 0


def _get_dethv(self):
    # TODO!!
    return 0
