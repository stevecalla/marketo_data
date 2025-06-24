import pandas as pd
from rapidfuzz import fuzz, process
import os

# === State Name to Abbreviation Mapping ===
us_state_to_abbrev = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC"
}

# === Directories & Filenames ===
input_directory = 'input/'
output_directory = 'output/events/'
output_file_name = 'matched_trifind_usat_events_2025_v1_created'
os.makedirs(output_directory, exist_ok=True)

# === Load Input Files ===
trifind = pd.read_excel(os.path.join(input_directory, 'trifind_advanced_search_2025_results.xlsx'), sheet_name='All Events')
usat = pd.read_csv(os.path.join(input_directory, 'results_2025-06-20_12-00-59_python_event_data_offset_0_batch_1.csv'))

# === Clean + Normalize ===
trifind = trifind[['title', 'city', 'state', 'location', 'race_type', 'usat_sanctioned', 'url', 'date']].dropna().rename(columns={
    'url': 'trifind_url',
    'usat_sanctioned': 'trifind_usat_sanctioned_flag'
})

# Convert full state names to abbreviations for matching
# trifind['state_abbrev'] = trifind['state'].map(us_state_to_abbrev)
trifind['state_abbrev'] = trifind['state'].apply(
    lambda s: us_state_to_abbrev.get(s, 'Other')
)

# Identify and log unmatched Trifind states

# Identify and print all Trifind states that were categorized as 'Other'
other_states = trifind[trifind['state_abbrev'] == 'Other']['state'].unique()
if len(other_states) > 0:
    print("⚠️ The following Trifind states were not recognized and categorized as 'Other':")
    for s in other_states:
        print(f" - {s}")

# Drop any rows where mapping failed
trifind = trifind.dropna(subset=['state_abbrev'])

usat = usat[['Name', '2LetterCode', 'RaceDate', 'ApplicationID', 'Status', 'RegistrationWebsite']].dropna(subset=['Name', '2LetterCode', 'RaceDate']).rename(columns={
    '2LetterCode': 'usat_state'
})
# Parse USAT RaceDate into month/year
usat['parsed_date'] = pd.to_datetime(usat['RaceDate'], errors='coerce')
usat['usat_month'] = usat['parsed_date'].dt.month
usat['usat_year'] = usat['parsed_date'].dt.year

# Filter USAT data for 2025 events only
usat = usat[usat['RaceDate'].astype(str).str.startswith('2025')]

trifind['title_norm'] = trifind['title'].str.lower().str.strip()
usat['Name_norm'] = usat['Name'].str.lower().str.strip()

trifind['parsed_date'] = pd.to_datetime(trifind['date'], errors='coerce')
trifind['month'] = trifind['parsed_date'].dt.month
trifind['year'] = trifind['parsed_date'].dt.year

# === Fuzzy Match Logic ===
all_matches = []

for _, tf in trifind.iterrows():
    if tf['state_abbrev'] == 'Other':
        continue  # skip unmatched states
    
    usat_candidates = usat[usat['usat_state'] == tf['state_abbrev']]
    if not usat_candidates.empty:
        usat_match_norm, score_usat, _ = process.extractOne(tf['title_norm'], usat_candidates['Name_norm'], scorer=fuzz.ratio)
        usat_row = usat_candidates[usat_candidates['Name_norm'] == usat_match_norm].iloc[0]
        usat_name = usat_row['Name']
        usat_status = usat_row['Status']
        usat_state = usat_row['usat_state']
        usat_month = usat_row['usat_month']
        usat_year = usat_row['usat_year']
        usat_date = usat_row['RaceDate']
        usat_app_id = usat_row['ApplicationID']
        usat_reg_url = usat_row['RegistrationWebsite']
    else:
        usat_name = usat_state = usat_date = usat_app_id = usat_reg_url = usat_status = None
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
        'trifind_city': tf['city'],
        'trifind_state': tf['state'],
        'trifind_location': tf['location'],
        'trifind_race_type': tf['race_type'],
        'trifind_date': tf['parsed_date'],
        'trifind_month': tf['month'],
        'trifind_year': tf['year'],
        'trifind_url': tf['trifind_url'],
        'trifind_usat_sanctioned_flag': tf['trifind_usat_sanctioned_flag'],

        'usat_name': usat_name,
        'usat_status': usat_status,
        'usat_state': usat_state,
        'usat_date': usat_date,
        'usat_month': usat_row['usat_month'] if not usat_candidates.empty else None,
        'usat_year': usat_row['usat_year'] if not usat_candidates.empty else None,
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

# === Inferred USAT Summary by State ===
summary_by_state = (
    df_matches.groupby(['trifind_state', 'inferred_usat_sanctioned'])
    .size()
    .unstack(fill_value=0)
    .rename(columns={True: 'USAT', False: 'Non-USAT'})
)

summary_by_state['Total'] = summary_by_state.sum(axis=1)
top_states = summary_by_state.sort_values(by='Total', ascending=False).head(5)

total_events = len(df_matches)
total_usat = summary_by_state['USAT'].sum()
total_non_usat = summary_by_state['Non-USAT'].sum()

print("\n📊 Summary:")
print(f"🔢 Total Events Scraped: {total_events}")
print(f"🏆 Top 5 States by Total Events:")

for state, row in top_states.iterrows():
    print(f"{state}: {row['Total']} total — 🟢 USAT: {row['USAT']}, 🔴 Non-USAT: {row['Non-USAT']}")

print("📈 Overall Breakdown:")
print(f"🟢 USAT Sanctioned: {total_usat}")
print(f"🔴 Non-USAT: {total_non_usat}")


print(f"\n✅ Match results written to: {output_path}")
