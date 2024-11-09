async function fetchCampaigns(url, allResults = []) {
  try {
    const response = await fetch(url);

    // Check if the response is successful
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    // Parse the JSON response
    const data = await response.json();

    return data;

  } catch (error) {
    // Log any error that occurs
    console.error('Error fetching data:', error);
    return null;
  }
}

module.exports = fetchCampaigns;

