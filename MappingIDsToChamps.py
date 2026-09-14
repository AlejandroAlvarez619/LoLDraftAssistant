import pandas as pd
import requests

CSV_IN = "./old/flex_matches_combined_filtered.csv"
CSV_OUT = "./data/flex_matches_combined_named_bans.csv"
LANG = "en_US"  # Names change from region to region

# Data Dragon is the API used by Riot to work with normalized data
def get_dd_version_for_patch(patch_str: str) -> str:
    """Return the DDragon version matching this patch (e.g., '15.19' -> '15.19.1').
    Falls back to the latest if an exact prefix match isn't found."""
    versions = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()

    for v in versions:
        if v.startswith(patch_str + "."):
            return v
        
    # If there's no plus version: try exact or latest
    if patch_str in versions:
        return patch_str
    return versions[0]

# Cache per version, to check if we've already fetched the mapping for the combination of (version, language)
# It will be a dictionary of dictionaries
_dd_cache = {}

def get_id_to_name_map(dd_version: str, lang: str = LANG) -> dict[int, str]:
    """Build {int(key) -> id} mapping for champions from DDragon."""
    # We work with a cache to fasten the compute during the CSV go-through, for not having to make many requests
    # to the API
    cache_key = (dd_version, lang)
    if cache_key in _dd_cache:
        return _dd_cache[cache_key]
    
    url = f"https://ddragon.leagueoflegends.com/cdn/{dd_version}/data/{lang}/champion.json"
    data = requests.get(url).json()["data"]

    # 'key' is the numeric champ ID used in match data. 'name' is the display name
    #id_to_name = {int(info["key"]): info["name"] for info in data.values()} old version, inconsistent names
    id_to_name = {int(info["key"]): info["id"] for info in data.values()}
    _dd_cache[cache_key] = id_to_name
    return id_to_name

# Transforms the string of banned champs ids into banned champs names
def ids_to_names(ids_str: str, id_to_name: dict[int, str]) -> str:
    # If ids_str is empty return an empty string (there are no bans in the game)
    if pd.isna(ids_str) or str(ids_str).strip() == "":
        return ""
    
    out = []
    for tok in str(ids_str).split(","):
        tok = tok.strip()
        if not tok:
            continue
    
        # Normalize the bans values
        try:
            val = int(tok.lstrip("0") or "0")
        except ValueError:
            # Skip it if it's not an integer
            continue

        # Clean no bans
        if val <= 0:
            continue

        name = id_to_name.get(val)
        # If the ID isn't in the map (unknown/bugs), skip it
        if name:
            out.append(name)

    # De-dupe while preserving order
    seen = set()
    cleaned = [x for x in out if not (x in seen or seen.add(x))]
    return ",".join(cleaned)
        
    

# Load the dataframe
df = pd.read_csv(CSV_IN)

# For each patch present in the data, convert its bans field with the corresponding mapping
df_out = df.copy()
# We group the data by patch. Calling df.groupby("patch") groups all rows that have the same patch value
# Calling .groups returns a dictionary where the key is the patch value and the value is a list of row
# positions in the DataFrame that belong to that patch. .items() gives the iterator of (key, value)
for (patch_value, idx) in df.groupby("patch").groups.items():
    dd_ver = get_dd_version_for_patch(str(patch_value))
    id_to_name_dictionary = get_id_to_name_map(dd_ver, LANG)

    # debug
    #print(id_to_name_dictionary)
    #print("\n\n----------------------------------------------------\n\n")

    # apply() applies the function defined for every row in the "bans" column.
    # With the lambda-function we define a one-line function in which we call ids_to_names
    # Combined, for each element s in the bans column of those rows call ids_to_names(s, id_to_name_dictionary)
    df_out.loc[idx, "bans"] = df.loc[idx, "bans"].apply(lambda s: ids_to_names(s, id_to_name_dictionary))

df_out.to_csv(CSV_OUT, index=False)
print(f"Saved with normalized bans in {CSV_OUT}")