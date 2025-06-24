// npm install axios cheerio xlsx

const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const XLSX = require('xlsx');

const BASE_URL = "https://www.trifind.com/";
const output_directory = 'output/events/';
const output_file_name = 'trifind_paginated_events';

// # US state abbreviations
const states = [
    'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga', 'hi',
    'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md', 'ma', 'mi',
    'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj', 'nm', 'ny', 'nc',
    'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut',
    'vt', 'va', 'wa', 'wv', 'wi', 'wy'
];
// const states = ['co']; // Replace with full list if needed
const allEvents = [];

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function scrapeState(state) {
  let page = 1;
  while (true) {
    const url = `${BASE_URL}${state}?page=${page}`;
    console.log(`Scraping: ${url}`);
    try {
      const { data: html } = await axios.get(url, {
        headers: { 'User-Agent': 'Mozilla/5.0' },
        timeout: 10000
      });

      const $ = cheerio.load(html);
      const panels = $('.panel.panel-info.clearfix');

      if (panels.length === 0) {
        console.log(`✅ No more panels on page ${page}.`);
        break;
      }

      panels.each((_, panel) => {
        const el = $(panel);
        const event = {
          state: state.toUpperCase(),
          title: null,
          url: null,
          date: null,
          location: null,
          race_types: [],
          usat_sanctioned: "No"
        };

        const a = el.find('a[title][href]').first();
        if (a.length) {
          event.title = a.text().trim();
          event.url = a.attr('href');
        }

        const dateDiv = el.find('.panel-heading .text-md-right').first();
        if (dateDiv.length) {
          event.date = dateDiv.text().trim();
        }

        const loc = el.find('span.location-text').first();
        if (loc.length) {
          event.location = loc.text().trim();
        }

        const rows = el.find('table tr');
        for (let i = 0; i < rows.length; i += 2) {
          const race = $(rows[i]).text().trim();
          const desc = $(rows[i + 1]).text().trim();
          if (race && desc) {
            event.race_types.push(`${race} - ${desc}`);
          }
        }

        const usatLogo = el.find('img[src="/images/usat-logo.png"]');
        event.usat_sanctioned = usatLogo.length > 0 ? "Yes" : "No";

        allEvents.push(event);
      });

      page++;
      await delay(1000); // polite delay
    } catch (error) {
      console.log(`❌ Failed on page ${page} for ${state}`);
      break;
    }
  }
}

(async () => {
  for (const state of states) {
    await scrapeState(state);
  }

  // Write CSV
  const csv = [
    Object.keys(allEvents[0]).join(','),
    ...allEvents.map(ev =>
      `${ev.state},"${ev.title}","${ev.url}","${ev.date}","${ev.location}","${ev.race_types.join('; ')}",${ev.usat_sanctioned}`
    )
  ].join('\n');

  // fs.writeFileSync('trifind_paginated_events.csv', csv);
  fs.writeFileSync(`${output_directory}${output_file_name}.csv`, csv);

  // Build pivot table by state & usat_sanctioned
  const pivotMap = {};
  allEvents.forEach(ev => {
    const key = ev.state;
    if (!pivotMap[key]) pivotMap[key] = { Yes: 0, No: 0 };
    pivotMap[key][ev.usat_sanctioned]++;
  });

  const pivotArray = Object.entries(pivotMap).map(([state, counts]) => ({
    state,
    Yes: counts.Yes,
    No: counts.No,
    Total_Events: counts.Yes + counts.No
  }));

  // Add grand total row
  const totalYes = pivotArray.reduce((sum, row) => sum + row.Yes, 0);
  const totalNo = pivotArray.reduce((sum, row) => sum + row.No, 0);
  pivotArray.push({
    state: 'ALL_STATES',
    Yes: totalYes,
    No: totalNo,
    Total_Events: totalYes + totalNo
  });

  // Write to Excel
  const workbook = XLSX.utils.book_new();
  const ws_all = XLSX.utils.json_to_sheet(allEvents);
  const ws_pivot = XLSX.utils.json_to_sheet(pivotArray);
  XLSX.utils.book_append_sheet(workbook, ws_all, 'All Events');
  XLSX.utils.book_append_sheet(workbook, ws_pivot, 'Pivot by USAT');
  XLSX.writeFile(workbook, `${output_directory}${output_file_name}.xlsx`);

  // Console summary
  const topStates = pivotArray
    .filter(row => row.state !== 'ALL_STATES')
    .sort((a, b) => b.Total_Events - a.Total_Events)
    .slice(0, 5);

  console.log("\n📊 Summary:");
  console.log(`🔢 Total Events Scraped: ${allEvents.length}\n`);
  console.log("🏆 Top 5 States by Total Events:");
  for (const row of topStates) {
    console.log(`${row.state}: ${row.Total_Events} total — 🟢 USAT: ${row.Yes}, 🔴 Non-USAT: ${row.No}`);
  }
  console.log(`\n📈 Overall Breakdown:\n🟢 USAT Sanctioned: ${totalYes}\n🔴 Non-USAT: ${totalNo}`);
})();
