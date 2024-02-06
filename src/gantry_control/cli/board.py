"""

_board.py

Python classes used to handling detector layout and board configurations, to
keep track of the existing calibration process results.
"""
import datetime
import enum
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .format import (_str_, _timestamp_, _timestamp_fmt_, _value_rounding,
                     str_to_time, time_to_str)

TEMPLATE_DIR = os.path.abspath("calib_progress/templates/")
DEFAULT_STORE_PATH = os.path.abspath("calib_progress/default_store")


#### TEMPLATE DIRECTORY #####
def __run_dir_check__():
    if os.path.isdir(TEMPLATE_DIR):
        raise ValueError(
            _str_(
                f"""
                Template directory [{TEMPLATE_DIR}] not found! You probably
                need to run the script
                [SiPMCalibControl/scripts/make_directories.py]
                """
            )
        )
    if os.path.isdir(DEFAULT_STORE_PATH):
        raise ValueError(
            _str_(
                f"""
                Default storage directory [{DEFAULT_STORE_PATH}] not found! You
                probably need to run the script
                [SiPMCalibControl/scripts/make_directories.py]
                """
            )
        )


@dataclass
class CalibratedResult:
    """
    Generated entry for summarizing calibration results, the core results will
    all be stored in the "data" entry. Specialized inheritance classes will be
    used for user-friendly translation of the results. Inheritance should never
    attempt to extend the data entries.
    """

    process: str = ""
    file: str = ""
    timestamp: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now()
    )
    data: List[float] = field(default_factory=lambda: [])

    @classmethod
    def from_jsonmap(cls, jsonmap):
        """
        Constructing and auto-casting when reading results from file
        """
        __class_map__ = {"halign": HAlignResult}
        res = __class_map__.get(jsonmap["process"], CalibratedResult)(
            **{
                **jsonmap,
                **{"timestamp": str_to_time(jsonmap.get("timestamp"))},
            }
        )
        res.check_data()  # Run additional format checking.
        return res

    def check_data(self):
        pass

    def to_json(self):
        return {**self.__dict__, **dict(timestamp=time_to_str(self.timestamp))}


class HAlignResult(CalibratedResult):
    """
    Horizontal lumi scan results. The data format stored is:
    - 0, the z value used to obtain the results
    - 1, the best fitted x value
    - 2, the uncertainty in the fitted x result
    - 3, the best fitted y value
    - 4, the uncertainty in the fitted y result
    """

    @property
    def process_z(self):
        return self.data[0]

    @property
    def fit_x(self):
        return self.data[1]

    @property
    def fit_xerr(self):
        return self.data[2]

    @property
    def fit_y(self):
        return self.data[3]

    @property
    def fit_yerr(self):
        return self.data[4]

    def check_data(self):
        assert self.process == "halign"
        # Must contain 5 entries
        assert len(self.data) == 5

    def is_overlap(self, other) -> bool:
        if isinstance(other, HAlignResult):
            return _value_rounding(self.process_z) == _value_rounding(other.process_z)
        elif isinstance(other, float):
            return _value_rounding(self.process_z) == other
        else:
            False


class ReadoutMode(enum.Enum):
    DRS = 0
    ADC = 1
    Tileboard = 2
    Model = -1


_CHANNEL_RANGE_ = {
    ReadoutMode.DRS.value: range(0, 4),
    ReadoutMode.ADC.value: range(0, 4),
    ReadoutMode.Tileboard.value: range(0, 72),
}


