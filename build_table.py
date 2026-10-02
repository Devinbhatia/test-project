#!/usr/bin/env python3
"""Build the open-jobs funnel table from saved Exelare pipeline pages.

Inputs
  data/active_jobs.csv      Active jobs (id|title|created|user|company)
  data/counts_partial.json  Submitted / Interview / Potential counts per job
  Received page files       JSON dumps of search_candidate_pipeline (stage=Received)
                            passed as arguments (or via --glob)

Output
  data/open_jobs_table.csv  and  data/open_jobs_table.html
"""
import argparse, csv, glob, html, json, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
COLS = ["Job Title", "Date Created", "Status", "User ID", "Company Name",
        "Received", "Potential", "Submitted", "Interview"]


def load_jobs():
    with open(os.path.join(DATA, "active_jobs.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="|"))


def load_received(paths):
    """Count Received rows per job id; dedupe pages by (job, candidate, date)."""
    seen, counts = set(), collections.Counter()
    for p in paths:
        d = json.load(open(p))
        if "Received" not in d.get("summary", ""):
            continue
        for r in d["rows"]:
            key = (r["jobId"], r["candidate"], r["dateAndTime"])
            if key in seen:
                continue
            seen.add(key)
            counts[r["jobId"]] += 1
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", help="glob of saved pipeline page files")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    paths = list(a.files) + (glob.glob(a.glob) if a.glob else [])

    jobs = load_jobs()
    partial = json.load(open(os.path.join(DATA, "counts_partial.json")))
    received = load_received(paths)

    rows = []
    for j in jobs:
        i = j["id"]
        rows.append([j["title"].strip(), j["created"], "Active", j["user"],
                     j["company"].strip(), received.get(i, 0),
                     partial["potential"].get(i, 0),
                     partial["submitted"].get(i, 0),
                     partial["interview"].get(i, 0)])

    with open(os.path.join(DATA, "open_jobs_table.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        w.writerows(rows)

    th = "".join(f"<th>{html.escape(c)}</th>" for c in COLS)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r)
                   + "</tr>" for r in rows)
    with open(os.path.join(DATA, "open_jobs_table.html"), "w",
              encoding="utf-8") as f:
        f.write("<!doctype html><meta charset=utf-8><title>Open Jobs</title>"
                "<style>body{font:14px sans-serif;margin:16px}"
                "table{border-collapse:collapse}th,td{border:1px solid #888;"
                "padding:4px 8px}th{background:#eee}</style>"
                f"<table><tr>{th}</tr>{body}</table>")
    print(f"{len(rows)} jobs; Received total matched to active jobs: "
          f"{sum(r[5] for r in rows)} of {sum(received.values())} rows read")


if __name__ == "__main__":
    main()
