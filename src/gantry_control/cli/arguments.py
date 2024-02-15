"""
Argument for running the control hardware system.

Control functions should be in the following take the following arguments

- session: a container which stores session information (loaded from the file
  structure), and various control interfaces.
- **kwargs: all other arguments should be handled as kwargs, so that the
  argument can either be constructed either from raw python parsing, or from the
  python in-built argparse.ArgumentParser return `NameSpace object`

File files contains the following methods:

- An additional parse_cli_args function for converting command line arguments,
  and converts it into a python dictionary to be passed to control functions as
  function arguments. This function should be used in-place of the standard
  argparse.ArgumentParser.parse_args method for simpler interface with the
  various operation functions. This function takes in:

  - session, (since processes are expected to be loaded as a session)
  - The cli input arguments (list of strings)
  - The argparse instance used to define the various options
  - A list of function for additional parsing. These function functions should
    take in the should also follow the following format

    - session: the container which stores the session information
    - The return of these functions should still be a argparse.Namespace object
      such that the functions can be chained together for compound parsing

  Notice that this interface is mainly reserved for session-dependent function
  argument determination (operations that requires parsing dependent on ongoing
  or existing gantry results). Simple functions (such as adjustment to single
  hardware) should be handled by directly interacting with the hardware
  controller client.


- Common argument parsing routines. This is used for the functions
"""
import argparse  # For function argument parsing
from typing import Dict, List, Callable, Optional, Any

from .session import Session
from .format import _str_
import numpy


