#!/usr/bin/env python3
# Setting up the configuration directories, as well as settings the standard
# paths for storing calibration progress. This script is expected to be ran
# from a path that contains the `SiPMCalibControl` directory

import os
import pathlib

from gantry_control.cli.board import DEFAULT_STORE_PATH, TEMPLATE_DIR

print(f"Checking template path [{TEMPLATE_DIR}]...")
pathlib.Path(TEMPLATE_DIR).mkdir(parents=True, exist_ok=True)

source_dir = os.path.abspath(os.path.dirname(__file__) + "/../config_templates")
target_list = os.listdir(source_dir)
for target in target_list:
    print(f"Checking symlink for [{target}]...")
    source_path = os.path.join(source_dir, target)
    final_path = os.path.join(TEMPLATE_DIR, target)
    if not os.path.islink(final_path):
        os.symlink(source_path, final_path, target_is_directory=True)

print("Done!")


print(f"Making default storage [{DEFAULT_STORE_PATH}]...")
pathlib.Path(DEFAULT_STORE_PATH).mkdir(parents=True, exist_ok=True)
print("Done!")
