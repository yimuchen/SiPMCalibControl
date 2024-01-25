#!/usr/bin/env python3
"""
Helper build script to not have to reload each time there is a client side change
"""

import glob
import os
import subprocess


def make_symlink(oldpath: str, newpath: str):
    if not os.path.exists(newpath):
        os.symlink(oldpath, newpath)
    elif os.path.islink(newpath):
        os.remove(newpath)
        os.symlink(oldpath, newpath)
    else:
        raise OSError(f"File exists at {newpath}")


if __name__ == "__main__":
    src_base = os.path.dirname(os.path.abspath(__file__))
    build_base = os.path.join(src_base, "build/")
    subprocess.run(
        ["npm", "run", "build"], cwd=src_base
    )  # Run the default build command

    hashed_js_path = glob.glob(os.path.join(build_base, "static/js/main.*.js"))[0]
    plain_js_path = os.path.join(os.path.dirname(hashed_js_path), "main.js")
    make_symlink(hashed_js_path, plain_js_path)

    hashed_js_map = glob.glob(os.path.join(build_base, "static/js/main.*.js.map"))[0]
    plain_js_map = os.path.join(os.path.dirname(hashed_js_map), "main.js.map")
    make_symlink(hashed_js_map, plain_js_map)

    hashed_css_path = glob.glob(os.path.join(build_base, "static/css/main.*.css"))[0]
    plain_css_path = os.path.join(os.path.dirname(hashed_css_path), "main.css")
    make_symlink(hashed_css_path, plain_css_path)

    hashed_css_map = glob.glob(os.path.join(build_base, "static/css/main.*.css.map"))[0]
    plain_css_map = os.path.join(os.path.dirname(hashed_js_map), "main.css.map")
    make_symlink(hashed_css_map, plain_css_map)

    # Writing a new index
    orig_index = os.path.join(build_base, "index.html")
    with open(orig_index, "r") as f:
        content = f.read()
        content = content.replace(
            os.path.basename(hashed_js_path), os.path.basename(plain_js_path)
        )
        content = content.replace(
            os.path.basename(hashed_css_path), os.path.basename(plain_css_path)
        )
    mod_index = os.path.join(build_base, ".index.html")
    with open(mod_index, "w") as f:
        f.write(content)
