"""Build data/squads.json from the Wikipedia 2026 World Cup squads page.

Free source; squad tables carry No./Pos./Player/DOB/Caps/Goals/Club.
Run:  python scripts/build_squads.py
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cupcast import config  # noqa: E402

URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"

# Wikipedia article heading -> dataset team name
WIKI_TO_DATASET = {
    "Czechia": "Czech Republic", "Czech Republic": "Czech Republic",
    "Türkiye": "Turkey", "Cabo Verde": "Cape Verde",
    "Côte d'Ivoire": "Ivory Coast", "Ivory Coast": "Ivory Coast",
    "United States": "United States", "South Korea": "South Korea",
    "DR Congo": "DR Congo", "IR Iran": "Iran", "Iran": "Iran",
    "Curaçao": "Curaçao",
}

POS_MAP = {"GK": "Goalkeeper", "DF": "Defender", "MF": "Midfielder", "FW": "Forward"}


def fetch_html():
    req = urllib.request.Request(URL, headers={"User-Agent": "CupCast/1.0 (portfolio project)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    squads = {}
    current = None
    body = soup.find(id="mw-content-text")
    for el in body.descendants:
        if el.name in ("h3", "h2"):
            heading = el.get_text(strip=True)
            heading = re.sub(r"\[edit\]$", "", heading)
            name = WIKI_TO_DATASET.get(heading, heading)
            current = name if name in config.TEAM_GROUP else None
        elif el.name == "table" and current:
            header = el.find("tr")
            if not header or "Caps" not in header.get_text():
                continue
            players = []
            for tr in el.find_all("tr")[1:]:
                cells = tr.find_all(["td", "th"])
                if len(cells) < 7:
                    continue
                texts = [c.get_text(" ", strip=True) for c in cells]
                no, pos, player, dob, caps, goals, club = texts[:7]
                age_m = re.search(r"aged?\s*(\d+)", dob)
                pos_m = re.search(r"\b(GK|DF|MF|FW)\b", pos)
                player = re.sub(r"\s*\(.*?\)$", "", player).replace("(captain)", "").strip()
                try:
                    players.append({
                        "no": int(no) if no.isdigit() else None,
                        "pos": POS_MAP.get(pos_m.group(1) if pos_m else "", pos),
                        "name": player,
                        "age": int(age_m.group(1)) if age_m else None,
                        "caps": int(re.sub(r"\D", "", caps) or 0),
                        "goals": int(re.sub(r"\D", "", goals) or 0),
                        "club": club,
                    })
                except ValueError:
                    continue
            if players:
                squads.setdefault(current, players)
                current = None  # one squad table per team
    return squads


def main():
    print(f"Fetching {URL} ...")
    squads = parse(fetch_html())
    missing = [t for t in config.WC_TEAMS if t not in squads]
    sizes = {t: len(p) for t, p in squads.items()}
    print(f"Parsed {len(squads)} squads; sizes min={min(sizes.values())} max={max(sizes.values())}")
    if missing:
        print(f"WARNING — missing teams: {missing}")
    out = config.DATA_DIR / "squads.json"
    out.write_text(json.dumps(squads, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
