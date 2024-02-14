import io
import os

import cv2
from flask import Response


def make_jpeg_image_byte(image):
    """Additional wrapping strings around JPEG image byte strings"""
    return b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + image + b"\r\n"


def visual_current(session):
    """
    Returning the current gantry visual system captured image. Reference for
    how the Reponse object is written can be found here:
    https://medium.com/datadriveninvestor/video-streaming-using-flask-and-opencv-c464bf8473d6
    """

    def default_image():
        """What image to show if visual is not available"""
        default_img_path = os.path.abspath(
            os.path.join(
                os.path.basename(__file__), "../../../gui_client/public/visual_off.jpg"
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
                yield make_jpeg_image_byte(
                    cv2.imencode(".jpg", session.hw.get_frame())
                )[1]
            except Exception:  # For any error falback to default
                yield default_image()
            session.sleep(0.1)  # Refresh interval (in seconds)

    return Response(
        current_image_bytes(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )
