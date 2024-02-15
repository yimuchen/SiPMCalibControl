""" 
Representing some server-side information as a downloadable file
"""
from flask import jsonify

from ...cli.format import logrecord_to_dict, logrecord_to_line
from ..session import GUISession

# Default casting methods
__filetype_map__ = {"json": jsonify, "txt": lambda x: str(x)}


def action_log(session: GUISession, filetype: str):
    return __filetype_map__[filetype](session.action_log)


def message_log(session: GUISession, filetype: str):
    content = session._mem_handlers.record_list
    if filetype == "json":
        return jsonify([logrecord_to_dict(x) for x in content])
    else:
        return "\n".join([logrecord_to_line(x) for x in content])
