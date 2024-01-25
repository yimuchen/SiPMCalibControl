"""
Additional logging handlers to retain lossy record in memory
"""
import json
import logging
import time
from typing import Dict, List

from ..cli.format import _str_, time_to_str

__all_logging_levels__ = {
    val: k for k, val in logging.__dict__.items() if k.upper() == k and type(val) == int
}


class FIFOHandler(logging.Handler):
    """
    Lossy handling logging records in memory using a first-in-first-out
    scheme.
    """

    def __init__(self, capacity: int, level: int = logging.NOTSET):
        super().__init__(level=level)
        self.record_list = collections.deque([], maxlen=capacity)

    def emit(self, record: logging.LogRecord):
        self.record_list.append(record)

    def record_to_dict(self, record: logging.LogRecord) -> Dict[str, str]:
        return {
            "time": time_to_str(time.localtime(record.created)),
            "name": record.name,
            "level": __all_logging_levels__[record.levelno],
            "msg": _str_(record.msg),
            "args": record.args,
        }

    def record_to_line(self, record) -> str:
        """
        @brief Returning a record instance as a single line of text.
        """
        rec_dict = self.record_to_dict(record)
        line = "{time}:::{name}:::{level}:::{msg}".format(**rec_dict)
        if rec_dict["args"]:  # For non empty arguments
            line += f':::{_str_(str(rec_dict["args"]))}'
        return line

    def dump_lines(self, file_obj, exclude: List[int]):
        _ = [
            file_obj.write(self.record_to_line(record) + "\n")
            for record in self.record_list
            if __all_logging_levels__[record.levelno] not in exclude
        ]

    def dump_json(self, file_obj, exclude: List[int]):
        json_dict = {
            "dumptime": time_to_str(time.localtime(time.time())),
            "excluded": exclude,
            "entries": [
                self.record_to_dict(record)
                for record in self.record_list
                if __all_logging_levels__[record.levelno] not in exclude
            ],
        }
        json.dump(json_dict, file_obj, indent=2)

