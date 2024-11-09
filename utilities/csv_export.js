const fs = require('fs').promises;
const path = require('path');

// Helper function to check if the file exists and is not empty
async function fileExistsCheck(filepath) {
  try {
    const stats = await fs.stat(filepath);
    return stats.size > 0;  // Check if the file is not empty
  } catch (err) {
    return false;  // If the file does not exist, return false
  }
}

// Function to convert array data to CSV format
async function downloadCSV(data, filename, count, data_row_count) {
  // Define the folder path and filename
  const folderPath = path.join(__dirname, "..", 'data');

  // Ensure the data folder exists, create it if it doesn't
  try {
    await fs.access(folderPath);
  } catch (err) {
    // If the folder does not exist, create it
    await fs.mkdir(folderPath, { recursive: true });
    console.log('Folder created:', folderPath);
  }

  filename = path.join(folderPath, filename);  // Specify your filename

  // Prepare the CSV content
  const header = Object.keys(data[0]).join(',');  // Header from object keys
  const rows = data.map(row =>
    Object.values(row)  // Values of each row object
      .map(value => `"${value}"`)  // Wrap values in double quotes to escape commas
      .join(',')
  );

  const csvContent = rows.join("\n");

  try {
    // Check if the file already exists and has content
    const fileExists = await fileExistsCheck(filename);

    if (!fileExists) {
      // If the file doesn't exist or is empty, add the header
      await fs.writeFile(filename, header + "\n" + csvContent, 'utf8');
      console.log(`CSV file has been created and header added: ${filename}`);
    } else {
      // If the file exists and has data, just append the rows
      await fs.appendFile(filename, "\n" + csvContent, 'utf8');
      console.log(`CSV content has been appended to ${filename}... ${count}... ${data.length}... ${data_row_count}`);
    }
  } catch (err) {
    console.error('Error handling the file:', err);
  }
}

// Export function for campaigns and activities
async function exportArrayToCSV(results, filenamePrefix = 'data', count, data_row_count) {

  if (results[0].attributes) {
    results = await results.map(row => flattenActivityData(row));
  }

  // Flatten the data if it's for activities
  if (results[0].primaryAttribute) {
    // Delete the 'attributes' property for each row
    results = await results.map(row => {
      delete row.primaryAttribute;
      return row;
    });
  }

  // Prepare the filename with the current timestamp
  const filename = `${filenamePrefix}_${await formatDateToCustomFormat()}.csv`;

  // Download and save CSV to file
  await downloadCSV(results, filename, count, data_row_count);
}

// Function to flatten the nested attributes in activity data
function flattenActivityData(row) {
  const flattenedRow = { ...row };  // Copy the main row data

  // Flatten the 'attributes' array into individual columns
  row?.attributes?.forEach(attribute => {
    flattenedRow[attribute.name] = attribute.value || attribute.dataType;
  });

  // Remove the 'attributes' array from the row
  delete flattenedRow.attributes;

  return flattenedRow;
}

// Function to format date to a custom format
async function formatDateToCustomFormat() {
  const date = new Date();

  // Get individual date components
  const month = date.getMonth() + 1; // Month is zero-based, so add 1
  const day = date.getDate();
  const year = date.getFullYear();
  const hours = date.getHours();
  const minutes = date.getMinutes();
  const seconds = date.getSeconds();
  const timezone = date.toLocaleTimeString('en-US', { timeZoneName: 'short' }).split(' ')[2];

  // Pad single-digit values with leading zeros
  const formattedMonth = month.toString().padStart(2, '0');
  const formattedDay = day.toString().padStart(2, '0');
  // const formattedHours = hours.toString().padStart(2, '0');
  // const formattedMinutes = minutes.toString().padStart(2, '0');
  // const formattedSeconds = seconds.toString().padStart(2, '0');

  // Construct the formatted date string
  // const formattedDate = `${formattedMonth}-${formattedDay}-${year}_${formattedHours}:${formattedMinutes}:${formattedSeconds}_${timezone}`;
  const formattedDate = `${formattedMonth}-${formattedDay}-${year}`;

  return formattedDate;
}

module.exports = exportArrayToCSV;

// // Example data
// const example_campaign_data = [{
//   id: 1054,
//   name: '01-Sync New People to CRM',
//   description: 'Sets initial Status and pushes Lead to the CRM',
//   type: 'trigger',
//   programName: 'OP-Lifecycle',
//   programId: 1011,
//   workspaceName: 'Default',
//   createdAt: '2014-06-27T02:45:14Z',
//   updatedAt: '2016-03-29T20:43:10Z',
//   active: false
// }];

// exportArrayToCSV(example_campaign_data, 'campaign');

// const example_activity_data = [{
//   id: 2024852576,
//   marketoGUID: '2024852576',
//   leadId: 5900785,
//   activityDate: '2024-11-08T00:00:07Z',
//   activityTypeId: 10,
//   campaignId: 10684,
//   primaryAttributeValueId: 23960,
//   primaryAttributeValue: '2024-11-06 Nix Bronze Members.2024-11-06 Nix Bronze Members',
//   attributes: [
//     { name: 'Bot Activity Pattern', value: 'N/A' },
//     { name: 'Browser', value: 'Google Mail' },
//     { name: 'Campaign Run ID', value: '20326' },
//     { name: 'Choice Number', value: '21070' },
//     { name: 'Device', value: 'Unknown' },
//     { name: 'Is Bot Activity', value: false },
//     { name: 'Is Mobile Device', value: false },
//     { name: 'Platform', value: 'Unknown' },
//     { name: 'Step ID', value: '13408' },
//     {
//       name: 'User Agent',
//       value: 'Mozilla/5.0 (Windows NT 5.1; rv:11.0) Gecko Firefox/11.0 (via ggpht.com GoogleImageProxy)'
//     },
//     {
//       name: 'Campaign',
//       value: 'Email Batch Program-8503-send-email-campaign'
//     }
//   ]
// }];

// To export activity data
// exportArrayToCSV(example_activity_data, 'activity');


// async function downloadCSV(data, filename, count, data_row_count) {
//   // Define the folder path and filename
//   const folderPath = path.join(__dirname, "..", 'data');

//   // Ensure the data folder exists, create it if it doesn't
//   try {
//     await fs.access(folderPath);
//   } catch (err) {
//     // If the folder does not exist, create it
//     await fs.mkdir(folderPath, { recursive: true });
//     console.log('Folder created:', folderPath);
//   }

//   filename = path.join(folderPath, filename);  // Specify your filename

//   // Prepare the CSV content
//   const header = Object.keys(data[0]).join(',');  // Header from object keys
//   const rows = data.map(row =>
//     Object.values(row)  // Values of each row object
//       .map(value => `"${value}"`)  // Wrap values in double quotes to escape commas
//       .join(',')
//   );

//   const csvContent = [header, ...rows].join("\n");

//   // Write the CSV to a file
//   // fs.writeFile(filename, csvContent, 'utf8', (err) => {
//   //   if (err) {
//   //     console.error('Error writing to file:', err);
//   //   } else {
//   //     console.log(`CSV file has been saved as ${filename}`);
//   //   }
//   // });

//   // console.log('appending to file...');
//   try {
//     await fs.appendFile(filename, csvContent, 'utf8');
//     console.log(`CSV content has been appended to ${filename}... ${count}... ${data.length}... ${data_row_count}`);
//   } catch (err) {
//     console.error('Error appending to file:', err);
//   }
// }



