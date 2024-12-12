const express = require('express');
const nodemailer = require('nodemailer');
const bodyParser = require('body-parser');
const path = require('path');
require('dotenv').config(); // Load environment variables from .env file

const app = express();

// Set the view engine to EJS
app.set('views', path.join(__dirname, 'templates'));
app.set('view engine', 'ejs');

// Middleware to parse form data
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'static')));

// Routes
app.get('/', (req, res) => {
    res.render('index');
});

app.get('/collections', (req, res) => {
    res.render('collections');
});

app.get('/about', (req, res) => {
    res.render('about');
});


app.get('/contact', (req, res) => {
    res.render('contact'); // Matches the updated contact.ejs file
});

app.get('/thank-you', (req, res) => {
    res.render('thank-you'); // Thank You page for successful submission
});

// New routes for impacts, sustainability, and community
app.get('/impacts', (req, res) => {
    res.render('impacts'); // Ensure impacts.ejs exists in the templates folder
});

app.get('/sustainability', (req, res) => {
    res.render('sustainability'); // Ensure sustainability.ejs exists in the templates folder
});

app.get('/community', (req, res) => {
    res.render('community'); // Ensure community.ejs exists in the templates folder
});

app.get('/other', (req, res) => {
    res.render('other'); // Ensure community.ejs exists in the templates folder
});

// Handle form submission
app.post('/contact', async (req, res) => {
    const { name, email, message } = req.body;

    // Validate input fields
    if (!name || !email || !message) {
        return res.status(400).send('<h1>All fields are required. Please fill out the form completely.</h1>');
    }

    // Configure transporter for nodemailer
    const transporter = nodemailer.createTransport({
        host: 'smtp.gmail.com',
        port: 587,
        secure: false,
        auth: {
            user: process.env.GMAIL_USER,
            pass: process.env.GMAIL_PASS,
        },
    });
    

    const mailOptions = {
        from: `"${name}" <${email}>`, // Include sender's name
        to: process.env.GMAIL_USER, // Email address to receive messages
        subject: `Message from ${name}`,
        text: `You have received a new message from ${name} (${email}):\n\n${message}`,
    };

    try {
        await transporter.sendMail(mailOptions); // Send email
        console.log('Email sent successfully');
        res.redirect('/thank-you'); // Redirect to Thank You page after success
    } catch (error) {
        console.error('Error sending email:', error.message);
        res.status(500).send(`<h1>Something went wrong. Please try again later.</h1><p>${error.message}</p>`);
    }
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
