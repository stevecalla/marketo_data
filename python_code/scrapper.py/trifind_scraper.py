import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://www.trifind.com/"
# US state abbreviations
states = [
    'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga', 'hi',
    'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md', 'ma', 'mi',
    'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj', 'nm', 'ny', 'nc',
    'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut',
    'vt', 'va', 'wa', 'wv', 'wi', 'wy'
]

# states = ['co', 'tx', 'ca']  # You can extend this to all states
all_events = []

def scrape_state_paginated(state):
    page = 1
    while True:
        url = f"{BASE_URL}{state}?page={page}"
        print(f"Scraping: {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

        if response.status_code != 200:
            print(f"❌ Failed on page {page} for {state}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        panels = soup.find_all("div", class_="panel panel-info clearfix")

        if not panels:
            print(f"✅ No more panels on page {page}. Ending pagination.")
            break

        for panel in panels:
            event = {
                "state": state.upper(),
                "title": None,
                "url": None,
                "date": None,
                "location": None,
                "race_types": [],
                "usat_sanctioned": "No",
            }

            # Event title and link
            a_tag = panel.find("a", href=True, title=True)
            if a_tag:
                event["title"] = a_tag.get_text(strip=True)
                event["url"] = a_tag["href"]

            # Event date
            date_div = panel.select_one(".panel-heading .text-md-right")
            if date_div:
                event["date"] = date_div.get_text(strip=True)

            # location
            loc_span = panel.find("span", class_="location-text")
            if loc_span:
                event["location"] = loc_span.get_text(strip=True)

            # Race types
            table = panel.find("table")
            if table:
                rows = table.find_all("tr")
                for i in range(0, len(rows), 2):
                    try:
                        race_type = rows[i].get_text(strip=True)
                        description = rows[i+1].get_text(strip=True)
                        event["race_types"].append(f"{race_type} - {description}")
                    except IndexError:
                        continue

            # USAT Sanctioning check
            usat_logo = panel.find("img", {"src": "/images/usat-logo.png"})
            event["usat_sanctioned"] = "Yes" if usat_logo else "No"

            all_events.append(event)

        page += 1
        time.sleep(1)  # Be polite

# Scrape the desired states
for state in states:
    scrape_state_paginated(state)

# Output to CSV
df = pd.DataFrame(all_events)
df["race_types"] = df["race_types"].apply(lambda x: "; ".join(x))
df.to_csv("trifind_paginated_events.csv", index=False)

# Create pivot table with USAT Sanctioning breakdown
pivot = df.pivot_table(index="state", columns="usat_sanctioned", aggfunc="size", fill_value=0)

# Add total column
pivot["Total_Events"] = pivot.sum(axis=1)

# Add a grand total row
total_row = pd.DataFrame(pivot.sum(axis=0)).T
total_row.index = ["ALL_STATES"]
pivot = pd.concat([pivot, total_row])

# Reset index for Excel export
pivot.reset_index(inplace=True)

# Output DataFrame and Pivot Table to Excel
with pd.ExcelWriter("trifind_paginated_events.xlsx", engine="xlsxwriter") as writer:
    df.to_excel(writer, sheet_name="All Events", index=False)
    pivot.to_excel(writer, sheet_name="Pivot by USAT", index=False)

# Console summary
total_events = len(df)
event_counts = df['state'].value_counts().head(5)

total_sanctioned = df[df['usat_sanctioned'] == 'Yes'].shape[0]
total_not_sanctioned = df[df['usat_sanctioned'] == 'No'].shape[0]

print("\n📊 Summary:")
print(f"🔢 Total Events Scraped: {total_events}\n")

print("🏆 Top 5 States by Total Events:")
for state, count in event_counts.items():
    sanctioned = df[(df['state'] == state) & (df['usat_sanctioned'] == 'Yes')].shape[0]
    not_sanctioned = df[(df['state'] == state) & (df['usat_sanctioned'] == 'No')].shape[0]
    print(f"{state}: {count} total — 🟢 USAT: {sanctioned}, 🔴 Non-USAT: {not_sanctioned}")

print(f"\n📈 Overall Breakdown:\n🟢 USAT Sanctioned: {total_sanctioned}\n🔴 Non-USAT: {total_not_sanctioned}")

print(f"\n✅ Scraped {len(df)} events across {len(states)} state(s).")
print("📁 Saved to 'trifind_paginated_events.xlsx'")

