# pylint: disable=global-statement,redefined-outer-name
import argparse
import csv
import glob
import json
import os

import dateutil.parser
import yaml
from flask import Flask, jsonify, redirect, render_template, send_from_directory
from flask_frozen import Freezer
from flaskext.markdown import Markdown

site_data = {}
by_uid = {}
by_day = {}
by_time = {}


def main(site_data_path):
    global site_data, extra_files
    extra_files = ["README.md"]
    # Load all for your sitedata one time.
    for f in glob.glob(site_data_path + "/*"):
        extra_files.append(f)
        name, typ = f.split("/")[-1].split(".")
        if typ == "json":
            site_data[name] = json.load(open(f))
        elif typ in {"csv", "tsv"}:
            site_data[name] = list(csv.DictReader(open(f)))
        elif typ == "yml":
            site_data[name] = yaml.load(open(f).read(), Loader=yaml.SafeLoader)

    for typ in ["paper_list", "speakers", "workshops", "session_list"]:
        by_uid[typ] = {}

        if typ == "session_list":
            by_uid["events"] = {}
            by_uid["sessions"] = {}

            for session_id, p in site_data[typ].items():
                by_uid["events"][session_id] = p

                # also iterate through each session within each event
                for timeslot in p["sessions"]:
                    # also put some parent info back into this item
                    fq_timeslot = timeslot.copy()
                    fq_timeslot.update(
                        {
                            "event": p["event"],
                            "event_type": p["event_type"],
                            "parent_id": session_id,
                        }
                    )

                    by_uid["sessions"][timeslot["session_id"]] = fq_timeslot

        elif typ == "paper_list":
            for id, p in site_data[typ].items():
                by_uid[typ][id] = p

        else:
            for p in site_data[typ]:
                by_uid[typ][p["UID"]] = p

    # organize sessions by day (calendar)
    for session in by_uid["sessions"].values():
        this_date = dateutil.parser.parse(session["time_start"])
        day = this_date.strftime("%A")
        if day not in by_day:
            by_day[day] = []

        by_day[day].append(format_by_session_list(session))

    # organize sessions by timeslot (linking simultaneous sessions together)
    for day, day_sessions in by_day.items():
        time_sessions = {}
        for session in day_sessions:
            timeslot = session["startTime"] + "|" + session["endTime"]
            if timeslot not in time_sessions:
                this_date = dateutil.parser.parse(session["startTime"])
                time_sessions[timeslot] = {
                    "sessions": [],
                    "date": this_date.strftime("%A, %d %b %Y"),
                    "startTime": session["startTime"],
                    "endTime": session["endTime"],
                }

            time_sessions[timeslot]["sessions"].append(session)

        by_time[day] = time_sessions

    ## TODO: add paper information to session information

    print("Data Successfully Loaded")
    return extra_files


# main() should be called before this function
def generateDayCalendars():
    if len(by_day) == 0:
        raise Exception("call main() before this function")

    all_events = []
    for day in by_day:
        day_events = []
        for session in by_day[day]:
            session_event = {
                "id": session["id"],
                "title": session["fullTitle"],
                "start": session["startTime"],
                "end": session["endTime"],
                # "location": session['youtube'],
                "location": "/session_" + session["id"] + ".html",
                "link": "http://virtual.ieeevis.org/session_" + session["id"] + ".html",
                "category": "time",
                "calendarId": session["type"],
            }
            day_events.append(session_event)

        calendar_fname = "calendar_" + day + ".json"
        # full_calendar_fname = os.path.join(site_data_path, calendar_fname)
        # with open(full_calendar_fname, 'w', encoding='utf-8') as f:
        #     json.dump(day_events, f, ensure_ascii=False, indent=2)

        site_data[calendar_fname] = day_events
        all_events.extend(day_events)

        # for the purposes of simplifying the main schedule, group by start/end times; merge times together; make location the appropriate tab
        # aggregated_events = []
        # timeslots = set(map(lambda event: event['start'] + "|" + event['end'], day_events))
        # for timeslot in timeslots:
        #     timeslot_events = []
        #     for event in day_events:
        #         timeslot_string = event['start']+ "|" + event['end']
        #         if timeslot_string == timeslot:
        #             timeslot_events.append(event)

        #     agg_event = {
        #         "id": timeslot,
        #         "title": ", ".join(map(lambda event: event['title'], timeslot_events)),
        #         "start": session['startTime'],
        #         "end": session['endTime'],
        #         # "location": session['youtube'],
        #         "location": "#tab-" + day,
        #         "link": "http://virtual.ieeevis.org/schedule.html#tab-" + day + ".html",
        #         "category": "time",
        #         "calendarId": "",
        #     }
        #     aggregated_events.append(agg_event)

        # all_events.extend(aggregated_events)

    # overwrite static main_calendar json with all assembled events
    site_data["main_calendar"] = all_events


