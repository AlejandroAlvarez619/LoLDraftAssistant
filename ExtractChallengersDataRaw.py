import os, requests
from dotenv import load_dotenv
from urllib.parse import quote
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"    # Takes the .env path
load_dotenv(dotenv_path=env_path)    # Reads .env in the workspace root

API_KEY = os.getenv("RIOT_API_KEY")
#print("API key loaded:", bool(API_KEY), "len:", len(API_KEY) if API_KEY else 0)    # Sanity check

if not API_KEY:
    raise RuntimeError("RIOT_API_KEY is not set or .env not loaded.")

region = "euw1"    # br1/eun1/euw1/jp1/kr/la1/la2/me1/na1/oc1/ru/sg2/tr1/tw2/vn2
queue = "RANKED_FLEX_SR"    # RANKED_SOLO_5x5/RANKED_FLEX_SR
url = f"https://{region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/{queue}"    # URL for the HTML request

headers = {"X-Riot-Token": API_KEY}

#print("Using endpoint:", url)
#print("Header token length:", len(API_KEY))
#print("Header first 8 chars:", API_KEY[:8])

resp = requests.get(url, headers=headers)
#print("HTTP", resp.status_code, resp.reason)

if resp.status_code == 200:    # Right response
    data = resp.json()
    tier = data.get("tier", "UNKNOWN")
    entries = data.get("entries", [])
    #print(f"Tier: {tier}, total entries: {len(entries)}")

    for entry in entries[:184]:
        puuid = entry.get("puuid")
        rank_div = entry.get("rank")       # usually "I" for Challenger
        lp = entry.get("leaguePoints")
        print(f"{puuid}")


else:
    # Helpful diagnostics
    print("Response text:", resp.text)
    if resp.status_code == 403:
        print(
            "\n403 Forbidden → Usually an invalid/expired API key or access to a forbiden API.\n"
            "- Regenerate your dev key in the Riot portal.\n"
            "- Update .env and restart your terminal/VS Code.\n"
            "- Make sure load_dotenv() is called before os.getenv().\n"
            "- Ensure you have access to that API."
        )