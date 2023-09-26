# pylint: disable=global-statement,redefined-outer-name
import argparse
import collections
import csv
import glob
import json
import os

import dateutil.parser
import yaml
from flask import Flask, jsonify, redirect, render_template, send_from_directory
from flask_frozen import Freezer
from flask_minify import minify
from flaskext.markdown import Markdown

from blueprints.blueprint_2020 import year_blueprint as blueprint_2020
from blueprints.blueprint_2021 import year_blueprint as blueprint_2021
from blueprints.blueprint_2022 import year_blueprint as blueprint_2022
from blueprints.blueprint_2023 import year_blueprint as blueprint_2023

site_data = {}
by_uid = {}
by_day = {}
by_time = {}
CURRENT_YEAR = "2023"

"""2020 was the first virtual vis year, and the only year where urls didn't include
the year (i.e. /year/2021/papers/153), so if any requests come in under /papers/153,
we redirect to /year/2020/papers/153.  Any other root URLs we redirect to the current
year (so / redirects to /year/2021 if CURRENT_YEAR == 2021)
"""
FROZEN_YEAR = "2020"

# ------------- SERVER CODE -------------------->

app = Flask(__name__)
app.config.from_object(__name__)
app.config["FREEZER_IGNORE_404_NOT_FOUND"] = True
# app.config['FREEZER_STATIC_IGNORE'] = ['static/*']
freezer = Freezer(app)
markdown = Markdown(app)

# Mounts previous + current years at /year/{year}/*.  See blueprints folder
blueprints = [blueprint_2020, blueprint_2021, blueprint_2022, blueprint_2023]
for blueprint in blueprints:
    app.register_blueprint(blueprint)

# # --------------- DRIVER CODE -------------------------->
# # Code to turn it all static


@freezer.register_generator
def generator():
    for blueprint in blueprints:
        site_data = blueprint.site_data
        by_uid = blueprint.by_uid
        year = blueprint.year
        for paper in site_data["paper_list"].values():
            yield "/year/{}/paper_{}.html".format(year, str(paper["uid"]))
        for speaker in site_data["speakers"]:
            yield "/year/{}/speaker_{}.html".format(year, str(speaker["UID"]))
        for workshop in site_data["workshops"]:
            yield "/year/{}/workshop_{}.html".format(year, str(workshop["UID"]))
        for session in by_uid["sessions"].keys():
            yield "/year/{}/session_{}.html".format(year, str(session))
        for event in by_uid["events"].keys():
            yield "/year/{}/event_{}.html".format(year, str(event))

        # only some years have posters
        if "poster_list" in site_data:
            for poster in site_data["poster_list"].values():
                yield "/year/{}/poster_{}.html".format(year, str(poster["uid"]))

        # only some years use rooms
        if "room_names" in site_data["config"]:
            for room_name in site_data["config"]["room_names"]:
                yield "/year/{}/room_{}.html".format(year, str(room_name))

        for key in site_data:
            yield "/year/{}/serve_{}.json".format(year, str(key))


# Utility method for handling redirects in the frozen site
def meta_redirect_html(site_year, site_path):
    return render_template(
        "year_redirect.html", site_path=site_path, site_year=site_year
    )
    # return render_template('year_redirect.html', { 'site_path': site_path, 'site_year': site_year})


# MAIN PAGES


@app.route("/")
def index():
    return meta_redirect_html(CURRENT_YEAR, "index.html")


@app.route("/favicon.png")
def favicon():
    return meta_redirect_html(CURRENT_YEAR, "favicon.png")


# TOP LEVEL PAGES


@app.route("/index.html")
def home():
    return meta_redirect_html(CURRENT_YEAR, "index.html")
    # data = {}
    # data['site_path'] = 'index.html'
    # data['site_year'] = CURRENT_YEAR
    # return render_template('year_redirect.html', **data)


@app.route("/help.html")
def about():
    return meta_redirect_html(FROZEN_YEAR, "help.html")


@app.route("/jobs.html")
def jobs():
    return meta_redirect_html(FROZEN_YEAR, "jobs.html")


@app.route("/impressions.html")
def impressions():
    return meta_redirect_html(FROZEN_YEAR, "impressions.html")


@app.route("/papers.html")
def papers():
    return meta_redirect_html(FROZEN_YEAR, "papers.html")


