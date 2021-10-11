from flask import Blueprint, render_template, abort, Flask, jsonify, redirect, send_from_directory
from flaskext.markdown import Markdown
from flask_minify import minify
import glob
import collections
import csv
import json
import os
import dateutil.parser
import yaml

year=2021
year_blueprint = Blueprint("vis{}".format(year), __name__, template_folder="templates/{}".format(year))
# year_blueprint = Blueprint("vis{}".format(year), __name__,
#                         template_folder="templates/{}".format(year),
#                         static_folder="static",
#                         static_url_path="/year/{}/static".format(year))

site_data = {}
by_uid = {}
by_day = {}
by_time = {}
def main(site_data_path):
    # global site_data, extra_files
    extra_files = ["README.md"]
    # Load all for your sitedata one time.
    for f in glob.glob(site_data_path + "/*"):
        extra_files.append(f)
        name, typ = f.split("/")[-1].split(".")
        if typ == "json":
            site_data[name] = json.load(open(f))
        elif typ in {"csv", "tsv"}:
            site_data[name] = list(csv.DictReader(open(f, encoding='utf-8-sig')))
        elif typ == "yml":
            site_data[name] = yaml.load(open(f).read(), Loader=yaml.SafeLoader)

    for typ in ["paper_list", "speakers", "workshops", "session_list", "poster_list"]:
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
                    fq_timeslot.update({
                        "event": p["event"],
                        "event_type": p["event_type"],
                        "parent_id": session_id,
                        "event_description": p["event_description"],
                        "event_url": p["event_url"],
                    })

                    by_uid['sessions'][timeslot['session_id']] = fq_timeslot

                    by_uid["sessions"][timeslot["session_id"]] = fq_timeslot

        elif typ == "paper_list" or typ == "poster_list":
            for paper_id, p in site_data[typ].items():
                by_uid[typ][paper_id] = p

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

        by_time[day] = collections.OrderedDict(sorted(time_sessions.items()))

    ## TODO: add paper information to session information

    print("Data Successfully Loaded")
    year_blueprint.site_data = site_data
    year_blueprint.by_uid = by_uid
    year_blueprint.year = year

    print("Data Successfully Loaded")

    generateDayCalendars()
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
                "room": session["track"],
                "day": sessionTimeToCalendarDay(session["startTime"]),
                "timeStart": sessionTimeToCalendarTime(session["startTime"]),
                "timeEnd": sessionTimeToCalendarTime(session["endTime"]),
                # "location": session['youtube'],
                "location": "session_" + session["id"] + ".html",
                "link": "session_" + session["id"] + ".html",
                "category": "time",
                "eventType": session["type"],
            }
            day_events.append(session_event)

        calendar_fname = "calendar_" + day

        # try ordering by title; maybe this'll make things line up in the calendar?
        day_events = sorted(day_events, key=lambda event: event['title'])

        site_data[calendar_fname] = day_events
        all_events.extend(day_events)

    # overwrite static main_calendar json with all assembled events
    site_data["main_calendar"] = all_events

# converts a full date string to a "time string", which is simply "07:45" -> "0745" (times in conference timezone)
def sessionTimeToCalendarTime(dateTime):
    thetime = dateTime.split('T')[1]

    # update the hour (GMT -5)
    # assumption is that day won't change when we do this
    split_time = thetime.split(":", 2)
    hour = int(split_time[0]) - 5
    minute = split_time[1]

    return "time-" + str(hour).zfill(2) + str(minute).zfill(2)

# converts a full date string to an indexed day for the calendar
# (e.g., if conference starts on Sunday, then session on first day is "day-1")
def sessionTimeToCalendarDay(dateTime):
    start_day = 24
    day = int(dateTime.split("T")[0].split("-")[-1])

    return "day-" + str(day - start_day + 1)

def _data():
    data = {}
    data["config"] = site_data["config"]
    return data


# @year_blueprint.route("/year/{}".format(year))
# def index():
#     return render_template('year_redirect.html', site_path='index.html', site_year=2021)