def create_cli_parser(
    single_det: bool, cli_args_list: List[Callable], **kwargs
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(**kwargs)
    if single_det:
        parser.add_argument(
            "--detid",
            type=int,
            required=True,
            help="Detector ID used for this calibration process",
        )
    for f in cli_args_list:
        f(parser)
    return parser


def update_parser_default(parser: argparse.ArgumentParser, **kwargs):
    """
    Updating the default values of the various arguments. We are assuming that
    the argument are created with a StoreAction instance, so it can then be set
    after the fact.
    """
    for action in parser._actions:
        if action.dest in kwargs.keys():
            action.default = kwargs[action.dest]
    return parser


def parse_cli_args(
    session: Session,
    cli_args: List[str],
    parser: argparse.ArgumentParser,
    post_processes: Optional[List[Callable]] = None,
) -> Dict[str, Any]:
    """
    Simple chaining of argument parsing functions.
    """
    try:
        args = parser.parse_args(cli_args)
        if post_processes is not None:
            for process in post_processes:
                args = process(session, args)
    except Exception as err:
        parser.print_help()
        raise err
    return args.__dict__


"""

COMMON ARGUMENTS AND ACCOMPANYING PARSING ROUTINES

"""


def add_visual_args(parser: argparse.ArgumentParser):
    """Arguments for visual processing algorithm parameters"""
    import gmqclient.camera_methods as cm

    group = parser.add_argument_group(
        title="Visual processing algorithm arguments",
        description=_str_(
            """
            Function arguments to be used for the visual processing algorithm.
            Details for how the visual processing algorithm is defined can be
            found in the gmqclient.camera_methods module.
            """
        ),
    )
    group.add_argument(
        "--visalgo_blur",
        type=int,
        default=cm.VISALGO_BLUR_DEFAULT,
        help="Blur kernel size before contouring [pixels]",
    )
    group.add_argument(
        "--visalgo_threshold",
        type=float,
        default=cm.VISALGO_THRESHOLD_DEFAULT,
        help="Grayscale threshold for contouring [0-255]",
    )
    group.add_argument(
        "--visalgo_maxlumi",
        type=float,
        default=cm.VISALGO_MAXLUMI_DEFAULT,
        help="Maximum luminosity of candidate contour [0-255]",
    )
    group.add_argument(
        "--visalgo_minsize",
        type=int,
        default=cm.VISALGO_MINSIZE_DEFAULT,
        help="Minimum size of candidate contour [pixels]",
    )
    group.add_argument(
        "--visalgo_maxratio",
        type=float,
        default=cm.VISALGO_MAXRATIO_DEFAULT,
        help="Maximum x-y ratio of candidate contour (>1)",
    )
    group.add_argument(
        "--visalgo_polyeps",
        type=float,
        default=cm.VISALGO_POLYEPS_DEFAULT,
        help="Relative tolerance for polygon approximation (0, 1)",
    )
    return parser


def parse_visual_args(
    session: Session, args: argparse.Namespace  # TODO
) -> argparse.Namespace:
    """Checking algorithm input range"""
    assert 0 < args.visalgo_blur, "Blur range must be > 0"
    assert 0 <= args.visalgo_threshold <= 255, "Threshold must be between 0-255"
    assert 0 <= args.visalgo_maxlumi <= 255, "Lumi cutoff must be between 0-255"
    assert 0 < args.visalgo_minsize, "Minimum size must be > 0"
    assert 1 < args.visalgo_maxratio, "Ratio cutoff must be > 1"
    assert 0 < args.visalgo_polyeps < 1, "Tolerance must be between 0-1"
    return args


"""

Getting the association function used for the central operation point

"""


def add_xy_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    group = parser.add_argument_group(
        "horizontal position",
        "Options for specifying the operation postion in the x-y coordinates.",
    )
    group.add_argument(
        "--x", type=float, help="Specifying the x coordinate explicitly [mm]."
    )
    group.add_argument(
        "--y", type=float, help="Specifying the y coordinate explicitly [mm]."
    )
    return parser


def parse_lumi_xy_args(
    session: Session, args: argparse.Namespace
) -> argparse.Namespace:
    """
    @brief Modifying the args.x args.y and args.detid values.

    @details If the detector is not specified, then we are using the directly
    using the provided x/y coordinates or the override with the current position.
    The detector ID, in this case, will alway be assigned to -100 (default
    calibration detector ID)

    If the detector is specified: We check if the detector exists in the current
    detector list. If not an exception is raised. If yes then we attempt to look
    up the x/y coordinates according to the target z position. The target z
    position is defined as follow:
    - If the args has a single z argument, then that is used.
    - If the args has a list of z arguments, then the minimal is used.
    - If neither is present, then the current z position is used.

    If the visual offset flag is True, then the look up sequence will be:
    - Direct visual calibrated coordinates.
    - Luminosity aligned cooridnates with visual offset added
    - Original coordinates with visual offset added

    If the visual offset flag is set to false, then the look up sequence will be:
    - Luminosity aligned alibrated coordinates.
    - Visual calibrated cooridnates with visual offset subtracted.
    - The original cooridnates.

    After parsing the return `args` object will always have `args.x`, `args.y`
    and `args.detid` attributes properly assigned.
    """
    if not args.detid in range(len(session.board.detectors)):
        raise ValueError(f"Det id was not specified in board type.")

    if args.x or args.y:
        session.logger.warn("Directly using user defined values")
        return args
    det = session.board.detectors[args.detid]

    current_z = _find_z(session, args)
    if det.get_latest_calibrated("halign") is not None:
        closest_z = det.get_closest_z("halign", current_z)
        lumi_res = det.get_lumi_coord(closest_z)
        args.x, args.y = lumi_res.fit_x, lumi_res.fit_y
    elif det.get_latest_calibrated("visualcenterdet") is not None:
        x_offset, y_offset = _find_xyoffset(session, current_z)
        closest_z = session.board.get_closest_calib_z(
            args.detid, "visualcenterdet", current_z
        )
        coord = session.board.get_vis_coord(args.detid, closest_z)["data"][
            "coordinates"
        ]
        args.x = coord[0] - x_offset
        args.y = coord[1] - y_offset
    else:
        args.x, args.y = det.default_coords

    return args


def parse_vis_xy_args(session: Session, args: argparse.Namespace) -> argparse.Namespace:
    if not args.detid in range(len(session.board.detectors)):
        raise ValueError(f"Det id was not specified in board type.")

    if args.x or args.y:
        session.logger.warn("Directly using user defined values")
        return args

    current_z = _find_z(session, args)
    if self.board.get_latest_entry(args.detid, "visualcenterdet") is not None:
        closest_z = session.board.get_closest_calib_z(
            args.detid, "visualcenterdet", current_z
        )
        coord = session.board.get_vis_coord(args.detid, closest_z)["data"][
            "coordinates"
        ]
        args.x, args.y = coord[0], coord[1]
    elif session.board.get_latest_entry(args.detid, "halign") is not None:
        closest_z = session.board.get_closest_calib_z(args.detid, "halign", current_z)
        x_offset, y_offset = session.find_xyoffset(current_z)
        coord = session.board.get_lumi_coord(args.detid, closest_z)["data"][
            "coordinates"
        ]
        args.x = coord[0] + x_offset
        args.y = coord[2] + y_offset
    else:
        x_offset, y_offset = self.find_xyoffset(current_z)
        args.x = det["coordinates"]["default"][0] + x_offset
        args.y = det["coordinates"]["default"][1] + y_offset

    return args


def _find_z(session: Session, args: argparse.Namespace) -> float:
    if hasattr(args, "z") and args.z is not None:
        return args.z
    if hasattr(args, "scanz") and args.scanz is not None:
        return args.scanz
    if hasattr(args, "zlist"):
        return np.min(args.zlist)
    return session.hw.gantry_coord[2]


DEFAULT_X_OFFSET = 40
DEFAULT_Y_OFFSET = 0


def _find_xyoffset(session: Session, current_z: float) -> float:
    """
    @brief Determining the luminosity/visual alignment offset values.

    @details First we loop over all the detectors, and finding if there are any
    detector that has the lumi_vis_separation. If multiple are found, then the
    "first" detector is used. If no such detectors are found, a default value
    will be used.
    """

    for detid in range(len(session.board.detectors)):
        closest_z = session.board.get_closest_calib_z(
            detid, "lumi_vis_separation", current_z
        )
        lumi_vis_separation = session.board.get_lumi_vis_separation(detid, closest_z)

        if lumi_vis_separation is not None:
            return (
                lumi_vis_separation["data"]["separation"][0],
                lumi_vis_separation["data"]["separation"][1],
            )

    return DEFAULT_X_OFFSET, DEFAULT_Y_OFFSET


"""

Horizontal scanning arguments

"""


def add_hscan_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    group = parser.add_argument_group(
        "grid options", "options for setting up x-y grid scanning coordinates"
    )
    group.add_argument(
        "--scanz", type=float, help="Height to perform horizontal scan [mm]."
    )
    group.add_argument("--range", type=float, help="Range from central position [mm]")
    group.add_argument(
        "--distance", type=float, help="Horizontal sampling distance [mm]"
    )
    return parser


def parse_hscan_args(session: Session, args: argparse.Namespace) -> argparse.Namespace:
    max_x = session.max_x
    max_y = session.max_y

    if (
        args.x - args.range < 0
        or args.x + args.range > session.max_x
        or args.y - args.range < 0
        or args.y + args.range > session.max_y
    ):
        session.logger.warn(
            _str_(
                """
                The arguments placed will put the gantry past its limits, the
                command will used modified input parameters"""
            )
        )

    xmin = max([args.x - args.range, 0])
    xmax = min([args.x + args.range, max_x])
    ymin = max([args.y - args.range, 0])
    ymax = min([args.y + args.range, max_y])
    sep = max([args.distance, 0.1])
    numx = int((xmax - xmin) / sep + 1)
    numy = int((ymax - ymin) / sep + 1)
    args.x = numpy.linspace(xmin, xmax, numx)
    args.y = numpy.linspace(ymin, ymax, numy)
    return args


"""

Z scanning arguments

"""


def add_scanz_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    group = parser.add_argument_group("Arguments for scanning in z")
    group.add_argument(
        "-z",
        "--zlist",
        type=float,
        nargs="+",
        help="List of z coordinate to perform scanning",
    )
    return argparse


def parse_scanz_args(session: Session, args: argparse.Namespace) -> argparse.Namespace:
    args.zlist = np.sort(np.unique(np.around(args.zlist, decimals=1)))
    # Additional Making sure that no objects are used for functions
    args.zlist = args.zlist[args.zlist < session._max_z]

    return args


if __name__ == "__main__":

    def mytest(test, **kwargs):
        print("Calling test function")
        print(test)
        return test * 3

    import sys

    parser = argparse.ArgumentParser("arguments")
    parser.add_argument("--test", help="this is a test", type=int)
    parser.add_argument("--test2", help="this is a test", type=int)

    args = parse_cli_args(None, None, sys.argv[1:], parser)
    print(mytest(**args))
