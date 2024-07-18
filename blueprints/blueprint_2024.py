from flask import Blueprint, render_template, abort, Flask, jsonify, redirect, send_from_directory
from flaskext.markdown import Markdown
from flask_minify import minify
import glob
import collections
import csv
import json
import os
import dateutil.parser
from datetime import datetime, timezone, timedelta
import yaml
from pathlib import Path
from dateutil.parser import ParserError

CONFERENCE_TIMEZONE = timezone(offset=-timedelta(hours=5)) # Eastern Time
CONFERENCE_OFFSET = -5 # EST is UTC - 5

year=2024
year_blueprint = Blueprint("vis{}".format(year), __name__, template_folder="templates/{}".format(year))

paper_type_names = {
    'short': 'VIS Short Paper',
    'full': 'VIS Full Paper',
    'associated': 'Associated Event',
    'workshop': 'Workshop'
}
site_data = {}
by_uid = {}
by_day = {}
by_time = {}
def main(site_data_path):
    # global site_data, extra_files
    extra_files = ["README.md"]
    # Load all for your sitedata one time.
    file_to_open = Path(site_data_path)
    for f in file_to_open.glob('*'):
        extra_files.append(f)
        name = f.stem
        typ = f.suffix[1:]
        if typ == "json":
            site_data[name] = json.load(open(f, encoding='utf-8-sig'))
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
                        "event": p.get("event"),
                        "event_type": p.get("event_type") or 'N/A',
                        "parent_id": session_id,
                        "event_description": p.get("event_description") or 'N/A',
                        "event_url": p.get("event_url") or 'N/A',
                        "room_name": get_room_name(fq_timeslot['track'], site_data['config']['room_names']) if ("track" in fq_timeslot) else 'N/A',
                    })

                    by_uid['sessions'][timeslot['session_id']] = fq_timeslot

        elif typ == "paper_list" or typ == "poster_list":
            for paper_id, p in site_data[typ].items():
                by_uid[typ][paper_id] = p

        else:
            for p in site_data[typ]:
                by_uid[typ][p["UID"]] = p

    # organize sessions by day (calendar)
    for session in by_uid["sessions"].values():
        if session["track"] not in ["None(virtual)", ""]:
            this_date = dateutil.parser.parse(session["time_start"]).astimezone(CONFERENCE_TIMEZONE)
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
                this_date = dateutil.parser.parse(session["startTime"]).astimezone(CONFERENCE_TIMEZONE)
                time_sessions[timeslot] = {
                    "sessions": [],
                    "date": this_date.strftime("%A, %d %b %Y"),
                    "startTime": session["startTime"],
                    "endTime": session["endTime"],
                    "room_name": session["room_name"]
                }

            time_sessions[timeslot]["sessions"].append(session)
            time_sessions[timeslot].update({"room_name": session["room_name"]})

        by_time[day] = collections.OrderedDict(sorted(time_sessions.items()))
        # by_time[day] = time_sessions

    ## TODO: add paper information to session information

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
                "shortTitle": session["title"],
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

            # skip adding demo sessions on invalid days (e.g. -1 days before conference)
            if session_event["day"] == "day--1":
                continue

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
    # dateTime will come in UTC, need to convert it to conference timezone


    thetime = dateTime.split('T')[1]

    # update the hour see CONFERENCE_TIMEZONE
    # assumption is that day won't change when we do this
    split_time = thetime.split(":", 2)
    hour = (int(split_time[0]) + CONFERENCE_OFFSET) % 24
    # round to the nearest 15 minutes
    minute = split_time[1]

    return "time-" + str(hour).zfill(2) + str(minute).zfill(2)

# converts a full date string to an indexed day for the calendar
# (e.g., if conference starts on Sunday, then session on first day is "day-1")
def sessionTimeToCalendarDay(dateTime):
    start_day = 22
    this_date = dateutil.parser.parse(dateTime).astimezone(CONFERENCE_TIMEZONE)
    day = int(this_date.strftime("%d"))

    return "day-" + str(day - start_day + 1)

def _data():
    data = {}
    data["config"] = site_data["config"]
    return data


# @year_blueprint.route("/year/{}".format(year))
# def index():
#     return render_template('year_redirect.html', site_path='index.html', site_year=2024)

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

@year_blueprint.route("/year/{}/jobs.html".format(year))
def jobs():
    data = _data()
    data["jobs"] = open("sitedata/{}/jobs.md".format(year)).read()
    return render_template("{}/jobs.html".format(year), **data)

@year_blueprint.route("/year/{}/impressions.html".format(year))
def impressions():
    data = _data()
    data["impressions"] = open("sitedata/{}/impressions.md".format(year)).read()
    return render_template("{}/impressions.html".format(year), **data)

@year_blueprint.route("/year/{}/supporters.html".format(year))
def supporters():
    data = _data()
    data["supporters"] = site_data["supporters"]
    data['supporters_extra'] = site_data["supporters_extra"]
    # data["jobs"] = open("sitedata/{}/jobs.md".format(year)).read()
    return render_template("{}/supporters.html".format(year), **data)


