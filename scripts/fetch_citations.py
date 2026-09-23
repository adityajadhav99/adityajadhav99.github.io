#!/usr/bin/env python3
"""
fetch_citations.py - Automated Citation Scraper and Synchronizer
Fetches live citation counts from Aditya Jadhav's Google Scholar Profile
and open academic APIs (OpenAlex), updating data/citations.json.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime

SCHOLAR_USER_ID = "gYYQk30AAAAJ"
SCHOLAR_URL = f"https://scholar.google.com/citations?user={SCHOLAR_USER_ID}&hl=en"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "citations.json")

# Map of paper titles/keywords to their metadata
KNOWN_PAPERS = {
    "10.1016/j.oceaneng.2023.116011": {
        "id": "oceaneng-2023",
        "title": "Collision Avoidance for Autonomous Surface Vessels Using Novel Artificial Potential Fields",
        "title_keyword": "collision avoidance",
        "default_cites": 42,
        "scholar_view_url": f"https://scholar.google.com/citations?view_op=view_citation&hl=en&user={SCHOLAR_USER_ID}&citation_for_view={SCHOLAR_USER_ID}:UeHWp8X0CEIC",
        "scholar_cites_url": "https://scholar.google.com/scholar?oi=bibs&hl=en&cites=17630434691432960012"
    },
    "10.1115/OMAE2023-104644": {
        "id": "omae-2023",
        "title": "Data Driven Identification of Ship Maneuvering Coefficients",
        "title_keyword": "maneuvering",
        "default_cites": 9,
        "scholar_view_url": f"https://scholar.google.com/citations?view_op=view_citation&hl=en&user={SCHOLAR_USER_ID}&citation_for_view={SCHOLAR_USER_ID}:qjMakFHDy7sC",
        "scholar_cites_url": "https://scholar.google.com/scholar?oi=bibs&hl=en&cites=13141983219490277131"
    }
}


def fetch_from_scholar():
    """Attempt to scrape metrics directly from the user's public Google Scholar profile."""
    req = urllib.request.Request(
        SCHOLAR_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            
        # Parse table of metrics: Citations, h-index, i10-index
        # Format: <td class="gsc_rsb_std">51</td>...
        stats = re.findall(r'<td class="gsc_rsb_std">(\d+)</td>', html)
        total_citations = int(stats[0]) if len(stats) >= 1 else None
        h_index = int(stats[2]) if len(stats) >= 3 else None
        i10_index = int(stats[4]) if len(stats) >= 5 else None

        # Parse individual papers
        paper_citations = {}
        for tr in re.finditer(r'<tr class="gsc_a_tr">(.*?)</tr>', html, re.DOTALL):
            row = tr.group(1)
            title_m = re.search(r'class="gsc_a_at"[^>]*>(.*?)</a>', row)
            cites_m = re.search(r'class="gsc_a_ac gs_ibl"[^>]*>(\d*)</a>', row)
            if title_m and cites_m:
                t_lower = title_m.group(1).lower()
                c_val = int(cites_m.group(1)) if cites_m.group(1) else 0
                for doi, meta in KNOWN_PAPERS.items():
                    if meta["title_keyword"] in t_lower:
                        paper_citations[doi] = c_val

        return {
            "success": True,
            "total_citations": total_citations,
            "h_index": h_index,
            "i10_index": i10_index,
            "paper_citations": paper_citations
        }
    except Exception as e:
        print(f"Google Scholar fetch warning: {e}", file=sys.stderr)
        return {"success": False, "error": str(e)}


def fetch_from_openalex(doi):
    """Fetch live citation count from OpenAlex open API as fallback/cross-check."""
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    req = urllib.request.Request(url, headers={"User-Agent": "mailto:jadhav.aditya127@gmail.com"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("cited_by_count", 0)
    except Exception as e:
        print(f"OpenAlex fetch error for {doi}: {e}", file=sys.stderr)
        return None


def main():
    # Load current cached data if available
    current_data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception:
            pass

    scholar_res = fetch_from_scholar()

    total_citations = current_data.get("total_citations", 51)
    h_index = current_data.get("h_index", 2)
    i10_index = current_data.get("i10_index", 1)
    papers_data = current_data.get("papers", {})

    if scholar_res.get("success") and scholar_res.get("total_citations") is not None:
        total_citations = scholar_res["total_citations"]
        if scholar_res.get("h_index") is not None:
            h_index = scholar_res["h_index"]
        if scholar_res.get("i10_index") is not None:
            i10_index = scholar_res["i10_index"]
        
        for doi, count in scholar_res.get("paper_citations", {}).items():
            if doi not in papers_data:
                papers_data[doi] = KNOWN_PAPERS[doi].copy()
            papers_data[doi]["citations"] = count
    else:
        print("Using OpenAlex / fallback checking...")
        computed_total = 0
        for doi, meta in KNOWN_PAPERS.items():
            alex_count = fetch_from_openalex(doi)
            cached_count = papers_data.get(doi, {}).get("citations", meta["default_cites"])
            # Google Scholar citations are typically >= OpenAlex (due to preprints/theses)
            chosen_count = max(cached_count, alex_count or 0)
            if doi not in papers_data:
                papers_data[doi] = meta.copy()
            papers_data[doi]["citations"] = chosen_count
            computed_total += chosen_count
        total_citations = max(total_citations, computed_total)

    # Ensure all known papers have their full metadata
    for doi, meta in KNOWN_PAPERS.items():
        if doi not in papers_data:
            papers_data[doi] = meta.copy()
        for k in ["id", "title", "scholar_view_url", "scholar_cites_url"]:
            papers_data[doi][k] = meta[k]
        if "title_keyword" in papers_data[doi]:
            del papers_data[doi]["title_keyword"]
        if "default_cites" in papers_data[doi]:
            del papers_data[doi]["default_cites"]

    updated_record = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "author": "Aditya Kailas Jadhav",
        "scholar_user_id": SCHOLAR_USER_ID,
        "scholar_profile_url": SCHOLAR_URL,
        "total_citations": total_citations,
        "h_index": h_index,
        "i10_index": i10_index,
        "papers": papers_data
    }

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_record, f, indent=2, ensure_ascii=False)

    print(f"Successfully updated {DATA_FILE}")
    print(f"Total Citations: {total_citations} | h-index: {h_index} | i10-index: {i10_index}")
    for doi, p in papers_data.items():
        print(f"  - {doi}: {p.get('citations')} citations")


if __name__ == "__main__":
    main()

