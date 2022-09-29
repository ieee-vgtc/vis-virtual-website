# replace_pdfs_with_dois.py
# Authors: Dylan Cashman and Janos Zimmermann
#
# After the conference is over, our agreement with the publishing company states
# we have to take down PDFs and link to DOIs instead.  This is handled by 
# updating the paper_list.json file.  
#
# This script first removes all PDF links from the paper_list.json file, and
# then does a DOI lookup using the habanero package, which uses the crossref
# API to search by title, since that's all that we have.  
#
# Our approach is overly conservative, so if there is any mismatch in title, we just
# say we couldn't find a doi.

import argparse
import os.path
import json
from habanero import Crossref
import requests
from difflib import SequenceMatcher
import codecs

def get_client():
    return Crossref()

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
    with open(paper_file_path, 'w') as f:
        json.dump(papers, f, indent=1)

"""
Uses habanero package to look up a doi given a title.
If the first title received from DOI perfectly matches our title, then we
return that DOI.  In all other cases, we return an empty string.
"""
def find_doi_from_title(title, crossref_client, counter):
    x = crossref_client.works(title=title)
    items = x['message']['items']
    first_item = items[0]
    print(first_item)
    title_from_crossref = str(first_item['title'])
    doi_from_crossref = first_item['doi']
    title_match_ratio = SequenceMatcher(None, title, title_from_datacite).ratio()
    if title_match_ratio > 0.8:
        print("found DOI: " + str(doi_from_crossref) +" with a title match of " + str(title_match_ratio) + " with crossref")
        return doi_from_crossref, (counter + 1)
        #print("found DOI: " + str(first_item['doi']))
    else:
        return "", counter


"""
Uses request to send a query to datacite.org and retrieve data for the given title as json.
If the first title received from DOI matches our title with a ratio of 0.8 or above,
then we return that DOI. DataCite API: https://support.datacite.org/docs/api-queries
If there is no data found from datacite.org we do not search any further but this could be expanded by:
- Crossref limits the requests per IP and is slow
- IEEE Xplore Needs an API Key but would probably be the best as the dois will link to ieee instead of arxiv
- ACM digital Library is member of Crossref with ID 320. Scaping the seach with curl would be another solution.
"""
def find_doi_from_datacite(title, counter):
    # We remove text within '()' and remove special characters, as they corrupt the request as '-' and ':'
    title = title.replace('-', ' ').replace(':', '').split('(')[0]
    url = 'https://api.datacite.org/dois?query='+str(title)

    response = requests.get(url)
    paper_json = response.json()
    if len(paper_json['data']) == 0:
        return "", counter
    first_item = paper_json['data'][0]
    title_from_datacite = first_item['attributes']['titles'][0]['title']
    doi_from_datacite = first_item['attributes']['doi']
    title_match_ratio = SequenceMatcher(None, title, title_from_datacite).ratio()
    if title_match_ratio > 0.8:
        print("found DOI: " + str(doi_from_datacite) +" with a title match of " + str(title_match_ratio) + " with datacite")
        return "doi.org/"+doi_from_datacite, (counter + 1)
    else:
        return "", counter

"""
A good overview about the crossref api query: https://github.com/CrossRef/rest-api-doc
It should be faster + no timeout when mailto is provided
"""
def find_doi_from_crossref(title, counter):
    # We remove text within '()'
    title = title.replace('&','').split('(')[0]
    url = 'https://api.crossref.org/works?query.bibliographic='+str(title)+'&rows=1'

    response = requests.get(url)
    paper_json = response.json()
    if len(paper_json['message']['items']) == 0:
        return "", counter
    first_item = paper_json['message']['items'][0]
    title_from_crossref = first_item['title']
    doi_from_crossref = first_item['DOI']
    title_match_ratio = SequenceMatcher(None, title, title_from_crossref).ratio()
    if title_match_ratio > 0.8:
        print("found DOI: " + str(doi_from_crossref) +" with a title match of " + str(title_match_ratio) + " with crossref")
        return "doi.org/"+doi_from_crossref, (counter + 1)
    else:
        return "", counter

"""
A good overview about the xplore api query: https://developer.ieee.org/Python_Software_Development_Kit
Its limited to 10 calls a second and 200 per day
The calls per day were changed to 500 after a friendly request from us as we got more than 200 papers
"""
def find_doi_from_xplore(title, counter):
    # We replace spaces with '+'
    title = title.replace(' ','+')

    url = 'http://ieeexploreapi.ieee.org/api/v1/search/articles?querytext='+str(title)+'&format=json&apikey=mj5w89ftt9c283fpxeskhw3q'

    response = requests.get(url)
    paper_json = response.json()
    if paper_json['total_records'] == 0:
        return "", counter
    first_item = paper_json['articles'][0]
    title_from_xplore = first_item['title']
    doi_from_xplore = first_item['doi']
    title_match_ratio = SequenceMatcher(None, title, title_from_xplore).ratio()
    if title_match_ratio > 0.8:
        print("found DOI: " + str(doi_from_xplore) +" with a title match of " + str(title_match_ratio) + " with xplore")
        return "doi.org/"+doi_from_xplore, (counter + 1)
    else:
        return "", counter


"""
Takes a dictionary representing a paper, and returns a dictionary with external_paper_link filled in
If a doi already exists on the title, we leave it.  Otherwise, we look it up with xplore, datacite and crossref
"""
def insert_doi_from_title(paper, crossref_client, counter):
    if 'external_paper_link' not in paper or (len(str(paper['external_paper_link'])) == 0):
        counter_before_xplore = counter
        print(paper['title'])
        paper['external_paper_link'], counter = find_doi_from_xplore(paper['title'], counter)
        # If we could not find the doi via xplore, we try datacite but it mostly links to arxiv
        if counter == counter_before_xplore:
            paper['external_paper_link'], counter = find_doi_from_datacite(paper['title'], counter)

        # If we could not find the doi via datacite, we could try crossref but its slow and up to now, didn not get a single match
        #if counter == counter_before_datacite:
            #paper['external_paper_link'], counter = find_doi_from_crossref(paper['title'], counter)
        #paper['external_paper_link'], counter = find_doi_from_title(paper['title'], crossref_client, counter)
    return paper, counter

"""
Takes a collection of papers in the format of paper_key => {paper} and fills papers
with their external_paper_link
"""
def fill_dois(papers, crossref_client):
    counter = 0
    for paper_key, paper in papers.items():
        new_paper, counter = insert_doi_from_title(paper, crossref_client, counter)
        papers[paper_key] = new_paper
    
    print("FOUND DOIs for ", counter, " papers")
    return papers

# schema
# read: paper (key) => title
# write: paper(key) => external_paper_link

def parse_arguments():
    parser = argparse.ArgumentParser(description="DOI API arguments")

    parser.add_argument("-y", "--year", type=str, default='2021', help="which year to update (i.e. sitedata/2021/paper_list.json")
    parser.add_argument("-f", "--paper_file", default='paper_list.json', help="file in sitedata that we are updating")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    crossref_client = get_client()
    paper_filepath = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sitedata', args.year, args.paper_file))
    papers = read_paper_file(paper_filepath)


    filled_papers = fill_dois(papers, crossref_client)
    write_paper_file(filled_papers, paper_filepath)

    # tokenizer = transformers.AutoTokenizer.from_pretrained("deepset/sentence_bert")