@dataclass
class Detector(object):
    """
    A detector element is defined as an object with a specific readout mode, a
    set of default x-y coordinates. And a list of per-device calibrated
    results.
    """

    # Read out method/channel
    readout: Tuple[int, int] = (-3, 0)
    default_coords: Tuple[float, float] = (0, 0)
    calibrated: List[CalibratedResult] = field(default_factory=lambda: [])

    @classmethod
    def from_json(cls, jsonmap):
        det = Detector(
            **{
                **jsonmap,
                **dict(
                    calibrated=[
                        CalibratedResult.from_jsonmap(x)
                        for x in jsonmap.get("calibrated", [])
                    ]
                ),
            }
        )

        return det

    def to_json(self):
        return {
            **self.__dict__,
            **{"calibrated": [x.to_json() for x in self.calibrated]},
        }

    def get_latest_calibrated(self, process: str, key=None):
        """
        Getting the latest calibration result of a particular process. The key argument
        can be used to specify a function to order the processes of interest.
        """
        # Getting the latest calibrated result, of a particular process. The key
        # can be used to specify th
        process_list = [x for x in self.calibrated if x.process == process]

        if len(process_list) == 0:
            return None
        elif key is None:
            return process_list[-1]
        else:
            return sorted(process_list, key=key)[0]

    # Adding the per detector calibration results
    def _add_lumi_result(
        self,
        file: str,
        z: float,
        fit_x: float,
        fit_xerr: float,
        fit_y: float,
        fit_yerr: float,
    ) -> HAlignResult:
        res = HAlignResult(
            process="halign",
            file=file,
            data=[z, fit_x, fit_xerr, fit_y, fit_yerr],
        )
        self.calibrated = [x for x in self.calibrated if not x.is_overlap(res)]
        self.calibrated.append(res)
        return self.calibrated[-1]

    def get_lumi_coord(self, z: None):
        # TODO: properly fix z ordering
        return self.get_latest_calibrated("halign", key=None)

    def has_lumi_overlap(self, z: float) -> bool:
        return (
            len(
                [
                    x
                    for x in self.calibrated
                    if x.process == "halign" and x.is_overlap(z)
                ]
            )
            > 0
        )
        return len(l) > 0

    @property
    def mode(self):
        return self.readout[0]

    @property
    def channel(self):
        return self.readout[1]

    @property
    def is_counting(self):
        return self.readout[2]

    def get_closest_z(self, process, current_z):
        """
        The calibrated process with z value closest to the target z value
        """
        z_list = [c.process_z for c in self.calibrated if c.process == process]
        return min(z_list, key=lambda x: abs(float(x) - float(current_z)))


