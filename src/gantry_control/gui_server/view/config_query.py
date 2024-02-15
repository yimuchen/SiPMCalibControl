import glob
import os
import pathlib

from ...cli.board import PROJECT_ROOT
from ..session import GUISession


def board_types(session: GUISession):
    glob_str = os.path.join(PROJECT_ROOT, "config_templates/board_layout/*.json")
    boardfiles = glob.glob(glob_str)
    return [pathlib.Path(os.path.basename(x)).stem for x in boardfiles]


def template_yamls(session: GUISession):
    yamlfiles = glob.glob(
        os.path.join(PROJECT_ROOT, "config_templates/tbc_yaml/*.yaml")
    )
    return [pathlib.Path(os.path.basename(x)).stem for x in yamlfiles]


def saved_sessions(session: GUISession):
    savefiles = glob.glob(os.path.join(PROJECT_ROOT, "results/*.json"))
    return [pathlib.Path(os.path.basename(x)).stem for x in savefiles]