@year_blueprint.route("/favicon.png")
def favicon():
    return send_from_directory(site_data_path, "favicon.png")


# TOP LEVEL PAGES


@year_blueprint.route("/year/{}/index.html".format(year))
def home():
    data = _data()
    data["readme"] = open("sitedata/{}/README.md".format(year)).read()
    data["supporters"] = site_data["supporters"]
    return render_template("{}/index.html".format(year), **data)


@year_blueprint.route("/year/{}/help.html".format(year))
def about():
    data = _data()
    data["discord"] = open("sitedata/{}/discord_guide.md".format(year)).read()
    data["FAQ"] = site_data["faq"]["FAQ"]
    data["gather"] = site_data["faq"]["gather"]
    return render_template("{}/help.html".format(year), **data)


@year_blueprint.route("/year/{}/papers.html".format(year))
def papers():
    data = _data()
    # data["papers"] = site_data["papers"]
    return render_template("{}/papers.html".format(year), **data)

@year_blueprint.route("/year/{}/posters.html".format(year))
def posters():
    data = _data()
    # data["posters"] = site_data["posters"]
    return render_template("{}/posters.html".format(year), **data)

@year_blueprint.route("/year/{}/paper_vis.html".format(year))
def paper_vis():
    data = _data()
    return render_template("{}/papers_vis.html".format(year), **data)


@year_blueprint.route("/year/{}/calendar.html".format(year))
def schedule():
    data = _data()

    data["days"] = {}
    for day in by_day:
        data["days"][day] = {"timeslots": by_time[day]}

    return render_template("{}/schedule.html".format(year), **data)


@year_blueprint.route("/year/{}/events.html".format(year))
def events():
    data = _data()
    all_events = [format_session_as_event(event_item, event_uid) for event_uid, event_item in by_uid['events'].items()]
    data['events'] = sorted(all_events, key=lambda e: e['abbr_type'])
    data['event_types'] = sorted(list(set([(e['type'], e["abbr_type"]) for e in all_events])), key=lambda x: x[0])
    data['colors'] = data['config']['calendar']['colors']
    return render_template("{}/events.html".format(year), **data)


# ALPER TODO: we should just special-case particular sessions and render them under this route
@year_blueprint.route("/year/{}/workshops.html".format(year))
def workshops():
    data = _data()
    data["workshops"] = [
        format_workshop(workshop) for workshop in site_data["workshops"]
    ]
    return render_template("{}/workshops.html".format(year), **data)


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

    paper_session = by_uid["sessions"][v["session_id"]]
    paper_event = by_uid["events"][paper_session["parent_id"]]

    return {
        "id": v["uid"],
        "title": v["title"],
        "authors": list_fields["authors"],
        "keywords": list_fields["keywords"],
        "abstract": v["abstract"],
        "time_stamp": v["time_stamp"],
        "session_id": v["session_id"],
        "session_title": paper_session["title"],
        "event_id": paper_session["parent_id"],
        "event_title": paper_event["event"],
        "award": v["paper_award"],
        "has_image": v["has_image"],
        "image_caption": v["image_caption"],
        "external_paper_link": v["external_paper_link"],
        "youtube_ff_url": v["ff_link"],
        "youtube_ff_id": v["ff_link"].split("/")[-1] if v["ff_link"] else None,

        # for papers.html:
        "sessions": [paper_session["title"]],
        "UID": v["uid"],
    }

def format_poster(v):
    list_keys = ["authors"]
    list_fields = {}
    for key in list_keys:
        list_fields[key] = extract_list_field(v, key)

    return {
        "id": v["uid"],
        "authors": list_fields["authors"],
        "title": v["title"],
        "discord_channel": v["discord_channel"],
        "session_title": v["event"],
        "sessions": [v["event"]],
        "poster_pdf": "https://ieeevis.b-cdn.net/vis_2021/posters/" + v["uid"] + ".pdf",
        "has_image": v["has_image"],
    }


def format_paper_list(v):
    list_keys = ["authors"]
    list_fields = {}
    for key in list_keys:
        list_fields[key] = extract_list_field(v, key)

    return {
        "id": v["uid"],
        "title": v["title"],
        "authors": list_fields["authors"],
        "award": v["paper_award"],
        ## eventually, FF/DOI?
    }

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


