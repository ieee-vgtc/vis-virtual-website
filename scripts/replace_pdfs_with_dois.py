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
        json.dump(papers, f)

"""
Uses habanero package to look up a doi given a title.
If the first title received from DOI perfectly matches our title, then we
return that DOI.  In all other cases, we return an empty string.
"""
def find_doi_from_title(title, crossref_client, counter):
    x = crossref_client.works(title=title)
    items = x['message']['items']
    first_item = items[0]
    print(first_item['title'])
    if first_item and first_item['title'] == title:
        return first_item['doi'], (counter + 1)
    else:
        return "", counter

"""
Takes a dictionary representing a paper, and returns a dictionary with external_paper_link filled in
If a doi already exists on the title, we leave it.  Otherwise, we look it up.
"""
def insert_doi_from_title(paper, crossref_client, counter):
    if 'external_paper_link' not in paper or (len(str(paper['external_paper_link'])) == 0):
        paper['external_paper_link'], counter = find_doi_from_title(paper['title'], crossref_client, counter)
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

    # model = transformers.AutoModel.from_pretrained("deepset/sentence_bert")
    # model.eval()

    # with open(args.papers, "r") as f:
    #     abstracts = list(csv.DictReader(f))
    #     all_abstracts = torch.zeros(len(abstracts), 768)
    #     with torch.no_grad():
    #         for i, row in enumerate(abstracts):

    #             input_ids = torch.tensor([tokenizer.encode(row["abstract"])[:512]])
    #             all_hidden_states, _ = model(input_ids)[-2:]
    #             all_abstracts[i] = all_hidden_states.mean(0).mean(0)
    #             print(i)
    # torch.save(all_abstracts, "embeddings.torch")
