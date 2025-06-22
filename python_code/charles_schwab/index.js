// npm install axios open base-64
// curl "http://127.0.0.1/?code=C0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.nIpPrlNVbnKoZz8hNvWM8h_mklRnZUkGkxaKx7czn1s%40&session=5d852e43-f8fa-472b-85eb-48581d3c20c2"

// open "http://127.0.0.1/?code=C0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.nIpPrlNVbnKoZz8hNvWM8h_mklRnZUkGkxaKx7czn1s%40&session=5d852e43-f8fa-472b-85eb-48581d3c20c2"

// const appKey = `bAnWqm7IfUc71ZAgPN3YBEcvXc1Cg6Az`;
// const appSecret = `80gy0PgRJAUqPOMA`;

// curl -X POST https://api.schwabapi.com/v1/oauth/token \
//   -d "grant_type=authorization_code" \
//   -d "code=C0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.nIpPrlNVbnKoZz8hNvWM8h_mklRnZUkGkxaKx7czn1s%40" \
//   -d "redirect_uri=https://127.0.0.1" \
//   -d "client_id=bAnWqm7IfUc71ZAgPN3YBEcvXc1Cg6Az" \
//   -d "client_secret=80gy0PgRJAUqPOMA"

const axios = require('axios');
const open = require('open');
const base64 = require('base-64');
const readline = require('readline');

// Logger function to simulate Python's loguru
const logger = {
    info: console.log,
    debug: console.log,
};

// Function to construct initial authorization URL
function constructInitAuthUrl() {
    const appKey = `bAnWqm7IfUc71ZAgPN3YBEcvXc1Cg6Az`;
    const appSecret = `80gy0PgRJAUqPOMA`;

    // const authUrl = `https://api.schwabapi.com/v1/oauth/authorize?client_id=bAnWqm7IfUc71ZAgPN3YBEcvXc1Cg6Az&redirect_uri=https://127.0.0.1`;
    const authUrl = `https://api.schwabapi.com/v1/oauth/authorize?client_id=${appKey}&redirect_uri=https://127.0.0.1`;

    logger.info('Click to authenticate:');
    logger.info(authUrl);

    return { appKey, appSecret, authUrl };
}

// Function to construct headers and payload
function constructHeadersAndPayload(returnedUrl, appKey, appSecret) {
    const responseCode = returnedUrl.slice(returnedUrl.indexOf('code=') + 5, returnedUrl.indexOf('%40')) + '@';

    const credentials = `${appKey}:${appSecret}`;
    const base64Credentials = base64.encode(credentials);

    const headers = {
        'Authorization': `Basic ${base64Credentials}`,
        'Content-Type': 'application/x-www-form-urlencoded',
    };

    const payload = {
        grant_type: 'authorization_code',
        code: responseCode,
        redirect_uri: 'https://127.0.0.1',
    };

    return { headers, payload };
}

// Function to retrieve tokens from the Schwab API
async function retrieveTokens(headers, payload) {
    try {
        const initTokenResponse = await axios.post('https://api.schwabapi.com/v1/oauth/token', new URLSearchParams(payload), {
            headers: headers
        });

        return initTokenResponse.data;
    } catch (error) {
        logger.info('Error retrieving tokens:', error);
        throw error;
    }
}

// Main function
async function main() {
    const { appKey, appSecret, csAuthUrl } = constructInitAuthUrl();
    console.log(csAuthUrl);
    // await open(csAuthUrl);

    // const rl = readline.createInterface({
    //     input: process.stdin,
    //     output: process.stdout
    // });

    // rl.question('Paste Returned URL: ', async (returnedUrl) => {
    //     const { headers, payload } = constructHeadersAndPayload(returnedUrl, appKey, appSecret);

    //     const tokens = await retrieveTokens(headers, payload);
    //     logger.debug(tokens);

    //     rl.close();
    // });
}

// Run the main function
main();
