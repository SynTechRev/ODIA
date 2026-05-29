"""Multi-term Questys Search harvester.

Strategy:
- The public Search/Default.aspx?q=<term> URL returns up to 50 results per
  query, but only indexes filenames (not full-text) and only docs flagged
  public-searchable. By issuing many varied queries we maximize coverage
  of the BOS-relevant subset of the archive.

Output: _questys_harvested_ids.json with deduped File.ashx IDs +
        per-ID filename / extension / search-term-that-found-it.

Run-time: ~5-10 minutes (one Questys round-trip per query, 50+ queries).
"""
import json
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
SEARCH = BASE + "Search/Default.aspx"


# Search terms — biased toward civic-accountability vocabulary that BOS
# agendas / packets / staff reports tend to use in filenames. The Questys
# search only indexes filenames so generic year/keyword queries are the
# best high-coverage strategy.
QUERIES = [
    # Document-type keywords
    "agenda", "minute", "minutes", "resolution", "ordinance", "appendix",
    "staff", "report", "memo", "memorandum", "summary", "packet",
    "presentation", "exhibit", "attachment", "exhibit a", "exhibit b",
    "contract", "agreement", "amendment", "addendum", "extension",
    "RFP", "RFQ", "bid", "proposal", "award", "purchase",
    "appointment", "appointing", "appoint",
    "allocation", "appropriation", "budget", "fiscal", "expenditure",
    "hearing", "notice", "public hearing", "PSA",
    "approval", "approve", "consent", "action",
    # Body-of-government keywords (BOS-specific)
    "board", "supervisor", "supervisors", "BOS",
    # Year-anchored (catches dated filenames like "AGENDA 14 MAR 2006")
    "2025", "2024", "2023", "2022", "2021", "2020",
    "2019", "2018", "2017", "2016", "2015",
    "2014", "2013", "2012", "2011", "2010", "2009", "2008", "2007", "2006",
    # Department / function (catches non-BOS but accountability-relevant)
    "sheriff", "fire", "health", "housing", "planning", "transit",
    "grant", "settlement", "litigation", "lawsuit",
    "personnel", "salary", "pension", "benefit",
]


def harvest():
    sess = requests.Session(impersonate=UA)
    sess.get(SEARCH, timeout=30)  # establish session

    # ID -> {filename, ext, found_via: [terms], first_seen_at}
    catalog: dict[int, dict] = {}

    for i, q in enumerate(QUERIES):
        try:
            url = f"{SEARCH}?q={q.replace(' ', '+')}"
            r = sess.get(url, timeout=60)
            soup = BeautifulSoup(r.text, "html.parser")

            # File.ashx IDs always appear in iframe-preview hrefs:
            #   javascript:ShowIframeModal("../File.ashx?id=N&v=V&isSearch=true", ...)
            ids = sorted(set(int(m) for m in re.findall(r"File\.ashx\?id=(\d+)", r.text)))

            # Try to also pair each ID with its filename from the result grid.
            # Each result row's cell[5] holds the filename.
            grid_ids_with_fnames: dict[int, str] = {}
            for row in soup.select("tr"):
                cells = row.find_all("td")
                if len(cells) < 6:
                    continue
                # row href ID
                row_ids = re.findall(r"File\.ashx\?id=(\d+)", str(row))
                if not row_ids:
                    continue
                row_id = int(row_ids[0])
                # filename is in cell[5] typically; some rows have it in cell[3]
                for cell_idx in (5, 4, 3):
                    if cell_idx < len(cells):
                        txt = cells[cell_idx].get_text(" ", strip=True)
                        if txt and "." in txt:  # plausible filename
                            grid_ids_with_fnames[row_id] = txt
                            break

            # Detect result-count text ("10 Results", "0 Results")
            count_match = re.search(r"(\d+)\s+Results?", r.text)
            count = int(count_match.group(1)) if count_match else None

            new_ids = 0
            for did in ids:
                if did not in catalog:
                    catalog[did] = {
                        "filename": grid_ids_with_fnames.get(did, ""),
                        "ext": (grid_ids_with_fnames.get(did, "").rsplit(".", 1)[-1].lower()
                                if "." in grid_ids_with_fnames.get(did, "") else ""),
                        "found_via": [q],
                    }
                    new_ids += 1
                else:
                    if q not in catalog[did]["found_via"]:
                        catalog[did]["found_via"].append(q)
                    # Backfill filename if missing
                    if not catalog[did]["filename"] and grid_ids_with_fnames.get(did):
                        fn = grid_ids_with_fnames[did]
                        catalog[did]["filename"] = fn
                        if "." in fn:
                            catalog[did]["ext"] = fn.rsplit(".", 1)[-1].lower()

            print(f"  [{i+1:>2}/{len(QUERIES)}] q={q!r:<22} returned {len(ids):>3} hits "
                  f"(count={count!s:<4}) — {new_ids} new ({len(catalog)} total)")
        except Exception as exc:
            print(f"  [{i+1:>2}/{len(QUERIES)}] q={q!r} FAILED: {exc}")
        # Be polite — small pause between queries
        time.sleep(0.5)

    return catalog


if __name__ == "__main__":
    print(f"=== Questys multi-term harvest ({len(QUERIES)} queries) ===\n")
    catalog = harvest()

    # Persist
    out = {
        "harvested_at_unix": int(time.time()),
        "query_count": len(QUERIES),
        "total_unique_ids": len(catalog),
        "ids": catalog,
    }
    Path("_questys_harvested_ids.json").write_text(json.dumps(out, indent=2))

    # Summary by extension
    from collections import Counter
    ext_dist = Counter(meta["ext"] or "(unknown)" for meta in catalog.values())
    print(f"\n=== summary ===")
    print(f"  unique IDs: {len(catalog)}")
    print(f"  extension distribution:")
    for ext, c in ext_dist.most_common(10):
        print(f"    {ext:<12} {c}")
    print(f"\n  saved to _questys_harvested_ids.json")
