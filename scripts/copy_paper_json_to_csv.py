import argparse
import csv
import json
import pandas

def parse_arguments():
    parser = argparse.ArgumentParser(description="convert paper_list.json to papers.csv")

    parser.add_argument("papers", default=False, help="papers file to parse")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    csv_out=[]
    df = pandas.read_json(args.papers)
    df.to_csv("papers.csv")
    # with open(args.papers, "r") as f:
    #     d = json.load(f)


    #     abstracts = list(csv.DictReader(f))
    #     all_abstracts = torch.zeros(len(abstracts), 768)
    #     with torch.no_grad():
    #         for i, row in enumerate(abstracts):
    #             input_ids = torch.tensor([tokenizer.encode(row["abstract"])[:512]])
    #             all_hidden_states, _ = model(input_ids)[-2:]
    #             all_abstracts[i] = all_hidden_states.mean(0).mean(0)
    #             print(i)
    # torch.save(all_abstracts, "embeddings.torch")
