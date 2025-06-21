import requests
import csv

# Step 1: Define URL and headers
url = "https://www.trifind.com/co"
headers = {
    "User-Agent": "Mozilla/5.0"  # Helps avoid basic anti-bot detection
}

# Step 2: Send GET request
response = requests.get(url, headers=headers)

# Step 3: Check response and write to files
if response.status_code == 200:
    raw_html = response.text

    # Write HTML to .html file for manual inspection
    with open("trifind_co_raw.html", "w", encoding="utf-8") as html_file:
        html_file.write(raw_html)
    print("✅ HTML saved to 'trifind_co_raw.html'")

    # Write HTML as a single cell into a CSV file
    with open("trifind_co_raw.csv", "w", newline='', encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["raw_html"])
        writer.writerow([raw_html])
    print("✅ HTML saved to 'trifind_co_raw.csv'")

else:
    print(f"❌ Failed to fetch page. Status code: {response.status_code}")