# ------------- SERVER CODE -------------------->

app = Flask(__name__)
app.config.from_object(__name__)
freezer = Freezer(app)
markdown = Markdown(app)


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
    return send_from_directory(site_data_path, "favicon.png")


# TOP LEVEL PAGES


@app.route("/index.html")
def home():
    data = _data()
    data["readme"] = open("README.md").read()
    data["committee"] = site_data["committee"]["committee"]
    return render_template("index.html", **data)


@app.route("/help.html")
def about():
    data = _data()
    data["FAQ"] = site_data["faq"]["FAQ"]
    return render_template("help.html", **data)


@app.route("/papers.html")
def papers():
    data = _data()
    # data["papers"] = site_data["papers"]
    return render_template("papers.html", **data)


@app.route("/paper_vis.html")
def paper_vis():
    data = _data()
    return render_template("papers_vis.html", **data)


@app.route("/calendar.html")
def schedule():
    data = _data()

    data["days"] = {}
    for day in by_day:
        data["days"][day] = {"timeslots": by_time[day]}

    return render_template("schedule.html", **data)


# ALPER TODO: we should just special-case particular sessions and render them under this route
@app.route("/workshops.html")
def workshops():
    data = _data()
    data["workshops"] = [
        format_workshop(workshop) for workshop in site_data["workshops"]
    ]
    return render_template("workshops.html", **data)


def extract_list_field(v, key):
    value = v.get(key, "")
    if isinstance(value, list):
        return value
    if value.find("|") != -1:
        return value.split("|")
    else:
        return value.split(",")


def format_paper(v):
    list_keys = ["authors", "keywords"]
    list_fields = {}
    for key in list_keys:
        list_fields[key] = extract_list_field(v, key)

    return {
        "id": v["uid"],
        "title": v["title"],
        "authors": list_fields["authors"],
        "keywords": list_fields["keywords"],
        "abstract": v["abstract"],
        "time_stamp": v["time_stamp"],
        "session_id": v["session_id"],
        "session_title": by_uid["sessions"][v["session_id"]]["title"],
        # for papers.html:
        "sessions": [by_uid["sessions"][v["session_id"]]["title"]],
        "UID": v["uid"],
        "pdf_url": v.get("pdf_url", ""),
    }


## new format for paper_list.json
# def format_paper_list(v):
#     return {
#         "id": v['uid'],
#         "forum": v['uid'].split('-')[1],
#         "content": {
#             "title": v["title"],
#             "authors": v["authors"],
#             "session": v["session_id"],
#             "time_stamp": v["time_stamp"],
#         }
#     }


def format_workshop(v):
    list_keys = ["authors"]
    list_fields = {}
    for key in list_keys:
        list_fields[key] = extract_list_field(v, key)

    return {
        "id": v["UID"],
        "title": v["title"],
        "organizers": list_fields["authors"],
        "abstract": v["abstract"],
    }


def format_session(v):
    list_keys = ["Organizers"]
    list_fields = {}
    for key in list_keys:
        list_fields[key] = extract_list_field(v, key)

    return {
        "id": v["UID"],
        "title": v["Title"],
        "type": v["Type"],
        "abstract": v["Abstract"],
        "organizers": list_fields["Organizers"],
        "chair": v["Chair"],
        "startTime": v["StartFixed"],
        "endTime": v["EndFixed"],
        "youtube": v["YouTube"],
        "discord": v["Discord"],
    }