def format_session_as_event(v, uid):
    list_keys = ['Organizers']
    list_fields = {}
    for key in list_keys:
        list_fields[key] = extract_list_field(v, key)

    return {
        "id": uid,
        "title": v["long_name"],
        "type": v["event_type"],
        "abbr_type": v["event_type"].split(" ")[0].lower(),
        "abstract": v["event_description"],
        "url": v["event_url"],
        "startTime": v["sessions"][0]["time_start"],
        "endTime": v["sessions"][-1]["time_end"],
        "sessions": [format_by_session_list(by_uid["sessions"][timeslot["session_id"]]) for timeslot in v["sessions"]],
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
        "track": v["track"],
        "startTime": v["time_start"],
        "endTime": v["time_end"],
        "timeSlots": v["time_slots"],
        "event": v["event"],  # backloaded from parent event
        "event_type": v["event_type"],  # backloaded from parent event
        "parent_id": v["parent_id"],  # backloaded from parent event
        "event_description": v["event_description"],  # backloaded from parent event
        "event_url": v["event_url"],  # backloaded from parent event
        "fullTitle": fullTitle,
        "redundantTitle": redundantTitle,
        "discord_category": v["discord_category"],
        "discord_channel": v["discord_channel"],
        "discord_channel_id": v["discord_channel_id"],
        "youtube_url": v["youtube_url"],
        "youtube_id": v["youtube_url"].split("/")[-1] if v["youtube_url"] else None,
        "streaming_session_id": v["streaming_session_id"] if "streaming_session_id" in v else None,
        "ff_playlist": v["ff_playlist"],
        "ff_playlist_id": v["ff_playlist"].split("=")[-1] if v["ff_playlist"] else None,
        # "zoom_meeting": v["zoom_meeting"]
    }


# ITEM PAGES


@year_blueprint.route("/year/{}/paper_<paper>.html".format(year))
def paper(paper):
    uid = paper
    v = by_uid["paper_list"][uid]
    data = _data()
    data["requires_auth"] = True
    data["paper"] = format_paper(v)
    return render_template("{}/paper.html".format(year), **data)

@year_blueprint.route("/year/{}/poster_<poster>.html".format(year))
def poster(poster):
    uid = poster
    v = by_uid["poster_list"][uid]
    data = _data()
    data["requires_auth"] = True
    data["poster"] = format_poster(v)
    return render_template("{}/poster.html".format(year), **data)

# ALPER TODO: get keynote info
@year_blueprint.route("/year/{}/speaker_<speaker>.html".format(year))
def speaker(speaker):
    uid = speaker
    v = by_uid["speakers"][uid]
    data = _data()
    data["speaker"] = v
    return render_template("{}/speaker.html".format(year), **data)

@year_blueprint.route("/year/{}/awards.html".format(year))
def awards():
    data = _data()
    data["awards_honor"] = site_data["awards_honor"]
    data["awards_tot"] = site_data["awards_tot"]
    data["awards_academy"] = site_data["awards_academy"]
    data["awards_papers"] = site_data["awards_papers"]
    return render_template("{}/awards.html".format(year), **data)


@year_blueprint.route("/year/{}/speakers.html".format(year))
def speakers():
    data = _data()
    data["speakers"] = site_data["speakers"]
    return render_template("{}/speakers.html".format(year), **data)

# ALPER TODO: populate the workshop list from session_list
@year_blueprint.route("/year/{}/workshop_<workshop>.html".format(year))
def workshop(workshop):
    uid = workshop
    v = by_uid["workshops"][uid]
    data = _data()
    data["workshop"] = format_workshop(v)
    return render_template("{}/workshop.html".format(year), **data)

# TODO: re-enable once keynote event available
# @year_blueprint.route('/year/{}/session_vis-keynote.html'.format(year))
def keynote():
    uid = "vis-keynote"
    v = by_uid["sessions"][uid]
    data = _data()
    data["requires_auth"] = True
    data["session"] = format_by_session_list(v)
    data["session"]["speaker"] = site_data["speakers"][0]
    return render_template("{}/keynote_or_capstone.html".format(year), **data)