@dataclass
class Board(object):
    """
    Class for storing a board configuration which includes:
    - A list of detectors (see the Detector object)
    - A list of conditions (see the Conditions object) calib.
    routines and board conditions.
    """

    filename: str = ""
    board_type: str = ""
    description: str = ""
    id_unique: int = -1
    detectors: List[Detector] = field(default_factory=lambda: [])
    # This is for the board conditions (ex. pedestal/timing settings... etc)
    calib_routines: List = field(default_factory=lambda: [])
    conditions: Dict = field(default_factory=lambda: {})

    def clear(self):
        self.filename = ""
        self.board_type = ""
        self.description = ""
        self.id_unique = -1
        self.detectors = []
        self.calib_routines = []
        self.conditions = {}

    @classmethod
    def from_json(cls, json_file):
        """Loading from a file"""
        jsonmap = json.load(open(json_file, "r"))
        b = Board(
            **{
                **jsonmap,
                **dict(detectors=[Detector.from_json(x) for x in jsonmap["detectors"]]),
            }
        )

        # Addition parsing to make sure some entries are present
        assert b.board_type != "", "Board type needs to be specified"
        assert len(b.detectors) > 0, "At least 1 detector needs to be specified"
        assert b.description != "", "Board should have a description"

        b.filename = json_file

        return b

    @classmethod
    def auto_resolve_jsonfile(cls, target: str) -> str:
        """
        "+<board>@<id>" to find latest board in the default store location.
        "++<board>@<id>" to spawn a new session board from template
        """
        if target.startswith("++"):
            if "@" in target:
                board_type, board_id = target.split("@")
                board_type = board_type.lstrip("+")
            else:
                raise ValueError(
                    "board id must be specified with the ++<board_type>@<board_id> format"
                )
            layout_path = os.path.join(TEMPLATE_DIR, "board_layout")
            board_files = [
                os.path.join(layout_path, x)
                for x in os.listdir(layout_path)
                if x == f"{board_type}.json"
            ]
            if len(board_files) == 0:
                raise ValueError(
                    f"No template of board type {board_type} found in {layout_path}"
                )
            else:
                board = Board.from_json(board_files[0])
                board.id_unique = int(board_id)
                return board

        elif target.startswith("+"):
            if "@" in target:
                board_type, board_id = target.split("@")
                board_type = board_type.lstrip("+")
            else:
                raise ValueError(
                    "board id must be specified with the +<board_type>@<board_id> format"
                )
            board_files = [
                os.path.join(DEFAULT_STORE_PATH, x)
                for x in os.listdir(DEFAULT_STORE_PATH)
                if x.startswith(board_type) and x.endswith(".json")
            ]
            if board_id:  # Additional board type parsing
                board_files = [
                    x for x in board_files if f"_{board_id}_" in os.path.basename(x)
                ]

            # Getting the latest assuming standard time stamp notation
            board_files.sort(
                key=lambda x: str_to_time(
                    os.path.basename(x).split("_")[-1].replace(".json", "")
                )
            )
            if len(board_files):
                board = Board.from_json(board_files[-1])
                return board
            else:
                return cls.auto_resolve_jsonfile(target="+" + target)
        else:
            raise ValueError(
                "Auto resolution must have target either in ++<board_type>@<board_id> or +<board_type>[@board_id]"
            )

    def to_json(self):
        return {
            **self.__dict__,
            **dict(detectors=[x.to_json() for x in self.detectors]),
        }

    def save_board(self, filename: str = ""):
        if filename != "":
            self.filename = filename

        # TODO: Filename renaming to avoid overriding template files
        if self.filename == "" or "templates" in self.filename:
            self.filename = os.path.join(
                DEFAULT_STORE_PATH,
                "_".join([self.board_type, str(self.id_unique), _timestamp_()])
                + ".json",
            )

        with open(self.filename, "w") as f:
            f.write(json.dumps(self.to_json(), indent=2))

    @property
    def detid_list(self):
        return range(len(self.detectors))

    def update_lumi_results(self, detid, *args, **kwargs):
        self.detectors[detid]._add_lumi_result(*args, **kwargs)
        self.save_board()

    # Get/Set calibration measures with additional parsing
    def add_vis_coord(self, detid, z, data, filename):
        self.detectors[detid].coordinates["calibrated"].append(
            {
                "command": "visualcenterdet",
                "z": self.roundz(z),
                "data": {"coordinates": data, "file": filename},
            }
        )

        self.save_board()

    def add_visM(self, detid, z, data, filename):
        self.detectors[detid].coordinates["calibrated"].append(
            {
                "command": "visualhscan",
                "z": self.roundz(z),
                "data": {"transform": data, "file": filename},
            }
        )

        self.save_board()

    def get_vis_coord(self, detid, z):
        return self.get_latest_entry(detid, "visualcenterdet", z)

    def get_visM(self, detid, z):
        return self.get_latest_entry(detid, "visualhscan", z)

    def get_lumi_vis_separation(self, detid, z):
        return self.get_latest_entry(detid, "lumi_vis_separation", z)

    def add_lumi_vis_separation(self, detid, z, h):
        self.detectors[detid - 1].coordinates["calibrated"].append(
            {
                "command": "lumi_vis_separation",
                "z": self.roundz(z),
                "data": {"separation": h},
            }
        )

        self.save_board()

    def empty(self):
        for detid in range(0, len(self.detectors)):
            if (
                self.get_latest_entry(detid, "visualcenterdet") is not None
                or self.get_latest_entry(detid, "visualhscan") is not None
                or self.get_latest_entry(detid, "halign") is not None
            ):
                return False
        return True

    @staticmethod
    def roundz(rawz):
        return round(rawz, 1)


