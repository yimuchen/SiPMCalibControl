import glob
import os
import pathlib

from ..session import GUISession


def board_types(session: GUISession):
    currentpath = os.path.dirname(__file__)
    boardpath = os.path.join(currentpath, "../../../../config_templates/board_layout")
    boardfiles = glob.glob(os.path.join(os.path.abspath(boardpath), "*.json"))
    boardnames = [pathlib.Path(os.path.basename(x)).stem for x in boardfiles]
