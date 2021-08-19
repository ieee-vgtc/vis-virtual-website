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
from flaskext.markdown import Markdown
from flask_minify import minify
from blueprints.blueprint_2020 import year_blueprint as blueprint_2020
from blueprints.blueprint_2021 import year_blueprint as blueprint_2021

site_data = {}
by_uid = {}
by_day = {}
by_time = {}
CURRENT_YEAR = '2021'

"""2020 was the first virtual vis year, and the only year where urls didn't include
the year (i.e. /year/2021/papers/153), so if any requests come in under /papers/153,
we redirect to /year/2020/papers/153.  Any other root URLs we redirect to the current
year (so / redirects to /year/2021 if CURRENT_YEAR == 2021)
"""
FROZEN_YEAR = '2020'


def main():
    pass
#     global site_data, extra_files
#     extra_files = ["README.md"]
#     # Load just the config in here.
#     for f in glob.glob("sitedata/{}".format(CURRENT_YEAR) + "/*"):
#         extra_files.append(f)

#         filename = f.split("/")[-1]
#         if '.' in filename:
#             name, typ = filename.split(".")
#             if typ == "json":
#                 site_data[name] = json.load(open(f))
#             elif typ in {"csv", "tsv"}:
#                 site_data[name] = list(csv.DictReader(open(f, encoding='utf-8-sig')))
#             elif typ == "yml":
#                 site_data[name] = yaml.load(open(f).read(), Loader=yaml.SafeLoader)

#     for typ in ["paper_list", "speakers", "workshops", "session_list"]:
#         by_uid[typ] = {}

#         if typ == "session_list":
#             by_uid["events"] = {}
#             by_uid["sessions"] = {}

#             for session_id, p in site_data[typ].items():
#                 by_uid["events"][session_id] = p

#                 # also iterate through each session within each event
#                 for timeslot in p["sessions"]:
#                     # also put some parent info back into this item
#                     fq_timeslot = timeslot.copy()
#                     fq_timeslot.update({
#                         "event": p["event"],
#                         "event_type": p["event_type"],
#                         "parent_id": session_id,
#                         "event_description": p["event_description"],
#                         "event_url": p["event_url"],
#                     })

#                     by_uid['sessions'][timeslot['session_id']] = fq_timeslot

#                     by_uid["sessions"][timeslot["session_id"]] = fq_timeslot

#         elif typ == "paper_list":
#             for paper_id, p in site_data[typ].items():
#                 by_uid[typ][paper_id] = p

#         else:
#             for p in site_data[typ]:
#                 by_uid[typ][p["UID"]] = p

#     # organize sessions by day (calendar)
#     for session in by_uid["sessions"].values():
#         this_date = dateutil.parser.parse(session["time_start"])
#         day = this_date.strftime("%A")
#         if day not in by_day:
#             by_day[day] = []

#         by_day[day].append(format_by_session_list(session))

#     # # organize sessions by timeslot (linking simultaneous sessions together)
#     for day, day_sessions in by_day.items():
#         time_sessions = {}
#         for session in day_sessions:
#             timeslot = session["startTime"] + "|" + session["endTime"]
#             if timeslot not in time_sessions:
#                 this_date = dateutil.parser.parse(session["startTime"])
#                 time_sessions[timeslot] = {
#                     "sessions": [],
#                     "date": this_date.strftime("%A, %d %b %Y"),
#                     "startTime": session["startTime"],
#                     "endTime": session["endTime"],
#                 }

#             time_sessions[timeslot]["sessions"].append(session)

#         by_time[day] = collections.OrderedDict(sorted(time_sessions.items()))

#     ## TODO: add paper information to session information

#     print("Data Successfully Loaded")
#     return extra_files


# # main() should be called before this function
# def generateDayCalendars():
#     if len(by_day) == 0:
#         raise Exception("call main() before this function")

#     all_events = []
#     for day in by_day:
#         day_events = []
#         for session in by_day[day]:
#             session_event = {
#                 "id": session["id"],
#                 "title": session["fullTitle"],
#                 "start": session["calendarDisplayStartTime"],
#                 "realStart": session["startTime"],
#                 "end": session["endTime"],
#                 # "location": session['youtube'],
#                 "location": "/session_" + session["id"] + ".html",
#                 "link": "http://virtual.ieeevis.org/session_" + session["id"] + ".html",
#                 "category": "time",
#                 "calendarId": session["type"],
#             }
#             day_events.append(session_event)

#         calendar_fname = "calendar_" + day + ".json"
#         # full_calendar_fname = os.path.join(site_data_path, calendar_fname)
#         # with open(full_calendar_fname, 'w', encoding='utf-8') as f:
#         #     json.dump(day_events, f, ensure_ascii=False, indent=2)

#         # try ordering by title; maybe this'll make things line up in the calendar?
#         day_events = sorted(day_events, key=lambda event: event['title'])

#         site_data[calendar_fname] = day_events
#         all_events.extend(day_events)

#         # for the purposes of simplifying the main schedule, group by start/end times; merge times together; make location the appropriate tab
#         # aggregated_events = []
#         # timeslots = set(map(lambda event: event['start'] + "|" + event['end'], day_events))
#         # for timeslot in timeslots:
#         #     timeslot_events = []
#         #     for event in day_events:
#         #         timeslot_string = event['start']+ "|" + event['end']
#         #         if timeslot_string == timeslot:
#         #             timeslot_events.append(event)