@year_blueprint.route("/year/{}/help.html".format(year))
def about():
    data = _data()
    data["discord"] = open("sitedata/{}/discord_guide.md".format(year)).read()
    data["gather"] = open("sitedata/{}/gather_guide.md".format(year)).read()
    data["FAQ"] = site_data["faq"]["FAQ"]
    return render_template("{}/help.html".format(year), **data)


@year_blueprint.route("/year/{}/papers.html".format(year))
def papers():
    data = _data()
    # print("list(site_data['paper_list'].items())[0] is ", list(site_data['paper_list'].items())[0])
    all_paper_types = [p['paper_type'] for _, p in site_data["paper_list"].items()]
    data['paper_types'] = sorted(list(set([(paper_type_names[pt] if pt in paper_type_names else 'None', pt) for pt in all_paper_types])), key=lambda x: x[0])
    data['colors'] = data['config']['calendar']['colors']
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
        data["days"][day] = {"timeslots": collections.OrderedDict(sorted(by_time[day].items()))}

    # all_events = [session for day, ds in by_time.items() for time, ts in ds.items() for session in ts['sessions']]
    # data['events'] = all_events
    print("printing by_time.keys(): ", by_time.keys())
    day_sort_order = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    data['events_by_time'] = collections.OrderedDict(sorted(by_time.items(), key=lambda item: day_sort_order.index(item[0])))
    # print("by_time is ", by_time)
    # data['event_types'] = sorted(list(set([(e['type'], e["type"].split(" ")[0].lower()) for e in all_events])), key=lambda x: x[0])
    data['colors'] = data['config']['calendar']['colors']

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
    # print("problem paper is ", v)
    room_name = get_room_name(paper_session['track'], site_data['config']['room_names'])
    return {
        "id": v["uid"],
        "title": v["title"],
        "authors": list_fields["authors"],
        "keywords": list_fields["keywords"],
        "abstract": v["abstract"],
        "time_stamp": v["time_stamp"],
        "session_id": v["session_id"],
        "session_title": paper_session["title"],
        "session_room": room_name,
        "event_id": paper_session["parent_id"],
        "event_title": paper_event["event"],
        "award": v["paper_award"],
        "has_image": v["has_image"],
        "has_pdf": v["has_pdf"],
        "has_fno": (len(v["fno"]) > 0) if "fno" in v else False,
        "fno": v["fno"] if "fno" in v else None,
        "doi": v["doi"] if "doi" in v else None,
        "image_caption": v["image_caption"],
        "external_paper_link": v["external_paper_link"],
        "youtube_ff_url": v["ff_link"] if "ff_link" in v else None,
        "youtube_ff_id": v["ff_link"].split("/")[-1] if "ff_link" in v and v["ff_link"] else None,
        "prerecorded_video_id": v["prerecorded_video_id"] if "prerecorded_video_id" in v else None,
        "prerecorded_video_link": v["prerecorded_video_link"] if "prerecorded_video_link" in v else None,
        # for papers.html:
        "sessions": [paper_session["title"]],
        "UID": v["uid"],
        "session_uid": "-".join(v["uid"].split("-")[0:-1]) if v["uid"] else "none", # Get rid of the paper ID so we can reach the CDN folder
        "paper_type": v["paper_type"],
        "paper_type_name": paper_type_names[v["paper_type"]] if v["paper_type"] in paper_type_names else 'None',
        "paper_type_color": site_data["config"]['calendar']['colors'][v["paper_type"]],
        "session_youtube_ff_link": v["youtube_ff_link"],
        "session_youtube_ff_id": v["youtube_ff_id"],
        "session_bunny_ff_link": v["bunny_ff_link"],
        "session_bunny_ff_subtitles": v["bunny_ff_subtitles"],
        "session_youtube_prerecorded_link": v["youtube_prerecorded_link"],
        "session_youtube_prerecorded_id": v["youtube_prerecorded_id"],
        "session_bunny_prerecorded_link": v["bunny_prerecorded_link"],
        "session_bunny_prerecorded_subtitles": v["bunny_prerecorded_subtitles"],
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
        "award": "",
        "discord_channel": v["discord_channel"],
        "session_title": v["event"],
        "poster_pdf": "https://ieeevis.b-cdn.net/vis_2024/posters/" + v["uid"] + ".pdf",
        "summary_pdf": "https://ieeevis.b-cdn.net/vis_2024/posters/" + v["uid"] + "-summary.pdf" if v["has_summary_pdf"] == "TRUE" else None,
        "has_image": v["has_image"] == "TRUE",

        # for posters.html
        "sessions": [v["event"]],
        "UID": v["uid"],
        "ff_link": v["ff_link"] if 'ff_link' in v else None
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

    formatted = {
        "id": uid,
        "title": v.get("long_name") if "long_name" in v else v.get("event"),
        "type": v.get("event_type") if "event_type" in v else 'VIS',
        "abbr_type": v["event_type"].split(" ")[0].lower() if "event_type" in v else 'vis',
        "abstract": v.get("event_description") if "event_description" in v else 'None',
        "url": v.get("event_url") if "event_url" in v else '',
        "startTime": v["sessions"] and v["sessions"][0]["time_start"],
        "endTime": v["sessions"] and v["sessions"][-1]["time_end"]
    }

    if v['event'] != 'VISxAI':
        formatted["sessions"] = [format_by_session_list(by_uid["sessions"][timeslot["session_id"]]) for timeslot in v["sessions"]]
    else:
        formatted["sessions"] = []
    return formatted

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
    day = ''
    try:
        day = dateutil.parser.parse(v["time_start"]).astimezone(CONFERENCE_TIMEZONE).strftime("%Y-%m-%d")
    except ParserError:
        print("couldn't parse day, v['time_start'] is ", v['time_start'])

    if v["event"].lower() != v["title"].lower():
        fullTitle += ": " + v["title"]
        redundantTitle = False
    return {
        "id": v["session_id"],
        "title": v["title"],
        "type": v["event_type"]
            .split(" ")[0]
            .lower(),  # get first word, which should be good enough...
        "chair": v.get("chair"),
        "organizers": v.get("organizers"),
        "track": v.get("track"),
        "startTime": v.get("time_start"),
        "endTime": v.get("time_end"),
        "day": day,
        "timeSlots": v.get("time_slots"),
        "event": v.get("event"),  # backloaded from parent event
        "event_type": v.get("event_type"),  # backloaded from parent event
        "parent_id": v.get("parent_id"),  # backloaded from parent event
        "event_description": v.get("event_description"),  # backloaded from parent event
        "event_url": v.get("event_url"),  # backloaded from parent event
        "fullTitle": fullTitle,
        "redundantTitle": redundantTitle,
        "discord_category": v.get("discord_category"),
        "discord_channel": v.get("discord_channel"),
        "discord_channel_id": v.get("discord_channel_id"),
        "discord_link": v.get("discord_link"),
        "slido_link": v.get("slido_link"),
        "youtube_url": v.get("youtube_url"),
        "youtube_id": v.get("youtube_id") if "youtube_id" in v else (v.get("youtube_url").split("/")[-1] if v.get("youtube_url") else None),
        "youtube_rec_url": v.get("youtube_rec_url"),
        "youtube_rec_id": v.get("youtube_rec_id") if "youtube_rec_id" in v else (v.get("youtube_rec_url").split("/")[-1] if v.get("youtube_rec_url") else None),
        "streaming_session_id": v.get("streaming_session_id") if "streaming_session_id" in v else None,
        "livestream_id": v.get("livestream_id") if "livestream_id" in v else None,
        "ff_playlist": v.get("ff_playlist"),
        "ff_playlist_id": v.get("ff_playlist").split("=")[-1] if v.get("ff_playlist") else None,
        "youtube_ff_url": v.get("ff_link") if "ff_link" in v else None,
        "youtube_ff_id": v["ff_link"].split("/")[-1] if "ff_link" in v else None,
        "zoom_meeting": v.get("zoom_meeting"),
        "room_name": v.get("room_name"),
        "livestream_id": v.get("livestream_id"),
    }

def get_room_name(track, room_names):
    # print("ROOM NAMES ARE ", room_names)
    if track in room_names:
        return room_names[track]
    else:
        return "None"

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

    room = data['session']['track']
    room_name = ''
    if 'room_names' in data['config'] and room in data['config']['room_names']:
        room_name = data['config']['room_names'][room]

    data["room"] = {
        'name': room_name,
        'id': room
    }
    return render_template("{}/session.html".format(year), **data)

@year_blueprint.route("/year/{}/room_<room>.html".format(year))
def room(room):
    data = _data()
    room_name = ''
    if 'room_names' in data['config'] and room in data['config']['room_names']:
        room_name = data['config']['room_names'][room]

    all_sessions = [by_uid['sessions'][uid] for uid in by_uid['sessions']]
    room_sessions = [s for s in all_sessions if s['track'] == room]

    room_sessions = sorted(room_sessions, key=lambda x: x and ('time_start' in x) and  x['time_start'])

    data["requires_auth"] = True
    data["sessions"] = [format_by_session_list(v) for v in room_sessions]

    data["room"] = {
        'name': room_name,
        'id': room
    }

    # We need to write a minimal data object to the js so that current session can be calculated.
    # We copy a minimal amount of data there
    data["sessionTimings"] = json.dumps([
            {
                'startTime': s['startTime'],
                'endTime': s['endTime'],
                'id': s['id'],
                'youtube_url': s['youtube_url'],
                'youtube_id': s['youtube_id'],
                'slido_link': s['slido_link'],
                'discord_link': s['discord_link']
            }
        for s in data["sessions"]])


    return render_template("{}/room.html".format(year), **data)

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
    data = _data()
    data["requires_auth"] = True
    return render_template("{}/streaming.html".format(year), **data)

@year_blueprint.route("/year/{}/playback.html".format(year))
def playback():
    data = _data()
    data["requires_auth"] = True
    return render_template("{}/playback.html".format(year), **data)


site_data_path = "sitedata/{}".format(year)
extra_files = main(site_data_path)
