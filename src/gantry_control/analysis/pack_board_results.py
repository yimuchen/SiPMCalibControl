"""

Collecting the files of a board calibration session and packing the results into
a tarball for detailed analysis uses. (This should *not* require a session to be
loaded, just the file to the tarball)

"""

import os
import shutil
import tarfile

import gantry_control.cli.board as brd
from gantry_control.cli.format import _timestamp_


def pack_board_results(board_file, remove_old=False):
    """
    Flatten out the structure of the of the stored file into the format of

    boardtype_boardid_{timestamp}
    """
    if board_file.startswith("+"):
        board = brd.Board.auto_resolve_jsonfile(board_file)
    else:
        board = brd.Board.from_json(board_file)

    # Creating the base directory
    base_dir = "{board_type}_{board_id}_{timestamp}".format(
        board_type=board.board_type,
        board_id=board.id_unique,
        timestamp=_timestamp_(),
    )
    os.mkdir(base_dir)

    # List of files to be copied
    old_files = []

    def make_new_filename(filename):
        return os.path.join(base_dir, os.path.basename(filename))

    # Copying the various calibration of individual detectors to file
    for det in board.detectors:
        for res in det.calibrated:
            old_files.append(res.file)
            shutil.copy(res.file, make_new_filename(res.file))
            res.file = make_new_filename(res.file)

    # Writing the modified board results to the directory
    old_files.append(board.filename)
    board.save_board(make_new_filename(board.filename))

    # Making the tarball
    with tarfile.open(base_dir + ".tar.gz", "w:gz") as tar:
        for file in os.listdir(base_dir):
            tar.add(os.path.join(base_dir, file))

    # Removing items in the dir
    shutil.rmtree(base_dir)
    if remove_old:
        for f in old_files:
            os.remove(f)


if __name__ == "__main__":
    pack_board_results("+simple_test_board@123456", True)
