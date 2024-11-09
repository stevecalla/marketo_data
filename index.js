require('dotenv').config();
const { performance } = require('perf_hooks');

// Throttling parameters
const MAX_CALLS_IN_20_SECS = 75;   // Max number of calls in 20 seconds
const TIME_WINDOW = 20000; // 20 seconds in ms
const CAP_CALLS_PER_DAY = 10000; // Max number of calls in a day 

// Queue to hold pending calls
let callCount = 0; // Track the number of calls in the current period
let lastResetTime = Date.now(); // Track the last time we reset the call count

const { MARKETO_TOKEN, GET_MARKETO_PAGING_TOKEN, GET_MARKETO_ACTIVITY_DATA, MARKETO_ACTIVITY_TYPES } = require('./utilities/api-paths');
const updateEnvFile = require('./utilities/update_env');
const fetchAPI = require('./utilities/fetch_api');
const exportArrayToCSV = require('./utilities/csv_export');
const { create } = require('domain');

const get_attribute_types = false; // append to file if exists otherwise create new file
const get_attributes_data = true; // append to file

async function export_to_csv(result, file_name = 'data', count, data_row_count) {
  if (result && result.length > 0) {
    exportArrayToCSV(result, file_name, count, data_row_count);
  } else {
    console.log('No results to export.');
  }
}

async function fetch_paging_token(sinceDatetime) {
  const MARKETO_PAGING_TOKEN = await GET_MARKETO_PAGING_TOKEN(sinceDatetime);
  const pagingToken = await fetchAPI(MARKETO_PAGING_TOKEN);
  return pagingToken.nextPageToken;
}

// Function to throttle another function (reset every 20 seconds)

async function throttleFunction(fn, ...args) {
  const now = Date.now();

  // Check if the 20-second window has passed
  if (now - lastResetTime > TIME_WINDOW) {
    // Reset call count every 20 seconds
    lastResetTime = now;
    callCount = 0;
    console.log('Resetting call count...');
  }

  // If we've exceeded the call limit, delay the function call
  if (callCount >= MAX_CALLS_IN_20_SECS) {
    const waitTime = TIME_WINDOW - (now - lastResetTime); // Calculate how much time is left in the 20-second window
    console.log(`Too many calls, waiting ${waitTime} ms...`);
    await new Promise(resolve => setTimeout(resolve, waitTime)); // Wait for the remaining time
  }

  // Now it's safe to call the function
  callCount++; // Increment the call count for the current window
  return fn(...args); // Call the function with the provided arguments
}

async function append_additional_fields(data, created_at) {
    // Update the activity data with additional fields
    const updated_activity_data = data.map(activity => {
      // Add activityTypeDesc based on activityTypeId
      let activityTypeDesc = '';
      switch (activity.activityTypeId) {
        case 6:
          activityTypeDesc = 'Email Sent';
          break;
        case 7:
          activityTypeDesc = 'Email Delivered';
          break;
        case 8:
          activityTypeDesc = 'Email Bounced';
          break;
        case 9:
          activityTypeDesc = 'Email Unsubscribe';
          break;
        case 10:
          activityTypeDesc = 'Email Open';
          break;
        case 11:
          activityTypeDesc = 'Email Click';
          break;
        default:
          activityTypeDesc = 'Other Activity Type';
      }
    
      // Add segment based on primaryAttributeValue
      let segment = '';
      switch (activity.primaryAttributeValue) {
        case '11-6 Segment 1.11-6 Segment 1':
          segment = 'Segment 1: 3-Year 2024 Expiration';
          break;
        case '11-6 Segment 2.11-6 Segment 2':
          segment = 'Segment 2: 3-Year 2023 Expiration';
          break;
        case '11-6 Segment 3.11-6 Segment 3':
          segment = 'Segment 3: 1-Year 2024 Expiration 40-59';
          break;
        case '11-6 Segment 4.11-6 Segment 4':
          segment = 'Segment 4: 1-Year 2023 Expiration 40-59';
          break;
        default:
          segment = 'Other Segment';
      }
    
      // Return the updated activity object with both activityTypeDesc and segment
      return {
        ...activity,
        activityTypeDesc, // Add the activity type description
        segment,         // Add the segment description
        created_at
      };
    });

    return updated_activity_data;
}

// Function to fetch activity data
async function fetch_activity_data(paging_token, count = 0, data_row_count = 0, created_at) {
  // Start the timer
  const start = performance.now();

  try {
    // Throttle the call to the API request function
    const MARKETO_ACTIVITY_DATA = await GET_MARKETO_ACTIVITY_DATA(paging_token); // sets API URL
    const data = await throttleFunction(fetchAPI, MARKETO_ACTIVITY_DATA); // fetches data

    count++;
    data_row_count += data?.result?.length;

    // Update the activity data with additional fields
    const updated_activity_data = await append_additional_fields(data.result, created_at);
    
    // Append to CSV
    await export_to_csv(updated_activity_data, 'activity_data', count, data_row_count);

    // If there are more results, call recursively (throttled)
    if (data.moreResult && count < CAP_CALLS_PER_DAY) {
      await fetch_activity_data(data.nextPageToken, count, data_row_count); // Recursively fetch more data
    }
  } catch (err) {
    console.error('Error fetching activity data:', err);
  }

  // End the timer
  const end = performance.now();
  // const durationInSeconds = (end - start) / 1000; // Convert milliseconds to seconds
  // console.log(`Duration: ${durationInSeconds} seconds`);
}

// Main function to fetch data and export to CSV

async function main() {
  // Fetch api token
  const token = await fetchAPI(MARKETO_TOKEN);

  // Write api token to .env file
  await updateEnvFile(token.access_token);

  // Fetch activity types
  if (get_attribute_types) {
    const attribute_types = await fetchAPI(MARKETO_ACTIVITY_TYPES);
    await export_to_csv(attribute_types.result, 'attribute_types');
  }

  // Fetch activities

  if (get_attributes_data) {
    // Start the timer
    // const start = performance.now();

    const sinceDatetime = '2024-11-06';
    const created_at = new Date().toISOString(); // ISO 8601 format
    let paging_token = await fetch_paging_token(sinceDatetime);

    let count = 0;
    let data_row_count = 0;

    await fetch_activity_data(paging_token, count, data_row_count, created_at);
  }
}

// Run the main function
main();




