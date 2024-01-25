"""

lumi_hscan.py

Method for scanning the detector center

"""

import time
from typing import Tuple

import numpy as np
import scipy.optimize

import gantry_control.cli as control_cli


def _model_profile(xydata, N, x0, y0, z, p):
    """Inverse square model used for fitting"""
    x, y = xydata
    D = (x - x0) ** 2 + (y - y0) ** 2 + z**2
    return (N * z / D**1.5) + p


def lumi_hscan(
    session: control_cli.session.Session, **kwargs
) -> Tuple[np.ndarray, np.ndarray]:
    # Getting the arguments that are unique to the primary command
    x = kwargs.get("x")
    y = kwargs.get("y")
    z = kwargs.get("scanz")
    rootfile = kwargs.get("rootfile")

    # Preparing the results regardless
    run_dict = control_cli.saveroot.create_run_dict(session, run_process="lumi_hscan")
    save_dict = control_cli.saveroot.create_save_dict("lumi", "unc")

    # Obtained data over meshgrid
    try:
        for _x, _y in session.make_progress_bar(control_cli.format.loop_mesh(x, y)):
            session.hw.move_to(x=_x, y=_y, z=z)
            lumi, unc = control_cli.readout.obtain_readout(
                session, average=True, **kwargs
            )
            control_cli.saveroot.update_save_dict(
                session, save_dict, lumi=lumi, unc=unc
            )
            session.update_pbar_data(lumi=f"{lumi:.2f}+-{unc:.2f}")

        # Running the fit
        p0 = (
            np.max(save_dict["lumi"]) * (z + 2) * (z + 2),
            np.mean(x),
            np.mean(y),
            z,
            np.min(save_dict["lumi"]),
        )
        fit_val, fit_covar = scipy.optimize.curve_fit(
            _model_profile,
            control_cli.format.loop_mesh(x, y).T,
            save_dict["lumi"],
            p0=p0,
            sigma=save_dict["unc"],
            maxfev=1000000,
        )

        run_dict["fit_x"] = fit_val[1], np.sqrt(fit_covar[1][1])
        run_dict["fit_y"] = fit_val[2], np.sqrt(fit_covar[2][2])
    except Exception as err:
        # Move back to central value before re-raising the error
        session.hw.move_to(x=np.mean(x), y=np.mean(y), z=z)
        raise err
    finally:  # Always save the results to what was obtained
        control_cli.saveroot.save_to_root(rootfile, run_dict, save_dict)

    return fit_val, fit_covar


def lumi_hscan_updating(
    session: control_cli.session.Session, interactive: bool = True, **kwargs
):
    # Parsing the kwargs requirements
    detid = kwargs.get("detid")
    fit_x = kwargs.get("fit_x")
    fit_y = kwargs.get("fit_y")
    z = kwargs.get("scanz")
    file = kwargs.get("rootfile")
    # Saving session information
    coords = (fit_x, fit_y)

    def _update():
        session.board.update_lumi_results(detid, file, z, *fit_x, *fit_y)
        control_cli.board.update_gantry_conditions(
            "halign", session.conditions, session.board, detid, z
        )

    if session.board.detectors[detid].has_lumi_overlap(z):
        if interactive:
            if control_cli.format.prompt_yn(
                f"""
                Detector element {detid} already has results for `halign` at
                z-height {z}, do you want to over-write?""",
                default=False,
            ):
                _update()
    else:
        _update()


if __name__ == "__main__":
    import logging
    import os
    import sys

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)

    parser = control_cli.arguments.create_cli_parser(
        single_det=True,
        cli_args_list=[
            control_cli.session.add_session_args,
            control_cli.arguments.add_xy_args,
            control_cli.arguments.add_hscan_args,
            control_cli.readout.add_readout_args,
            control_cli.saveroot.add_save_args,
        ],
        prog="lumi_hscan",
        description="Determining the horizontal position of detector elements using a horizontal scan",
    )
    parser = control_cli.arguments.update_parser_default(
        parser,
        scanz=20,
        range=20,
        distance=1,
        rootfile=os.path.join(
            control_cli.board.DEFAULT_STORE_PATH, "halign_{timestamp}.root"
        ),
    )

    session = control_cli.session.load_blank_session(
        logger=logging.Logger("lumi_hscan")
    )

    args = control_cli.arguments.parse_cli_args(
        session,
        cli_args=sys.argv[1:],
        parser=parser,
        post_processes=[
            control_cli.session.parse_session_args,
            control_cli.arguments.parse_lumi_xy_args,
            control_cli.arguments.parse_hscan_args,
            control_cli.readout.parse_readout_args,
            control_cli.saveroot.parse_save_args,
        ],
    )
    # Running the data extraction process
    fit_val, fit_covar = lumi_hscan(session, **args)

    fit_x = (fit_val[1], np.sqrt(fit_covar[1][1]))
    fit_y = (fit_val[2], np.sqrt(fit_covar[2][2]))
    fit_z = (fit_val[3], np.sqrt(fit_covar[3][3]))

    # Mini results display
    session.logger.info("Best x: {c:.1f}+-{u:.2f}".format(c=fit_x[0], u=fit_x[1]))
    session.logger.info("Best y: {c:.1f}+-{u:.2f}".format(c=fit_y[0], u=fit_y[1]))
    session.logger.info("Fit  z: {c:.1f}+-{u:.2f}".format(c=fit_z[0], u=fit_z[1]))

    # Updating the required processes
    lumi_hscan_updating(session, interactive=True, fit_x=fit_x, fit_y=fit_y, **args)

    ## Sending gantry to fitted position after fit
    if (
        fit_x[0] > 0
        and fit_x[0] < session.max_x
        and fit_y[0] > 0
        and fit_y[0] < session.max_y
    ):
        session.hw.move_to(fit_x[0], fit_y[0], args["scanz"])
    else:
        session.logger.warning("Fit position is out of gantry bounds, not moving")
