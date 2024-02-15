"""
format.py

Utility functions for formatting the string outputs and processing to be more
pleasant.
"""
import datetime
import logging
import time
from typing import Dict, List, Optional

import numpy


def make_color_text(message: str, colorcode: int) -> str:
    """
    Adding ASCII color headers around message string. More details regarding
    the ASCII code for string colors can be found [here][ascii].

    [ascii]: https://en.wikipedia.org/wiki/ANSI_escape_code
    """
    return f"\033[1;{colorcode:d}m{message}\033[0m"


def RED(message: str) -> str:
    return make_color_text(message, 31)


def GREEN(message: str) -> str:
    return make_color_text(message, 32)


def YELLOW(message: str) -> str:
    return make_color_text(message, 33)


def CYAN(message: str) -> str:
    return make_color_text(message, 36)


def NOCOLOR(message: str) -> str:
    return message


def _str_(text: str) -> str:
    """Collapsing string to a single line."""
    return " ".join(text.split())


_timestamp_fmt_ = "%Y%m%d-%H%M%S"


def time_to_str(t: datetime.datetime) -> str:
    return t.strftime(_timestamp_fmt_)


def str_to_time(s: str) -> datetime.datetime:
    return datetime.datetime.strptime(s, _timestamp_fmt_)


def _timestamp_(t: Optional[datetime.datetime] = None) -> str:
    """
    Returning time in standardized format. If no explicit datetime is given use
    the datetime.now() function.
    """
    if t is None:
        t = datetime.datetime.now()
    return t.strftime(_timestamp_fmt_)


def prompt_input(message: str, allowed: Optional[List[str]] = None) -> str:
    """
    Helper function for required command line interactions.
    """
    while True:
        input_val = input(message)
        # Default behavior for no inputs.
        if allowed is not None and input_val not in allowed:
            print(f'Illegal value: "{input_val}", valid inputs: {allowed}')
        else:
            return input_val


def prompt_yn(question: str, default: Optional[bool] = None) -> bool:
    """
    Present a yes/no question and prompt a question to the user and return
    their answer. The default can be used for a default yes/no result if user
    does not provide an explicit input.
    """
    valid_map = {"yes": True, "ye": True, "y": True, "no": False, "n": False}

    if default is not None:
        valid_map[""] = default
    prompt_str = (
        " [Y/n] " if default is True else " [y/N] " if default is False else " [y/n] "
    )

    return valid_map[
        prompt_input(_str_(question + prompt_str), allowed=valid_map.keys())
    ]


def _value_rounding(x):
    return numpy.round(x, decimals=1)


def loop_mesh(*args):
    """
    Given list of iterables, create meshgrid of so that all combinations are
    tested.
    """
    if len(args) == 0:
        raise ValueError("Requires at least 1 iterable")
    if len(args) == 1:  # Trivial operation
        return args[0]

    array_list = numpy.meshgrid(*args)
    return numpy.vstack([x.ravel() for x in array_list]).T


"""
Methods for casting logging record to other containers
"""

__all_logging_levels__ = {
    # Integer to string casting
    val: k
    for k, val in logging.__dict__.items()
    if k.upper() == k and type(val) is int
}


def logrecord_to_dict(record: logging.LogRecord) -> Dict[str, str]:
    return {
        "time": _timestamp_(
            datetime.datetime.fromtimestamp(time.mktime(time.localtime(record.created)))
        ),
        "name": record.name,
        "level": __all_logging_levels__[record.levelno],
        "msg": _str_(record.msg),
        "args": record.args,
    }


def logrecord_to_line(record: logging.LogRecord) -> str:
    rec_dict = logrecord_to_dict(record)
    line = "{time}:::{name}:::{level}:::{msg}".format(**rec_dict)
    if rec_dict["args"]:  # For non empty arguments
        line += f':::{_str_(str(rec_dict["args"]))}'
    return line
