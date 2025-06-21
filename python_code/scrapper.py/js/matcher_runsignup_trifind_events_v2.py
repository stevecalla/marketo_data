import pandas as pd
from rapidfuzz import fuzz, process
import os

# === Directories & Filenames ===
input_directory = 'input/'
output_directory = 'output/events/'
output_file_name = 'matched_runsignup_trifind_usat_events_2025'
os.makedirs(output_directory, exist_ok=True)

# === Load Input Files ===
runsignup = pd.read_excel(os.path.join(input_directory, 'runsignup_triathlon_duathlon_aquathlon_aqua_bike_swim_run_2025.xlsx'), sheet_name='All Events')
trifind = pd.read_excel(os.path.join(input_directory, 'trifind_paginated_events.xlsx'), sheet_name='All Events')
usat = pd.read_csv(os.path.join(input_directory, 'results_2025-06-20_12-00-59_python_event_data_offset_0_batch_1.csv'))

# === Clean + Normalize ===
runsignup = runsignup[['title', 'state', 'url', 'date']].dropna()
trifind = trifind[['title', 'state', 'usat_sanctioned', 'url', 'date']].dropna().rename(columns={'url': 'trifind_url'})
usat = usat[['Name', '2LetterCode', 'RaceDate']].dropna().rename(columns={'2LetterCode': 'usat_state'})
usat = usat[usat['RaceDate'].astype(str).str.startswith('2025')]

runsignup['title_norm'] = runsignup['title'].str.lower().str.strip()
trifind['title_norm'] = trifind['title'].str.lower().str.strip()
usat['Name_norm'] = usat['Name'].str.lower().str.strip()

# === Parse Dates into Month & Year ===
runsignup['parsed_date'] = pd.to_datetime(runsignup['date'], errors='coerce')
runsignup['month'] = runsignup['parsed_date'].dt.month
runsignup['year'] = runsignup['parsed_date'].dt.year

trifind['parsed_date'] = pd.to_datetime(trifind['date'], errors='coerce')
trifind['month'] = trifind['parsed_date'].dt.month
trifind['year'] = trifind['parsed_date'].dt.year

# === Fuzzy Match Logic ===
all_matches = []

for _, rs in runsignup.iterrows():
    # Trifind match
    trifind_candidates = trifind[trifind['state'] == rs['state']]
    if not trifind_candidates.empty:
        tf_match_norm, score_trifind, _ = process.extractOne(rs['title_norm'], trifind_candidates['title_norm'], scorer=fuzz.ratio)
        tf_row = trifind_candidates[trifind_candidates['title_norm'] == tf_match_norm].iloc[0]
        trifind_title = tf_row['title']
        trifind_url = tf_row['trifind_url']
        trifind_date = tf_row['parsed_date']
        trifind_month = tf_row['month']
        trifind_year = tf_row['year']
        usat_sanctioned = tf_row['usat_sanctioned']
    else:
        trifind_title = trifind_url = trifind_date = trifind_month = trifind_year = None
        score_trifind = 0
        usat_sanctioned = 'Unknown'

    # USAT match
    usat_candidates = usat[usat['usat_state'] == rs['state']]
    if not usat_candidates.empty:
        usat_match_norm, score_usat, _ = process.extractOne(rs['title_norm'], usat_candidates['Name_norm'], scorer=fuzz.ratio)
        usat_row = usat_candidates[usat_candidates['Name_norm'] == usat_match_norm].iloc[0]
        usat_name = usat_row['Name']
        usat_state = usat_row['usat_state']
    else:
        usat_name = usat_state = None
        score_usat = 0

    all_matches.append({
        'runsignup_title': rs['title'],
        'runsignup_url': rs['url'],
        'runsignup_date': rs['parsed_date'],
        'runsignup_month': rs['month'],
        'runsignup_year': rs['year'],
        'state': rs['state'],

        'trifind_title': trifind_title,
        'trifind_url': trifind_url,
        'trifind_date': trifind_date,
        'trifind_month': trifind_month,
        'trifind_year': trifind_year,
        'match_score_trifind': score_trifind,
        'usat_sanctioned': usat_sanctioned,

        'usat_name': usat_name,
        'usat_state': usat_state,
        'match_score_usat': score_usat,
        'matched_usat': score_usat >= 90
    })

df_matches = pd.DataFrame(all_matches)

# === Score Bins ===
bins = [0, 69, 79, 89, 94, 100]
labels = ['0–69', '70–79', '80–89', '90–94', '95–100']
df_matches['score_bin_trifind'] = pd.cut(df_matches['match_score_trifind'], bins=bins, labels=labels, include_lowest=True)
df_matches['score_bin_usat'] = pd.cut(df_matches['match_score_usat'], bins=bins, labels=labels, include_lowest=True)

# === Summaries ===
summary_trifind = df_matches['score_bin_trifind'].value_counts().sort_index().reset_index()
summary_trifind.columns = ['match_score_bin_trifind', 'count']

summary_usat = df_matches['score_bin_usat'].value_counts().sort_index().reset_index()
summary_usat.columns = ['match_score_bin_usat', 'count']

# === Save to Excel ===
output_path = os.path.join(output_directory, output_file_name + '.xlsx')
with pd.ExcelWriter(output_path) as writer:
    df_matches.to_excel(writer, sheet_name='Matches', index=False)
    summary_trifind.to_excel(writer, sheet_name='Trifind Score Summary', index=False)
    summary_usat.to_excel(writer, sheet_name='USAT Score Summary', index=False)

# === Console Summary ===
print("\n📊 Trifind Match Score Bin Summary:")
for _, row in summary_trifind.iterrows():
    print(f"{row['match_score_bin_trifind']}: {row['count']} matches")

print("\n📊 USAT Match Score Bin Summary:")
for _, row in summary_usat.iterrows():
    print(f"{row['match_score_bin_usat']}: {row['count']} matches")

print("\n🟢 USAT Sanctioned Event Count (Trifind):")
print(df_matches['usat_sanctioned'].value_counts())

print(f"\n✅ Match results written to: {output_path}")
