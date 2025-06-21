import pandas as pd
from rapidfuzz import fuzz, process

# Load Excel files
output_directory = 'output/events/';
output_file_name = 'matched_runsignup_trifind_events_2025';

runsignup = pd.read_excel(output_directory + 'runsignup_triathlon_duathlon_aquathlon_aqua_bike_swim_run_2025.xlsx', sheet_name='All Events')
trifind = pd.read_excel(output_directory + 'trifind_paginated_events.xlsx', sheet_name='All Events')

# Ensure needed columns are present
runsignup = runsignup[['title', 'state']].dropna()
trifind = trifind[['title', 'state', 'usat_sanctioned']].dropna()

# Normalize titles
runsignup['title_norm'] = runsignup['title'].str.lower().str.strip()
trifind['title_norm'] = trifind['title'].str.lower().str.strip()

# Perform fuzzy matching
all_matches = []

for _, rs in runsignup.iterrows():
    candidates = trifind[trifind['state'] == rs['state']]
    if not candidates.empty:
        match, score, _ = process.extractOne(rs['title_norm'], candidates['title_norm'], scorer=fuzz.ratio)
        trifind_match = candidates[candidates['title_norm'] == match].iloc[0]

        all_matches.append({
            'runsignup_title': rs['title'],
            'trifind_title': trifind_match['title'],
            'state': rs['state'],
            'match_score': score,
            'usat_sanctioned': trifind_match['usat_sanctioned']
        })
    else:
        all_matches.append({
            'runsignup_title': rs['title'],
            'trifind_title': None,
            'state': rs['state'],
            'match_score': 0,
            'usat_sanctioned': 'Unknown'
        })

# Convert to DataFrame
df_matches = pd.DataFrame(all_matches)

# Create score bins
bins = [0, 69, 79, 89, 94, 100]
labels = ['0–69', '70–79', '80–89', '90–94', '95–100']
df_matches['score_bin'] = pd.cut(df_matches['match_score'], bins=bins, labels=labels, right=True, include_lowest=True)

# Count by score bin
summary = df_matches['score_bin'].value_counts().sort_index().reset_index()
summary.columns = ['match_score_bin', 'count']

# Save to Excel
with pd.ExcelWriter(output_directory + output_file_name + '.xlsx') as writer:
    df_matches.to_excel(writer, sheet_name='Matches', index=False)
    summary.to_excel(writer, sheet_name='Score Summary', index=False)

# Print summary to console
print("\n📊 Match Score Bin Summary:")
for _, row in summary.iterrows():
    print(f"{row['match_score_bin']}: {row['count']} matches")

print("\n🟢 USAT Sanctioned Event Count:")
print(df_matches['usat_sanctioned'].value_counts())

print("\n✅ Match results written to 'matched_runsignup_trifind_events_2025.xlsx'")
