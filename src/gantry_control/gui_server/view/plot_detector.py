import awkward
import hist
import uproot

from ...cli.board import Board
from ..session import GUISession


def plot_pedestal(session: GUISession, detid: int):
    routine = [
        routine
        for routine in session.board.board_routines
        if routine.process == "pedestal"
    ]
    assert len(routine) > 0, "Calibration routine not found"
    assert len(routine) == 1, "More than 1 routine found"
    datafile = routine[0].datafile

    with uproot.open(datafile) as f:
        arr = f["unpacker_data/hgcroc"].arrays()
        adc = arr.adc[arr.channel == session.board.detectors[detid].readout[1]]
        min, max = awkward.min(adc), awkward.max(adc)
        h = hist.Hist(hist.axis.Integer(min, max))
        h.fill(adc)

    return [list(h.axes[0].edges), list(h.view())]
