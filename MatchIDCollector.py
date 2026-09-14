# ExtractFlexMatches.py
# Pulls Ranked Flex (queue 440) matches for a list of Challenger PUUIDs
# Saves a clean CSV with team comps, winner, queueId, patch, etc.

import os
import csv
import time
import json
import math
import random
import logging
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

# -------------------------
# Config
# -------------------------
# Set these to the platform + regional cluster for the accounts you’re scraping.
# Example: EUW -> platform="euw1", region="europe"
#          NA  -> platform="na1",  region="americas"
#          KR  -> platform="kr",   region="asia"
PLATFORM = "euw1"
REGION   = "europe"

QUEUE_ID = 440                 # Ranked Flex 5v5
COUNT_PER_PAGE = 100           # Up to 100 by Riot API
MAX_MATCHES_PER_PUUID = 400    # Adjust as you wish
SLEEP_BETWEEN_PUUIDS = 1.0     # Seconds, light throttle
OUTPUT_CSV = "flex_matches.csv"
PUUIDS_TXT = "data/challenger_puuids.txt"    # one PUUID per line
CHECKPOINT_JSON = "checkpoints/seen_matches.json"    # for resume/dedupe

# -------------------------
# Setup
# -------------------------
ROOT = Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT / ".env")
API_KEY = os.getenv("RIOT_API_KEY")
if not API_KEY:
    raise RuntimeError("RIOT_API_KEY is not set in .env")

HDR = {"X-Riot-Token": API_KEY}

# This sets up Python’s built-in logging system.
# This is better than using plain print() because you can control verbosity, log to files, etc.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# This creates a named logger object called "flex-crawler". The script now can do functions like:
# log.info("Saved 50 rows so far.")
# log.warning("Got 429, sleeping 10s.")

log = logging.getLogger("flex-crawler")

session = requests.Session()    # Creates a reusable HTTP session object
session.headers.update(HDR)     # Adds the Riot API header to every request
session.timeout = 15            # Tells the session to wait at most 15 seconds before giving up on a request

# -------------------------
# Utils
# -------------------------

# Ensures that the directories exist or can be created
def ensure_dirs():
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "checkpoints").mkdir(exist_ok=True)

# Reads the players' PUUIDs from a file that contains a PUUID in each line
# Returns a list of strings
def load_puuids(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"No PUUID file at {path}")
    try:
        # Handles UTF-8
        with path.open("r", encoding="utf-8") as f:    # The with block ensures the file is closed automatically after reading
            # Iterates through every line in the file, removes blank spaces and filters out any blank lines
            # Collects the cleaned lines into a list and returns it
            return [line.strip() for line in f if line.strip()]
    except UnicodeDecodeError:
        # Fallback for UTF-16 LE
        with path.open("r", encoding="utf-16") as f:
            return [line.strip() for line in f if line.strip()]

# Loads a set of match IDs from a JSON file and turns it into a set
def load_seen_matches(path: Path):
    if not path.exists():
        # Returns an empty set if the seen matches file doesn't exist
        return set()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data)
    except Exception:
        return set()
    
# Function to prevent reprocessing some matches and appending duplicates
def load_seen_from_csv(csv_path: Path) -> set:
    if not csv_path.exists():
        return set()
    seen = set()
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r, None)
        for row in r:
            if row:
                seen.add(row[0])  # matchId is first column
    return seen

# Saves the current set of seen match IDs back to seen_macthes file to know which matches have been already processed
def save_seen_matches(path: Path, seen: set):
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(sorted(list(seen)), f)
    tmp.replace(path)

# Handles rate-limit error (429) and server errors (500-599)
def handle_rate_limit(resp):
    if resp.status_code == 429:    # Too many requests
        retry_after = resp.headers.get("Retry-After")
        delay = int(retry_after) if retry_after and retry_after.isdigit() else 10
        log.warning(f"429 Too Many Requests. Sleeping {delay}s")
        time.sleep(delay)
        return True
    if 500 <= resp.status_code < 600:
        log.warning(f"{resp.status_code} server error. Sleeping 5s")
        time.sleep(5)
        return True
    return False

# Gets the match ids by puuid. Can get up to 100 match ids.
def get_match_ids_by_puuid(puuid: str, start: int, count: int, queue: int):
    url = (f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/"
           f"{puuid}/ids?queue={queue}&start={start}&count={count}")
    while True:
        resp = session.get(url)
        if resp.status_code == 200:
            return resp.json()
        if handle_rate_limit(resp):
            continue
        # If there are other errors, log warning and return empty list
        log.warning(f"match-ids {puuid} [{start}:{start+count}] -> {resp.status_code}: {resp.text[:180]}")
        return []

# Gets the match details and results
def get_match_detail(match_id: str):
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    while True:
        resp = session.get(url)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            # Rare, but happens if match expired/not available
            log.info(f"{match_id} -> 404 (skipping)")
            return None
        if handle_rate_limit(resp):
            continue
        log.warning(f"match-detail {match_id} -> {resp.status_code}: {resp.text[:180]}")
        return None