@app.route("/paper_vis.html")
def paper_vis():
    return meta_redirect_html(FROZEN_YEAR, "paper_vis.html")


@app.route("/calendar.html")
def schedule():
    return meta_redirect_html(FROZEN_YEAR, "calendar.html")


@app.route("/events.html")
def events():
    return meta_redirect_html(FROZEN_YEAR, "events.html")


# ALPER TODO: we should just special-case particular sessions and render them under this route
@app.route("/workshops.html")
def workshops():
    return meta_redirect_html(FROZEN_YEAR, "workshops.html")


# ITEM PAGES


@app.route("/paper_<paper>.html")
def paper(paper):
    return meta_redirect_html(FROZEN_YEAR, "paper_{}.html".format(paper))


# ALPER TODO: get keynote info
@app.route("/speaker_<speaker>.html")
def speaker(speaker):
    return meta_redirect_html(FROZEN_YEAR, "speaker_{}.html".format(speaker))


@app.route("/awards.html")
def awards():
    return meta_redirect_html(FROZEN_YEAR, "awards.html")


@app.route("/speakers.html")
def speakers():
    return meta_redirect_html(FROZEN_YEAR, "speakers.html")


# ALPER TODO: populate the workshop list from session_list
@app.route("/workshop_<workshop>.html")
def workshop(workshop):
    return meta_redirect_html(FROZEN_YEAR, "workshop_{}.html".format(workshop))


@app.route("/session_vis-keynote.html")
def keynote():
    return meta_redirect_html(FROZEN_YEAR, "session_vis-keynote.html")


@app.route("/session_vis-capstone.html")
def capstone():
    return meta_redirect_html(FROZEN_YEAR, "session_vis-capstone.html")


@app.route("/session_x-posters.html")
def poster_session():
    return meta_redirect_html(FROZEN_YEAR, "session_x-posters.html")


@app.route("/session_<session>.html")
def session(session):
    return meta_redirect_html(FROZEN_YEAR, "session_{}.html".format(session))


@app.route("/room_<room>.html")
def room(room):
    return meta_redirect_html(FROZEN_YEAR, "room_{}.html".format(room))


@app.route("/event_<event>.html")
def event(event):
    return meta_redirect_html(FROZEN_YEAR, "event_{}.html".format(event))


# ALPER TODO: there should be a single poster page; redirect to iPosters
@app.route("/posters.html")
def posters():
    return meta_redirect_html(FROZEN_YEAR, "posters.html")


## Internal only; used to generate markdown-like list for main website paper list
@app.route("/paperlist.html")
def allpapers():
    return meta_redirect_html(FROZEN_YEAR, "paperlist.html")


# ALPER TODO: remove
@app.route("/chat.html")
def chat():
    return meta_redirect_html(FROZEN_YEAR, "chat.html")


@app.route("/redirect.html")
def redirect_page():
    return meta_redirect_html(FROZEN_YEAR, "redirect.html")


# FRONT END SERVING

# @app.route("/papers.json")
# def paper_json():
#     return meta_redirect_html(FROZEN_YEAR, "papers.json")


@app.route("/static/<path:path>")
def send_static(path):
    return meta_redirect_html(FROZEN_YEAR, "static/{}.html".format(path))


@app.route("/serve_<path>.json")
def serve(path):
    return meta_redirect_html(FROZEN_YEAR, "serve_{}.html".format(path))


# Streaming single page app


@app.route("/streaming.html")
def streaming():
    return meta_redirect_html(CURRENT_YEAR, "streaming")


@app.route("/playback.html")
def playback():
    return meta_redirect_html(CURRENT_YEAR, "playback")


print("Data Successfully Loaded")


def parse_arguments():
    parser = argparse.ArgumentParser(description="MiniConf Portal Command Line")

    parser.add_argument(
        "--build",
        action="store_true",
        default=False,
        help="Convert the site to static assets",
    )

    parser.add_argument(
        "-b",
        action="store_true",
        default=False,
        dest="build",
        help="Convert the site to static assets",
    )

    parser.add_argument("path", help="Pass the JSON data path and run the server")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()

    site_data_path = args.path

    if args.build:
        minify(app=app, html=True, js=False, cssless=True)
        freezer.freeze()
    else:
        debug_val = False
        if os.getenv("FLASK_DEBUG") == "True":
            debug_val = True

        app.run(port=5000, debug=debug_val)
