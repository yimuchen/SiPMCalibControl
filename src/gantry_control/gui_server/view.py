"""

Defining the URL-like responses to the client session. Here we are relying on
the decorator method, since everything should be defined for the session to
make sense. Notice that register_view_methods should be called after the
initialization of the GUISession instance of interest.

"""
import os

from flask import jsonify, render_template

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
        else:
            raise ValueError("Corresponding contents was not found!!")

        # Converting the target file content
        if filetype == "json":
            return jsonify(content)
        else:
            raise ValueError("Unknown format requested!!")