# Returns a flat dictionary row or None if it's not a flex 5v5
def parse_record(match_json: dict):
    try:
        info = match_json["info"]
        if info.get("queueId") != QUEUE_ID:
            return None
        # Participants contain 10 entries
        parts = info["participants"]
        team1 = [p["championName"] for p in parts if p["teamId"] == 100]    # Blue team
        team2 = [p["championName"] for p in parts if p["teamId"] == 200]    # Red team

        # Winner determination
        team1_win = any(p.get("win", False) for p in parts if p["teamId"] == 100)
        winner = "Team1" if team1_win else "Team2"

        # Bans (if provided by endpoint)
        bans = []
        for t in info.get("teams", []):
            for b in t.get("bans", []):
                # b: {"championId": 157, "pickTurn": 1}
                champ_id = b.get("championId")
                if champ_id is not None:
                    bans.append(str(champ_id))

        # Patch major.minor
        gv = info.get("gameVersion", "")
        patch = ""
        if gv:
            # Transform patch to typical form "13.19.523.1234" -> "13.19"
            parts_gv = gv.split(".")
            if len(parts_gv) >= 2:
                patch = f"{parts_gv[0]}.{parts_gv[1]}"

        row = {
            "matchId": match_json["metadata"]["matchId"],
            "region": REGION,
            "platform": PLATFORM,
            "queueId": info.get("queueId"),
            "patch": patch,
            "team1_champions": ",".join(team1),
            "team2_champions": ",".join(team2),
            "winner": winner,
            "bans": ",".join(bans)
        }
        return row
    except Exception as e:
        log.warning(f"parse error: {e}")
        return None

# Write the csv header to the csv file if it's not yet
def append_csv_header_if_needed(csv_path: Path):
    if not csv_path.exists():
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["matchId","region","platform","queueId","patch",
                        "team1_champions","team2_champions","winner","bans"])

# Add a row to the csv file
def append_csv_row(csv_path: Path, row: dict):
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            row["matchId"], row["region"], row["platform"], row["queueId"], row["patch"],
            row["team1_champions"], row["team2_champions"], row["winner"], row["bans"]
        ])

# -------------------------
# Main
# -------------------------
def main():
    ensure_dirs()
    puuids = load_puuids(ROOT / PUUIDS_TXT)
    random.shuffle(puuids)    # Spread load a bit

    append_csv_header_if_needed(ROOT / OUTPUT_CSV)
    seen = load_seen_matches(ROOT / CHECKPOINT_JSON)
    seen |= load_seen_from_csv(ROOT / OUTPUT_CSV)    # Union to avoid duplicates across runs

    log.info(f"Loaded {len(puuids)} PUUIDs. Seen matches so far: {len(seen)}.")

    total_saved = 0
    try:
        # Iterate through all the puuids collected
        for idx, puuid in enumerate(puuids, 1):
            log.info(f"[{idx}/{len(puuids)}] PUUID {puuid[:12]}...")    # Outputs log progress

            # Paginate through match ids
            fetched_ids = 0
            start = 0
            # Each Riot API call only gives up to COUNT_PER_PAGE match IDs
            # This loop keeps requesting games until MAX_MATCHES_PER_PUUID is reached
            while fetched_ids < MAX_MATCHES_PER_PUUID:
                need = min(COUNT_PER_PAGE, MAX_MATCHES_PER_PUUID - fetched_ids)
                mids = get_match_ids_by_puuid(puuid, start=start, count=need, queue=QUEUE_ID)
                if not mids:    # We stop if the API gives back nothing
                    break

                # Iterate through every match
                for mid in mids:
                    if mid in seen:    # Skip matches already processed
                        continue
                    mj = get_match_detail(mid)    # Download full match details
                    if not mj:    # If the API gives back nothing
                        seen.add(mid)
                        continue
                    # Parse into a flat row and write it into the CSV
                    row = parse_record(mj)
                    if row:
                        append_csv_row(ROOT / OUTPUT_CSV, row)
                        total_saved += 1
                        if total_saved % 50 == 0:    # Log every 50 matches
                            log.info(f"Saved {total_saved} rows so far.")
                    seen.add(mid)

                # Update counters
                fetched_ids += len(mids)
                start += len(mids)
                if len(mids) < need:
                    # Fewer than requested -> probably no more matches in the user's history
                    break
            
            # Writes the updated set of seen matches IDs to disk so you can resume later
            save_seen_matches(ROOT / CHECKPOINT_JSON, seen)
            # Sleeps briefly before moving to the next PUUID to be polite with Riots' rate limits
            time.sleep(SLEEP_BETWEEN_PUUIDS)

        log.info(f"Done. Total saved rows: {total_saved}. Unique matches seen: {len(seen)}.")

    except KeyboardInterrupt:
        # If you stop the script with Ctrl + C it still saves the checkpoint of seen match IDs to not lose the progress
        log.warning("Interrupted. Saving checkpoint...")
        save_seen_matches(ROOT / CHECKPOINT_JSON, seen)

if __name__ == "__main__":
    main()
