import pandas as pd

# Read the dataset
df = pd.read_csv("./data/flex_matches_combined.csv")

# Print how many total and duplicate matches we have
print(f"Total entries: {len(df)}")
print(f"Duplicate matchIds: {df['matchId'].duplicated().sum()}")

# Remove duplicate matchIds, keeping the first occurence
df_unique = df.drop_duplicates(subset=['matchId'], keep='first')

# Keep only the relevant columns
columns_to_keep = ['patch', 'team1_champions', 'team2_champions', 'winner', 'bans']
df_filtered = df_unique[columns_to_keep]

# Save the cleaned dataset to a new CSV file
df_filtered.to_csv("./data/flex_matches_combined_filtered.csv", index=False)

print(f"After removing duplicates: {len(df_unique)}")
print("File 'flex_matches_combined_filtered.csv created successfully.'")