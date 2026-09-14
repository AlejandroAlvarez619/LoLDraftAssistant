import pandas as pd

# Load the original CSV
df = pd.read_csv("./data/flex_matches_combined_named_bans.csv")

# Shuffle the rows (optional but recommended)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Compute the index for 70%
split_index = int(len(df) * 0.7)

# Split into two DataFrames
df_70 = df.iloc[:split_index]
df_30 = df.iloc[split_index:]

# Save them to new CSV files
df_70.to_csv("./data/training.csv", index=False)
df_30.to_csv("./data/testing.csv", index=False)

print("CSV successfully split into 70% and 30%.")
