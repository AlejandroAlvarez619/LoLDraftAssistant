import os, requests
from dotenv import load_dotenv
from urllib.parse import quote
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)  # Reads .env in the workspace root

API_KEY = os.getenv("RIOT_API_KEY")
print("API key loaded:", bool(API_KEY), "len:", len(API_KEY) if API_KEY else 0)  # Quick sanity check


if not API_KEY:
    raise RuntimeError("RIOT_API_KEY is not set or .env not loaded.")

summonerName = "Sky Scrabble"
encodedName = quote(summonerName, safe="")
summonerTag = "FIUM"
region = "europe"    # europe/asia/americas

encodedName = quote(summonerName, safe="")    # Link-format accessible name
url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encodedName}/{summonerTag}"


headers = {"X-Riot-Token": API_KEY}

print("Using endpoint:", url)
print("Header token length:", len(API_KEY))
print("Header first 8 chars:", API_KEY[:8])

resp = requests.get(url, headers=headers)
print("HTTP", resp.status_code, resp.reason)

if resp.status_code == 200:
    summonerData = resp.json()
    puuid = summonerData["puuid"]
    print(f"{summonerName}'s PUUID:", puuid)
    print(summonerData)
else:
    # Helpful diagnostics
    print("Response text:", resp.text)
    if resp.status_code == 403:
        print(
            "\n403 Forbidden → Usually an invalid/expired API key.\n"
            "- Regenerate your dev key in the Riot portal.\n"
            "- Update .env and restart your terminal/VS Code.\n"
            "- Make sure load_dotenv() is called before os.getenv()."
        )