#         #     agg_event = {
#         #         "id": timeslot,
#         #         "title": ", ".join(map(lambda event: event['title'], timeslot_events)),
#         #         "start": session['startTime'],
#         #         "end": session['endTime'],
#         #         # "location": session['youtube'],
#         #         "location": "#tab-" + day,
#         #         "link": "http://virtual.ieeevis.org/schedule.html#tab-" + day + ".html",
#         #         "category": "time",
#         #         "calendarId": "",
#         #     }
#         #     aggregated_events.append(agg_event)

#         # all_events.extend(aggregated_events)

#     # overwrite static main_calendar json with all assembled events
#     site_data["main_calendar"] = all_events


# ------------- SERVER CODE -------------------->

app = Flask(__name__)
app.config.from_object(__name__)
app.config['FREEZER_IGNORE_404_NOT_FOUND'] = True
freezer = Freezer(app)
markdown = Markdown(app)

# Mounts previous + current years at /year/{year}/*.  See blueprints folder
# blueprints = [blueprint_2020, blueprint_2021]
blueprints = [blueprint_2021]
for blueprint in blueprints:
    app.register_blueprint(blueprint) 

# MAIN PAGES


def _data():
    data = {}
    data["config"] = site_data["config"]
    return data


@app.route("/")
def index():
    return redirect("/index.html")


@app.route("/favicon.png")
def favicon():
    return redirect("/year/{}/favicon.png".format(CURRENT_YEAR))


# TOP LEVEL PAGES


@app.route("/index.html")
def home():
    return redirect("/year/{}/index.html".format(CURRENT_YEAR))


@app.route("/help.html")
def about():
    return redirect("/year/{}/help.html".format(FROZEN_YEAR))


@app.route("/papers.html")
def papers():
    return redirect("/year/{}/papers.html".format(FROZEN_YEAR))


@app.route("/paper_vis.html")
def paper_vis():
    return redirect("/year/{}/paper_vis.html".format(FROZEN_YEAR))


@app.route("/calendar.html")
def schedule():
    return redirect("/year/{}/calendar.html".format(FROZEN_YEAR))


@app.route("/events.html")
def events():
    return redirect("/year/{}/events.html".format(FROZEN_YEAR))


# ALPER TODO: we should just special-case particular sessions and render them under this route
@app.route("/workshops.html")
def workshops():
    return redirect("/year/{}/workshops.html".format(FROZEN_YEAR))


# ITEM PAGES


@app.route("/paper_<paper>.html")
def paper(paper):
    return redirect("/year/{}/paper_{}.html".format(FROZEN_YEAR, paper))


# ALPER TODO: get keynote info
@app.route("/speaker_<speaker>.html")
def speaker(speaker):
    return redirect("/year/{}/speaker_{}.html".format(FROZEN_YEAR, speaker))

@app.route("/awards.html")
def awards():
    return redirect("/year/{}/awards.html".format(FROZEN_YEAR))


@app.route("/speakers.html")
def speakers():
    return redirect("/year/{}/speakers.html".format(FROZEN_YEAR))

# ALPER TODO: populate the workshop list from session_list
@app.route("/workshop_<workshop>.html")
def workshop(workshop):
    return redirect("/year/{}/workshop_{}.html".format(FROZEN_YEAR, workshop))


@app.route('/session_vis-keynote.html')
def keynote():
    return redirect("/year/{}/session_vis-keynote.html".format(FROZEN_YEAR))


@app.route('/session_vis-capstone.html')
def capstone():
    return redirect("/year/{}/session_vis-capstone.html".format(FROZEN_YEAR))

@app.route("/session_x-posters.html")
def poster_session():
    return redirect("/year/{}/session_x-posters.html".format(FROZEN_YEAR))


@app.route("/session_<session>.html")
def session(session):
    return redirect("/year/{}/session_{}.html".format(FROZEN_YEAR, session))


@app.route('/event_<event>.html')
def event(event):
    return redirect("/year/{}/event_{}.html".format(FROZEN_YEAR, event))


# ALPER TODO: there should be a single poster page; redirect to iPosters
@app.route("/posters.html")
def posters():
    return redirect("/year/{}/posters.html".format(FROZEN_YEAR))

## Internal only; used to generate markdown-like list for main website paper list
@app.route("/paperlist.html")
def allpapers():
    return redirect("/year/{}/paperlist.html".format(FROZEN_YEAR))


# ALPER TODO: remove
@app.route("/chat.html")
def chat():
    return redirect("/year/{}/chat.html".format(FROZEN_YEAR))


@app.route("/redirect.html")
def redirect_page():
    return redirect("/year/{}/redirect.html".format(FROZEN_YEAR))


# FRONT END SERVING

@app.route("/papers.json")
def paper_json():
    return redirect("/year/{}/papers.json".format(FROZEN_YEAR))


@app.route("/static/<path:path>")
def send_static(path):
    return redirect("/year/{}/static/{}.html".format(FROZEN_YEAR, path))


@app.route("/serve_<path>.json")
def serve(path):
    return redirect("/year/{}/serve_{}.html".format(FROZEN_YEAR, path))


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

        for key in site_data:
            yield "/year/{}/serve_{}.json".format(year, str(key))

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
    extra_files = main()

    # generateDayCalendars()

    if args.build:
        minify(app=app, html=True, js=False, cssless=True)
        freezer.freeze()
    else:
        debug_val = False
        if os.getenv("FLASK_DEBUG") == "True":
            debug_val = True

        app.run(port=5000, debug=debug_val, extra_files=extra_files)