# new format for session_list.json
def format_session_list(v):
    return {
        "id": v["session_id"],
        "title": v["title"],
        "type": v["session_id"][0],  # first character designates type
        "startTime": v["time_start"],
        "endTime": v["time_end"],
        "timeSlots": v["time_slots"],
    }


def format_by_session_list(v):
    fullTitle = v["event"]
    redundantTitle = True
    if v["event"].lower() != v["title"].lower():
        fullTitle += ": " + v["title"]
        redundantTitle = False

    return {
        "id": v["session_id"],
        "title": v["title"],
        "type": v["event_type"]
        .split(" ")[0]
        .lower(),  # get first word, which should be good enough...
        "chair": v["chair"],
        "organizers": v["organizers"],
        "startTime": v["time_start"],
        "endTime": v["time_end"],
        "timeSlots": v["time_slots"],
        "event": v["event"],
        "event_type": v["event_type"],
        "parent_id": v["parent_id"],
        "fullTitle": fullTitle,
        "redundantTitle": redundantTitle,
    }


# ITEM PAGES


@app.route("/paper_<paper>.html")
def paper(paper):
    uid = paper
    v = by_uid["paper_list"][uid]
    data = _data()
    data["paper"] = format_paper(v)
    return render_template("paper.html", **data)


# ALPER TODO: get keynote info
@app.route("/speaker_<speaker>.html")
def speaker(speaker):
    uid = speaker
    v = by_uid["speakers"][uid]
    data = _data()
    data["speaker"] = v
    return render_template("speaker.html", **data)


# ALPER TODO: populate the workshop list from session_list
@app.route("/workshop_<workshop>.html")
def workshop(workshop):
    uid = workshop
    v = by_uid["workshops"][uid]
    data = _data()
    data["workshop"] = format_workshop(v)
    return render_template("workshop.html", **data)


@app.route("/session_<session>.html")
def session(session):
    uid = session
    v = by_uid["sessions"][uid]
    data = _data()
    data["session"] = format_by_session_list(v)
    return render_template("session.html", **data)


## TODO: event landing page
## (no livestream links here, just links out to each session and maybe has more descriptive metadata)
@app.route("/event_<event>.html")
def event(event):
    uid = event
    v = by_uid["session_list"][uid]
    data = _data()
    data["event"] = format_session(v)
    return render_template("event.html", **data)


# ALPER TODO: there should be a single poster page; redirect to iPosters
@app.route("/posters.html")
def posters():
    data = _data()
    return render_template("posters.html", **data)


@app.route("/chat.html")
def chat():
    data = _data()
    return render_template("chat.html", **data)


# FRONT END SERVING

## ALPER TODO: not sure what uses this (papers.html?), but we don't need it right now
@app.route("/papers.json")
def paper_json():
    json = []
    for v in site_data["paper_list"].items():
        json.append(format_paper(v[1]))
    return jsonify(json)


@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)


@app.route("/serve_<path>.json")
def serve(path):
    return jsonify(site_data[path])


# --------------- DRIVER CODE -------------------------->
# Code to turn it all static


@freezer.register_generator
def generator():
    for paper in site_data["paper_list"].values():
        yield "paper", {"paper": str(paper["uid"])}
    for speaker in site_data["speakers"]:
        yield "speaker", {"speaker": str(speaker["UID"])}
    for workshop in site_data["workshops"]:
        yield "workshop", {"workshop": str(workshop["UID"])}
    for session in by_uid["sessions"].keys():
        yield "session", {"session": str(session)}

    for key in site_data:
        yield "serve", {"path": key}


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
    extra_files = main(site_data_path)

    generateDayCalendars()

    if args.build:
        freezer.freeze()
    else:
        debug_val = False
        if os.getenv("FLASK_DEBUG") == "True":
            debug_val = True

        app.run(port=5000, debug=debug_val, extra_files=extra_files)
