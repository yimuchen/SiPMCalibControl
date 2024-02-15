"""

savefile.py

Methods and handlers for saving the root files.

For usual analysis operations, we will save 2 trees:

- A run-level item, for which there is essentially have a single entry per
  branch. This will be used to log the information that is used for producing
  the file in question

- A per-extraction level item: where along with the primary data of interests,
  we will also add standard monitoring entries.

Both trees will be handled by a dictionary of numpy arrays and will be written
using uproot. The functions in this module provides standardized method to
create dictionary and update the entries to contain the standard methods.

"""

from .session import Session
from .format import _timestamp_

from typing import Dict, List, Iterable
import argparse
import uproot
import numpy
import string


def add_save_args(args: argparse.ArgumentParser) -> argparse.ArgumentParser:
    args.add_argument(
        "--rootfile",
        type=str,
        help="File path to save files to. Use '{arg}' to add argument results to the file name",
    )
    return args


def parse_save_args(session, args: argparse.Namespace) -> argparse.Namespace:
    """Keeping for parity"""
    assert args.rootfile, "Root save file needs to be specified"
    key_list = [
        k[1] for k in string.Formatter().parse(args.rootfile) if k[1] is not None
    ]
    if len(key_list):
        format_args = {k: getattr(args, k) for k in key_list if hasattr(args, k)}
        if "timestamp" in key_list:
            format_args.update({"timestamp": _timestamp_()})
        args.rootfile = args.rootfile.format(**format_args)
    return args


def create_run_dict(session: Session, **kwargs):
    return {
        "board_id": session.board.id_unique,
        "board_type": session.board.board_type,
        "timestamp": _timestamp_(),
        **kwargs,
    }


def save_run_dict(
    f: uproot.writing.writable.WritableDirectory,
    run_dict: Dict,
    tree_name: str = "runinfo",
):
    pass


def create_save_dict(*args):
    return {
        "led_lv": [],
        "led_hv": [],
        "led_temp": [],
        "det_temp": [],
        "det_hv": [],
        "gantry_coord": [],
        **{x: [] for x in args},
    }


def update_save_dict(session, save_dict: Dict[str, List], **kwargs) -> Dict[str, List]:
    """Update the standard dictionary"""
    save_dict["led_lv"].append(session.hw.get_ledlv())
    save_dict["led_hv"].append(session.hw.get_ledhv())
    save_dict["led_temp"].append(session.hw.get_ledtemp())
    save_dict["det_temp"].append(session.hw.get_dettemp())
    save_dict["det_hv"].append(session.hw.get_dethv())
    save_dict["gantry_coord"].append(session.hw.get_coord())
    for key, values in kwargs.items():
        save_dict[key].append(values)
    return save_dict


def save_to_root(
    file_name: str,
    run_dict: Dict,
    save_dict: Dict[str, Iterable],
    run_tree: str = "runinfo",
    save_tree: str = "results",
):
    """
    The `run_dict` every instance in the run_dict will need to be wrapped as a
    single length array. Additional handling will need to done for "string"
    entries as uproot supports string arrays (Corresponding read-back is handled
    in the `read_root` function)
    """

    def _run_dict_value_cast(v):
        if isinstance(v, str):
            return [numpy.array(list(v)).view(numpy.int8)]
        else:
            return [v]

    with uproot.recreate(file_name) as f:
        f[run_tree] = {k: _run_dict_value_cast(v) for k, v in run_dict.items()}
        f[save_tree] = save_dict


def read_root(filename: str, run_tree: str = "runinfo", save_tree: str = "results"):
    """
    Returning the run_dict and save_dict used to save to a tree. Reversing the
    string collapsing operation to help with the setting.
    """

    def _run_dict_cast_array(v):
        if v.dtype == numpy.int8:
            return ["".join(x.view("U1")) for x in v]
        else:
            return v

    with uproot.open(filename) as f:
        run_arr = f[run_tree].array(library="np")
        run_dict = {k: _run_dict_cast_array(v) for k, v in run_arr.items()}
        save_dict = f[save_tree]

    return run_dict, save_dict
