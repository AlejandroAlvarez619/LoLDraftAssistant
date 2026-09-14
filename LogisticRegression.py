import itertools
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import random
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(BASE_DIR, "data", "training.csv")

dataframe = pd.read_csv(data_path)

# Converts each cell into a list of champion names
def parseData(cell):
    if pd.isna(cell):
        return []
    parts = [p.strip() for p in str(cell).replace(";", ",").split(",")]
    return [p for p in parts if p]

# Create parsed columns for t1, t2 and bans
dataframe["t1"]   = dataframe["team1_champions"].apply(parseData)
dataframe["t2"]   = dataframe["team2_champions"].apply(parseData)
dataframe["bans"] = dataframe["bans"].apply(parseData)

# Build the labeled vector. 1 if Team1 won, 0 otherwise
y = (dataframe["winner"].str.strip().str.lower() == "team1").astype(int).values

# Build a dictionary of all champions in dataset
possibleChamps = sorted(
                    set(itertools.chain.from_iterable(dataframe["t1"])) |
                    set(itertools.chain.from_iterable(dataframe["t2"])) |
                    set(itertools.chain.from_iterable(dataframe["bans"]))
                    )

# Create a unique integer index for each champion
champToDictPos = {c:i for i,c in enumerate(possibleChamps)}
n = len(possibleChamps)

# Compute inter-team champion pairs
pairs = sorted({(c1, c2)
                for t1, t2 in zip(dataframe["t1"], dataframe["t2"])
                for c1 in t1 for c2 in t2
                if c1 in champToDictPos and c2 in champToDictPos})

# Assign a possition to each pair
pairToDictPos = {p: i for i, p in enumerate(pairs)}
m = len(pairs)

# Convert each match (row) into a features vector
def row_to_features(t1_list, t2_list, bans_list):
    x = np.zeros(3*n + m, dtype=np.float32)
    for c in t1_list:
        if c in champToDictPos: x[champToDictPos[c]] = 1.0               # T1 block
    for c in t2_list:
        if c in champToDictPos: x[n + champToDictPos[c]] = 1.0           # T2 block
    for c in bans_list:
        if c in champToDictPos: x[2*n + champToDictPos[c]] = 1.0         # BAN block
    offset = 3 * n
    for c1 in t1_list:
        if c1 not in champToDictPos: continue
        for c2 in t2_list:
            if c2 not in champToDictPos: continue
            p = (c1, c2)
            idx = pairToDictPos.get(p)
            if idx is not None:
                x[offset + idx] = 1.0
    return x

# Build the full training matrix
X = np.vstack([row_to_features(t1, t2, b) for t1, t2, b in zip(dataframe["t1"], dataframe["t2"], dataframe["bans"])])

model = LogisticRegression(
    penalty = "l1",
    C = 0.1,
    max_iter = 1000,
    class_weight = None,
    solver = "liblinear"
)

model.fit(X, y)

def recommend_next_pick(enemyTeam, currentPicks = None, bans = None, k = 1):
    """
    enemyTeam: list[str] (5 champs picked by enemy team)
    currentPicks: list[str] (4 champs picked by team)
    bans: list[str] (10 champs banned)
    Returns top champions that maximize win probability.
    """
    currentPicks = currentPicks or []
    bans = bans or []

    blacklistedChamps = set(currentPicks) | set(enemyTeam) | set(bans)
    champsLeft = [c for c in possibleChamps if c not in blacklistedChamps]

    results = []
    for c in champsLeft:
        t1_trial = currentPicks + [c]
        x = row_to_features(t1_trial, enemyTeam, bans).reshape(1, -1)
        p = model.predict_proba(x)[0,1]
        results.append((c, float(p)))

    results.sort(key = lambda x: x[1], reverse = True)
    return results[:k]

def probability(ours_list, enemy_list, bans_list):
    x = row_to_features(ours_list, enemy_list, bans_list).reshape(1, -1)
    return float(model.predict_proba(x)[0, 1])

def demo_one_step_recommendation(seed: int = 0):
    """
    Reproduce the original behavior: pick a random enemy team, our 4 champs
    and bans; compute base probability and top 5 recommendations for the
    final pick.

    Using a fixed seed makes the scenario reproducible.
    """
    random.seed(seed)

    enemy = random.sample(possibleChamps, 5)
    ours = random.sample([c for c in possibleChamps if c not in enemy], 4)
    bans = random.sample([c for c in possibleChamps if c not in enemy + ours], 10)

    print("\n--- One-step recommendation demo ---")
    print("Enemy team:", ", ".join(enemy))
    print("Our picks: ", ", ".join(ours))
    print("Bans:      ", ", ".join(bans))

    base_prob = probability(ours, enemy, bans)
    top_recos = recommend_next_pick(enemyTeam=enemy, currentPicks=ours, bans=bans, k=5)

    print(f"\nBase win prob with current 4 picks: {base_prob:.3f}")
    print("Top recommendations:")
    for champ, prob in top_recos:
        print(f"  {champ}: {prob:.3f} ({prob - base_prob:+.3f})")

    best_champ, best_p = top_recos[0]
    print(f"\nBest pick right now: {best_champ} (predicted win prob {best_p:.3f})")

def main():
    
    demo_one_step_recommendation(seed=0)


if __name__ == "__main__":
    main()    