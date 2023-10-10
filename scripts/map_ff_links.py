# find all ff links for the corresponding papers
# Authors: Janos Zimmermann

import argparse
import json
import os.path
from os import walk

"""
reads the paper_list.json file into a dict
"""


def read_paper_file(paper_file_path):
    d = {}
    with open(paper_file_path, "r+") as f:
        d = json.load(f)

    return d


"""
writes the paper_list.json file from a dict
"""


def write_paper_file(papers, paper_file_path):
    with open(paper_file_path, "w") as f:
        json.dump(papers, f, indent=1)


"""
Takes a collection of papers in the format of paper_key => {paper} and fills papers
with their ff links
"""


def fill_papers_ff_links(papers, ff_dict):
    counter = 0
    for paper_key, paper in papers.items():
        if paper_key in ff_dict:
            papers[paper_key]["ff_link"] = str(ff_dict[paper_key])
            print(str(paper_key) + " -> " + str(papers[paper_key]["ff_link"]))
            counter += 1

    print(
        "We mapped "
        + str(counter)
        + " ff links of total "
        + str(len(papers))
        + " papers"
    )
    return papers


"""
Takes a collection of sessions in the format of session_key => {session} and fills sesssions
with their ff links
"""


def fill_sessions_ff_links(tracks, ff_dict):
    counter = 0
    sessioncounter = 0
    for track_key, track in tracks.items():
        print(track_key)
        for session in tracks[track_key]["sessions"]:
            session_id = session["session_id"]
            # print("    " + session_id)
            sessioncounter += 1
            if session_id in ff_dict:
                ff_string = str(ff_dict[session_id])
                print("   " + str(session_id) + " -> " + str(ff_string))
                session["ff_link"] = ff_string
                session["ff_playlist"] = ff_string
                # tracks[track_key]['sessions'][session_id]['ff_link'] = "https://ieeevis.b-cdn.net/vis_2022/fast_forwards/" + str(ff_dict[session_id])
                counter += 1
            else:
                print("   " + str(session_id))

    print(
        "We mapped "
        + str(counter)
        + " ff links of total "
        + str(sessioncounter)
        + " sessions"
    )
    return tracks


"""
Takes a collection of papers in the format of paper_key => {paper} and fills papers
with their ff links
"""


def fill_poster_ff_links(posters, ff_dict):
    counter = 0
    for poster_key, poster in posters.items():
        print(poster_key)
        if poster_key in ff_dict:
            papers[poster_key]["ff_link"] = str(ff_dict[poster_key])
            print(str(poster_key) + " -> " + str(ff_dict[poster_key]))
            counter += 1
        else:
            papers[poster_key]["ff_link"] = ""

    print(
        "We mapped "
        + str(counter)
        + " ff links of total "
        + str(len(posters))
        + " poster"
    )
    return posters


# schema
# read: paper (key) => title
# write: paper(key) => ff link


def parse_arguments():
    parser = argparse.ArgumentParser(description="FF link arguments")

    parser.add_argument(
        "-y",
        "--year",
        type=str,
        default="2021",
        help="which year to update (i.e. sitedata/2021/paper_list.json",
    )
    parser.add_argument(
        "-f",
        "--paper_file",
        default="paper_list.json",
        help="file in sitedata that we are updating",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    paper_filepath = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "sitedata",
            args.year,
            args.paper_file,
        )
    )
    papers = read_paper_file(paper_filepath)

    print(len(papers))

    folder_with_ff_videos = (
        ""  # //TODO fill in the path to your local download of the ff-videos
    )
    ff_filenames = next(walk(folder_with_ff_videos), (None, None, []))[2]

    ff_dict = {}
    for full_name in ff_filenames:
        if "posters" in full_name:
            ff_dict[full_name.split(".")[0]] = full_name.split(".")[0]
        else:
            ff_dict[full_name.split("_")[0]] = full_name.split(".")[0]

    if args.paper_file == "paper_list.json":
        filled_papers = fill_papers_ff_links(papers, ff_dict)
        write_paper_file(filled_papers, paper_filepath)

    if args.paper_file == "poster_list.json":
        filled_papers = fill_poster_ff_links(papers, ff_dict)
        write_paper_file(filled_papers, paper_filepath)

    # if args.paper_file == 'session_list.json':
    # filled_sessions = fill_sessions_ff_links(papers, ff_dict)
    # write_paper_file(filled_sessions, paper_filepath)
