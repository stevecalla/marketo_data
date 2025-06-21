const axios = require('axios');
const cheerio = require('cheerio');
const ExcelJS = require('exceljs');

const BASE_URL = 'https://runsignup.com';
const EVENT_TYPES = ['triathlon', 'duathlon', 'aquathlon', 'aqua_bike', 'swim_run'];

const output_directory = 'output/events/';
const output_file_name = `runsignup_${EVENT_TYPES.join('_')}_2025`;

const allEvents = [];
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

(async () => {
  try {
    for (const eventType of EVENT_TYPES) {
      let page = 1;
      let hasMorePages = true;
      console.log(`\n🔍 Scraping event type: ${eventType}`);

      while (hasMorePages) {
        const searchUrl = `${BASE_URL}/Races?name&eventType=${eventType}&radius=5&zipcodeRadius&country=US&state&distance&max_distance&units=K&start_date=2025-01-01&end_date&num=250&page=${page}`;
        console.log(`Fetching: ${searchUrl}`);

        const { data: html } = await axios.get(searchUrl, {
          headers: { 'User-Agent': 'Mozilla/5.0' }
        });

        const $ = cheerio.load(html);
        let eventsFound = 0;

        $('tr').each((_, row) => {
          const event = {
            title: null,
            date: null,
            location: null,
            state: null,
            url: null,
            month: null,
            year: null,
            event_type: eventType
          };

          const titleAnchor = $(row).find('a.fs-lg-2.d-inline-block.margin-b-5');
          if (titleAnchor.length) {
            event.title = titleAnchor.text().trim();
            const href = titleAnchor.attr('href');
            event.url = href ? `${BASE_URL}${href}` : null;
          }

          const dateCell = $(row).find('td.fs-sm-2').first();
          if (dateCell.length) {
            event.date = dateCell.text().trim();
            const parsedDate = new Date(event.date);
            if (!isNaN(parsedDate)) {
              event.month = parsedDate.getMonth() + 1;
              event.year = parsedDate.getFullYear();
            }
          }

          const locSpan = $(row).find('span > span').first();
          if (locSpan.length) {
            event.location = locSpan.text().trim();
            const stateMatch = event.location.match(/,\s*([A-Z]{2})\s/);
            event.state = stateMatch ? stateMatch[1] : null;
          }

          if (event.title && event.date && event.location) {
            allEvents.push(event);
            eventsFound++;
          }
        });

        if (eventsFound === 0) {
          hasMorePages = false;
        } else {
          page++;
          await delay(1000);
        }
      }
    }

    // Create Excel workbook and worksheets
    const workbook = new ExcelJS.Workbook();

    // Sheet 1: All Events
    const sheet = workbook.addWorksheet('All Events');
    sheet.columns = [
      { header: 'title', key: 'title' },
      { header: 'date', key: 'date' },
      { header: 'location', key: 'location' },
      { header: 'state', key: 'state' },
      { header: 'url', key: 'url' },
      { header: 'month', key: 'month' },
      { header: 'year', key: 'year' },
      { header: 'event_type', key: 'event_type' }
    ];
    allEvents.forEach(ev => sheet.addRow(ev));

    // Sheet 2: Summary by State-Year
    const stateYearMap = {};
    allEvents.forEach(ev => {
      if (ev.state && ev.year) {
        const key = `${ev.state}_${ev.year}`;
        stateYearMap[key] = (stateYearMap[key] || 0) + 1;
      }
    });

    const stateYearSheet = workbook.addWorksheet('Summary State-Year');
    stateYearSheet.addRow(['State', 'Year', 'Event Count']);

    const sortedStateYear = Object.entries(stateYearMap)
      .map(([key, count]) => {
        const [state, year] = key.split('_');
        return { state, year: parseInt(year), count };
      })
      .sort((a, b) => a.state.localeCompare(b.state));

    sortedStateYear.forEach(row => {
      stateYearSheet.addRow([row.state, row.year, row.count]);
    });


    // Sheet 3: Summary by Event Type and State
    const typeStateMap = {};
    allEvents.forEach(ev => {
      if (ev.event_type && ev.state) {
        // const key = `${ev.event_type}_${ev.state}`;
        const key = `${ev.event_type}__${ev.state}`;
        typeStateMap[key] = (typeStateMap[key] || 0) + 1;
      }
    });

    const typeStateSheet = workbook.addWorksheet('Summary Type-State');
    typeStateSheet.addRow(['Event Type', 'State', 'Event Count']);

    const sortedTypeState = Object.entries(typeStateMap)
      .map(([key, count]) => {
        // const [event_type, state] = key.split('_');
        const [event_type, state] = key.split('__');
        return { event_type, state, count };
      })
      .sort((a, b) => a.state.localeCompare(b.state) || a.event_type.localeCompare(b.event_type));

    sortedTypeState.forEach(row => {
      typeStateSheet.addRow([row.event_type, row.state, row.count]);
    });

    // Sheet 4: Summary by Event Type
    const typeCountMap = {};
    allEvents.forEach(ev => {
      if (ev.event_type) {
        typeCountMap[ev.event_type] = (typeCountMap[ev.event_type] || 0) + 1;
      }
    });

    const typeSummarySheet = workbook.addWorksheet('Summary Event Type');
    typeSummarySheet.addRow(['Event Type', 'Event Count']);
    Object.entries(typeCountMap).forEach(([event_type, count]) => {
      typeSummarySheet.addRow([event_type, count]);
    });

    // await workbook.xlsx.writeFile(OUTPUT_FILENAME);
    await workbook.xlsx.writeFile(`${output_directory}${output_file_name}.xlsx`);

    console.log(`\n✅ Scraped ${allEvents.length} total events.`);
    console.log(`📁 Saved to '${OUTPUT_FILENAME}'`);

  } catch (error) {
    console.error('❌ Error scraping page:', error.message);
  }
})();
