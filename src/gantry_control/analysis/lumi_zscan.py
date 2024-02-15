"""

lumi_hscan.py

Method for scanning the detector center

"""

import gantry_control.cli as control_cli

import numpy as np
import scipy.optimize
import time


def lumi_zscan(session: control_cli.session.Session, **kwargs):
    x = kwargs.get("x")
    y = kwargs.get("y")
    _z = kwargs.get("zlist")
    _p = kwargs.get("power")
    rootfile = kwargs.get("rootfile")

    run_dict = control_cli.saveroot.create_run_dict(session, run_process="lumi_hscan")
    save_dict = control_cli.saveroot.create_save_dict("lumi", "unc")

    try:
        for z, p in session.make_progress_bar(control_cli.format.loop_mesh(_z, _p)):
            session.hw.move_to(x, y, z)
            # self.gpio.pwm(0, power, 1e5)  # Maximum PWM frequency

            lumi, unc = control_cli.readout.obtain_readout(
                session, average=True, **kwargs
            )
            control_cli.saveroot.update_save_dict(
                session, save_dict, lumi=lumi, unc=unc
            )
            session.update_pbar_data(lumi=f"{lumi:.2f}+-{unc:.2f}")
    finally:  # Always save the results to what was obtained
        control_cli.saveroot.save_to_root(rootfile, run_dict, save_dict)


if __name__ == "__main__":
    import sys, os
    import logging

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
