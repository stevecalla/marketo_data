const express = require('express');
const app = express();

const PORT = 80;

app.get('/', (req, res) => {
    res.send('Authentication successful');
});

app.listen(PORT, () => {
    console.log(`Server running at https://127.0.0.1:${PORT}`);
});
