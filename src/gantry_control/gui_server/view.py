"""

Defining the URL-like responses to the client session. Here we are relying on
the decorator method, since everything should be defined for the session to
make sense. Notice that register_view_methods should be called after the
initialization of the GUISession instance of interest.

"""
import glob
import io
import os
import pathlib

import cv2
from flask import Response, jsonify, render_template

from ..cli.format import logrecord_to_dict, logrecord_to_line
from .session import GUISession  # Just for typing


def register_view_methods(session: GUISession):
    @session.app.route("/")
    def view_main_page():
        if os.path.isfile(os.path.join(session._js_client_path, ".index.html")):
            return render_template(".index.html")
        else:  # In case modified index.html was not generated
            return render_template("index.html")

    @session.app.route("/test/<testval>")
    def view_test(testval: str):
        return jsonify({"response": "test response!", "inputval": testval})

    @session.app.route("/download/<filetype>/<content>")
    def download_content(filetype: str, content: str):
        # Filtering for the understood content
        if content == "actionLog":
            content = session.action_log
        elif content == "messageLog":
            content = session._mem_handlers.record_list
            if filetype == "json":
                content = [logrecord_to_dict(x) for x in content]
            else:
                content = "\n".join([logrecord_to_line(x) for x in content])
        else:
            raise ValueError("Corresponding contents was not found!!")

        # Converting the target file content
        if filetype == "json":
            return jsonify(content)
        elif filetype == "text":
            return content
        else:
            raise ValueError("Unknown format requested!!")

    @session.app.route("/boardtypes")
    def boardtypes():
        currentpath = os.path.dirname(__file__)
        boardpath = os.path.join(currentpath, "../../../config_templates/board_layout")
        boardfiles = glob.glob(os.path.join(os.path.abspath(boardpath), "*.json"))
        boardnames = [pathlib.Path(os.path.basename(x)).stem for x in boardfiles]
        return jsonify(boardnames)

    @session.app.route("/existingsessions")
    def existingsession():
        return jsonify([])

    @session.app.route("/visual_current")
    def visual_current():
        """
        Returning the current gantry visual system captured image. Reference
        for how the Reponse object is written can be found here:
        https://medium.com/datadriveninvestor/video-streaming-using-flask-and-opencv-c464bf8473d6
        """

        def make_jpeg_image_byte(image):
            """Additional wrapping strings around JPEG image byte strings"""
            return b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + image + b"\r\n"

        def default_image():
            """What image to show if visual is not available"""
            default_img_path = os.path.abspath(
                os.path.join(
                    os.path.basename(__file__), "../../gui_client/public/visual_off.jpg"
                )
            )
            default_image_io = io.BytesIO(
                cv2.imencode(".jpg", cv2.imread(default_img_path, 0))[1]
            )
            return make_jpeg_image_byte(default_image_io.read())

        def current_image_bytes():
            """Continuous loop of getting the current image"""
            while True:  # This function will always generate a return
                try:
                    yield make_jpeg_image_byte(session.cmd.visual.get_image_bytes())
                except Exception:  # For any error falback to default
                    yield default_image()
                session.sleep(0.1)  # Refresh interval (in seconds)

        return Response(
            current_image_bytes(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )
