import os

from flask import jsonify, render_template

from ..session import GUISession
from . import config_query, download, visual_response


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
        __map__ = {
            "actionLog": download.action_log,
            "messageLog": download.message_log,
        }
        if content not in __map__:
            raise ValueError("Corresponding contents was not found!!")
        return __map__[content](session, filetype)
        # Filtering for the understood content

    @session.app.route("/config/<query>")
    def _query(query: str):
        __map__ = {
            "boardtype": config_query.board_type,
        }
        if query not in __map__:
            raise ValueError(f"Unknown configuration type [{query}]")

        return jsonify(__map__[query](session))

    @session.app.route("/visual_current")
    def visual_current():
        return visual_response.visual_current(session)