@dataclass
class Conditions:
    """
    Container class for storing the gantry conditions (used to extrapolate for
    rapid calibration)
    """

    filename: str = ""
    fov_transformation: Dict = field(default_factory=lambda: {})
    fov_lumi_mismatch: Dict = field(default_factory=lambda: {})
    use_count: int = 0
    mismatch_history: List = field(default_factory=lambda: [])

    @classmethod
    def from_json(cls, filename):
        cond = Conditions(**json.load(open(filename, "r")))
        cond.mismatch_history = [cond.fov_lumi_mismatch["data"]["separation"]]
        return cond

    def __dict__(self):
        return dict(
            fov_transformation=self.fov_transformation,
            fov_lumi_mismatch=self.fov_lumi_mismatch,
            use_count=self.use_count,
        )

    # saves gantry conditions to a file
    def save_json(self, filename=""):
        if filename != "":
            self.filename = filename
        if self.filename == "":
            self.timestamp_filename()

        with open(self.filename, "w") as f:
            self.use_count += 1
            f.write(json.dumps(self.__dict__(), indent=2))

    def is_h_valid(self, h, tolerance):
        """
        Checks if the h value is within tolerance of the h values in the h_list
        """
        for h_i in self.mismatch_history:
            if abs(h_i - h) > tolerance:
                return False
        return True

    # define get, calculate functions for the data quality(long term) conditions and the board conditions
    def get_board_conditions(self):
        pass

    def calculate_board_conditions(self):
        pass

    # TODO: a function to load data quality(long term) conditions from a file
    # TODO: a function to save data quality(long term) conditions to a file
    # TODO: a getter for the data quality(long term) conditions
    # TODO: implement the data quality(long term) conditions calculation
    def get_data_quality_conditions(self):
        pass

    def calculate_data_quality_conditions(self):
        pass

    @classmethod
    def save_directory(cls):
        """
        Making the string represent the gantry conditions storage directory.
        """
        return "calib_progress/default_store/"

    def timestamp_filename(self) -> str:
        """
        Returning the string corresponding to the filename for a new set of
        gantry conditions.
        """
        self.filename = os.path.join(
            self.save_directory(), f"{_timestamp_()}.json")
        return self.filename

    @classmethod
    def latest_conditions_filename(cls) -> Optional[str]:
        """
        Returning the string corresponding to the filename for the latest set
        of gantry conditions.
        """
        file_names = os.listdir(cls.save_directory())
        # sort the file names by date if the format ofd the filename is '%Y%m%d-%H%M'.json
        if len(file_names) > 0:
            return sorted(
                file_names,
                key=lambda x: datetime.datetime.strptime(
                    os.path.basename(x), f"{_timestamp_fmt_}.json"
                ),
            )[-1]
        else:
            return None


"""

Synchronized update methods for both boards and conditions

"""


def update_gantry_conditions(
    cmd_name: str, cond: Conditions, board: Board, detid: int, z: float
):
    __look_up__ = {
        "visualcenterdet": _update_viscenter,
        "halign": _update_halign,
        "visualhscan": _update_vishscan,
    }

    def _unrecognized(*args):
        raise ValueError(f"Unrecognized conditions update command {cmd_name}")

    __look_up__.get(cmd_name, _unrecognized)(cond, board, detid, z)
    cond.save_json()  # Always save the conditions


def _update_viscenter(cond: Conditions, board: Board, detid: int, z: float):
    if board.detectors[detid].get_latest_calibrated("halign"):
        _update_separation(cond, board, detid, z)


def _update_halign(cond: Conditions, board: Board, detid: int, z: float):
    if board.detectors[detid].get_latest_calibrated("visualcenterdet"):
        _update_separation(cond, board, detid, z)


def _update_separation(cond: Conditions, board: Board, detid: int, z: float):
    h = board.get_lumi_coord(detid, z) - board.get_vis_coord(detid, z)
    board.add_lumi_vis_separation(detid, z, h)

    # check if we have multiple H values out of tolerance with each other,
    if cond.is_h_valid(h, 0.5):
        cond.fov_lumi_mismatch["separation"] = (
            (cond.fov_lumi_mismatch["separation"] * len(cond.h_list)) + h
        ) / (len(cond.h_list) + 1)
        cond.h_list.append(h)
    else:
        # TODO: An error should be raised (?) such that the operator knows that
        # something is wrong (maybe the gantry head dislodged or was tugged
        pass


def _update_vishscan(cond: Conditions, board: Board, detid: int, z: float):
    visM = board.get_visM(detid, z=z)
    cond.fov_transformation["z"] = visM["z"]
    cond.fov_transformation["transform"] = visM["data"]["transform"]
