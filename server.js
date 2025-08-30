const express = require('express');
const path = require('path');

const app = express();

// Serve only static assets from backend/static (no EJS, no views)
app.use(express.static(path.join(__dirname, 'static')));

// Simple health check
app.get('/health', (req, res) => res.json({ ok: true }));

// Everything else -> tell the user to use Flask
app.use((req, res) => {
  res
    .status(404)
    .send('This Node server only serves static assets. Run the Flask app for pages.');
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Node static server running on http://localhost:${PORT}`);
});
