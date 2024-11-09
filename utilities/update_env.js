const fs = require('fs');
// require('dotenv').config({ path: '../.env' });

async function updateEnvFile(token) {
  // Read the current .env file content
  const envFilePath = '.env';
  const envContent = fs.readFileSync(envFilePath, 'utf8');

  if (token !== process.env.MARKETO_API_TOKEN) {

    // Replace the line that contains 'MARKETO_API_TOKEN'
    const updatedEnvContent = envContent.replace(/^MARKETO_API_TOKEN=.*$/m, `MARKETO_API_TOKEN=${token}`);

    // Write the updated content back to the .env file
    fs.writeFileSync(envFilePath, updatedEnvContent, 'utf8');

    console.log('MARKETO_API_TOKEN has been updated.');
  } else {
    console.log('MARKETO_API_TOKEN is already up to date.');
  }
}

// Export the function
module.exports = updateEnvFile;
