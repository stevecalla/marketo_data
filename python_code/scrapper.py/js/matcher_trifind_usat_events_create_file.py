import pandas as pd
from rapidfuzz import fuzz, process
import os

# === Directories & Filenames ===
input_directory = 'input/'
output_directory = 'output/events/'
output_file_name = 'matched_trifind_usat_events_2025_v1'
os.makedirs(output_directory, exist_ok=True)

# === Load Input Files ===
trifind = pd.read_excel(os.path.join(input_directory, 'trifind_paginated_events.xlsx'), sheet_name='All Events')
usat = pd.read_csv(os.path.join(input_directory, 'results_2025-06-20_12-00-59_python_event_data_offset_0_batch_1.csv'))

# === Clean + Normalize ===
trifind = trifind[['title', 'state', 'usat_sanctioned', 'url', 'date']].dropna().rename(columns={
    'url': 'trifind_url',
    'usat_sanctioned': 'trifind_usat_sanctioned_flag'
})

usat = usat[['Name', '2LetterCode', 'RaceDate', 'ApplicationID', 'RegistrationWebsite']].dropna(subset=['Name', '2LetterCode', 'RaceDate']).rename(columns={
    '2LetterCode': 'usat_state'
})
usat = usat[usat['RaceDate'].astype(str).str.startswith('2025')]

trifind['title_norm'] = trifind['title'].str.lower().str.strip()
usat['Name_norm'] = usat['Name'].str.lower().str.strip()

trifind['parsed_date'] = pd.to_datetime(trifind['date'], errors='coerce')
trifind['month'] = trifind['parsed_date'].dt.month
trifind['year'] = trifind['parsed_date'].dt.year

# === Fuzzy Match Logic ===
all_matches = []

for _, tf in trifind.iterrows():
    usat_candidates = usat[usat['usat_state'] == tf['state']]
    if not usat_candidates.empty:
        usat_match_norm, score_usat, _ = process.extractOne(tf['title_norm'], usat_candidates['Name_norm'], scorer=fuzz.ratio)
        usat_row = usat_candidates[usat_candidates['Name_norm'] == usat_match_norm].iloc[0]
        usat_name = usat_row['Name']
        usat_state = usat_row['usat_state']
        usat_date = usat_row['RaceDate']
        usat_app_id = usat_row['ApplicationID']
        usat_reg_url = usat_row['RegistrationWebsite']
    else:
        usat_name = usat_state = usat_date = usat_app_id = usat_reg_url = None
        score_usat = 0

    trifind_sanctioned = str(tf['trifind_usat_sanctioned_flag']).strip().lower() == 'yes'
    match_score_high = score_usat > 90

    is_sanctioned = trifind_sanctioned or match_score_high
    sanction_discrepancy_flag = trifind_sanctioned != match_score_high

    # ✅ reason_for_sanction logic:
    if trifind_sanctioned and match_score_high:
        reason = "both"
        # "both" – Both sources confirm
    elif trifind_sanctioned and not match_score_high:
        reason = "flag_only"
        # "flag_only" – Trifind says “yes”, but match score ≤ 90
    elif not trifind_sanctioned and match_score_high:
        reason = "score_only"
        # "score_only" – Match score > 90, but Trifind says not “yes”
    else:
        reason = "neither"
        # "neither" – Neither does

    all_matches.append({
        'trifind_title': tf['title'],
        'trifind_url': tf['trifind_url'],
        'trifind_date': tf['parsed_date'],
        'trifind_month': tf['month'],
        'trifind_year': tf['year'],
        'trifind_state': tf['state'],
        'trifind_usat_sanctioned_flag': tf['trifind_usat_sanctioned_flag'],

        'usat_name': usat_name,
        'usat_state': usat_state,
        'usat_date': usat_date,
        'match_score_usat': score_usat,
        'matched_usat': match_score_high,
        'ApplicationID': usat_app_id,
        'RegistrationWebsite': usat_reg_url,

        'inferred_usat_sanctioned': is_sanctioned,
        'sanction_discrepancy_flag': sanction_discrepancy_flag,
        'reason_for_sanction': reason
    })

df_matches = pd.DataFrame(all_matches)

# === Score Bins ===
bins = [0, 69, 79, 89, 94, 100]
labels = ['0–69', '70–79', '80–89', '90–94', '95–100']
df_matches['score_bin_usat'] = pd.cut(df_matches['match_score_usat'], bins=bins, labels=labels, include_lowest=True)

# === Summary Table ===
summary_usat = df_matches['score_bin_usat'].value_counts().sort_index().reset_index()
summary_usat.columns = ['match_score_bin_usat', 'count']

# === Save to Excel ===
output_path = os.path.join(output_directory, output_file_name + '.xlsx')
with pd.ExcelWriter(output_path) as writer:
    df_matches.to_excel(writer, sheet_name='Matches', index=False)
    summary_usat.to_excel(writer, sheet_name='USAT Score Summary', index=False)

# === Console Output ===
print("\n📊 USAT Match Score Bin Summary:")
for _, row in summary_usat.iterrows():
    print(f"{row['match_score_bin_usat']}: {row['count']} matches")

print("\n🟢 Trifind USAT Sanctioned Flag (Raw):")
print(df_matches['trifind_usat_sanctioned_flag'].value_counts().to_string(index=True, header=False))

print("\n🟢 Inferred USAT Sanctioned (Based on Flag OR Score > 90):")
print(df_matches['inferred_usat_sanctioned'].value_counts().to_string(index=True, header=False))

print("\n⚠️  Sanction Discrepancy (Trifind vs Match Score > 90):")
print(df_matches['sanction_discrepancy_flag'].value_counts().to_string(index=True, header=False))

print("\n📌 Sanction Reason Breakdown:")
print(df_matches['reason_for_sanction'].value_counts().to_string(index=True, header=False))

print(f"\n✅ Match results written to: {output_path}")