# TODO: re-enable once capstone event available
# @year_blueprint.route('/year/{}/session_vis-capstone.html'.format(year))
def capstone():
    uid = "vis-capstone"
    v = by_uid["sessions"][uid]
    data = _data()
    data["requires_auth"] = True
    data["session"] = format_by_session_list(v)
    data["session"]["speaker"] = site_data["speakers"][1]
    return render_template("{}/keynote_or_capstone.html".format(year), **data)

# TODO: re-enable once posters event available
# @year_blueprint.route("/year/{}/session_x-posters.html".format(year))
def poster_session():
    uid = "x-posters"
    v = by_uid["sessions"][uid]
    data = _data()
    data["requires_auth"] = True
    data["session"] = format_by_session_list(v)
    data["event"] = format_session_as_event(by_uid['events'][uid], uid)
    if uid in site_data["event_ff_playlists"]:
        data["event"]["ff_playlist"] = site_data["event_ff_playlists"][uid]
        data["event"]["ff_playlist_id"] = site_data["event_ff_playlists"][uid].split("=")[-1]
    return render_template("{}/poster_session.html".format(year), **data)


@year_blueprint.route("/year/{}/session_<session>.html".format(year))
def session(session):
    uid = session
    v = by_uid["sessions"][uid]
    data = _data()
    data["requires_auth"] = True
    data["session"] = format_by_session_list(v)
    if "streaming_session_id" in v:
        data["streaming_session_id"] = v["streaming_session_id"]
    return render_template("{}/session.html".format(year), **data)


@year_blueprint.route('/year/{}/event_<event>.html'.format(year))
def event(event):
    uid = event
    v = by_uid['events'][uid]
    data = _data()
    data["event"] = format_session_as_event(v, uid)
    if uid in site_data["event_ff_playlists"]:
        data["event"]["ff_playlist"] = site_data["event_ff_playlists"][uid]
        data["event"]["ff_playlist_id"] = site_data["event_ff_playlists"][uid].split("=")[-1]
    return render_template("{}/event.html".format(year), **data)


## Internal only; used to generate markdown-like list for main website paper list
@year_blueprint.route("/year/{}/paperlist.html".format(year))
def allpapers():
    data = _data()
    data["papers"] = {
        'full': [],
        'short': [],
    }
    for uid, v in site_data["paper_list"].items():
        if uid[0] == "f":
            data['papers']['full'].append(format_paper_list(v))
        if uid[0] == "s":
            data['papers']['short'].append(format_paper_list(v))

    return render_template("{}/paperlist.html".format(year), **data)


# ALPER TODO: remove
@year_blueprint.route("/year/{}/chat.html".format(year))
def chat():
    data = _data()
    return render_template("{}/chat.html".format(year), **data)

@year_blueprint.route("/year/{}/redirect.html".format(year))
def redirect():
    data = _data()
    data["requires_auth"] = True
    return render_template("{}/redirect.html".format(year), **data)


# FRONT END SERVING
@year_blueprint.route("/year/{}/papers.json".format(year))
def paper_json():
    json = []
    for v in site_data["paper_list"].items():
        json.append(format_paper(v[1]))
    return jsonify(json)

@year_blueprint.route("/year/{}/posters.json".format(year))
def poster_json():
    json = []
    for v in site_data["poster_list"].items():
        json.append(format_poster(v[1]))
    return jsonify(json)


@year_blueprint.route("/year/{}/static/<path:path>".format(year))
def send_static(path):
    return send_from_directory("static/{}".format(year), path)


@year_blueprint.route("/year/{}/serve_<path>.json".format(year))
def serve(path):
    return jsonify(site_data[path])

# Streaming single page app

@year_blueprint.route("/year/{}/streaming.html".format(year))
def streaming():
    return render_template("{}/streaming.html".format(year))


site_data_path = "sitedata/{}".format(year)
extra_files = main(site_data_path)
