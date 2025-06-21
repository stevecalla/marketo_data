const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Step 1: Define URL and headers
// const url = "https://www.trifind.com/co";
// const file_name = 'trifind_co_raw';

const event_type = ["triathlon", "duathlon", "aquathlon", "aqua_bike", "swim_run"];

const url = "https://runsignup.com/Races?name&eventType=triathlon&radius=5&zipcodeRadius&country=US&state&distance&max_distance&units=K&start_date=2025-01-01&end_date&num=250#tab-tabRaceSearchAdvanced";

const file_name = 'runsignup_raw';

const headers = {
  "User-Agent": "Mozilla/5.0"
};

// Step 2: Send GET request
axios.get(url, { headers })
  .then(response => {
    const rawHtml = response.data;

    // Step 3: Write HTML to file
    fs.writeFileSync(`${file_name}.html`, rawHtml, "utf8");
    console.log(`✅ HTML saved to ${file_name}.html`);

    // Step 4: Write HTML as one cell in CSV
    const csvContent = `"raw_html"\n"${rawHtml.replace(/"/g, '""')}"`; // escape quotes for CSV

    // fs.writeFileSync("trifind_co_raw.csv", csvContent, "utf8");
    // console.log("✅ HTML saved to 'trifind_co_raw.csv'");

    fs.writeFileSync(`${file_name}.csv`, rawHtml, "utf8");
    console.log(`✅ HTML saved to ${file_name}.csv`);
  })
  .catch(error => {
    console.error(`❌ Failed to fetch page. ${error.message}`);
  });
