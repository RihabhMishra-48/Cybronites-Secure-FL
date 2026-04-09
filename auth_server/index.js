const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const mailService = require('./mailService');

// Load environment variables from root .env
dotenv.config({ path: '../.env' });

const app = express();
const PORT = process.env.PORT || 5001;

// Middleware
app.use(cors());
app.use(express.json());

// Basic health check
app.get('/health', (req, res) => {
    res.json({ status: 'OK', message: 'Auth server with Mailjet is running' });
});

/**
 * Route to trigger automated email alerts
 */
app.post('/api/mail/send', async (req, res) => {
    const { toEmail, toName, type, details } = req.body;

    if (!toEmail || !toName || !type) {
        return res.status(400).json({ error: 'toEmail, toName, and type are required' });
    }

    try {
        let result;
        switch (type) {
            case 'security-alert':
                result = await mailService.sendSecurityAlert(toEmail, toName, details.alertType, details.details);
                break;
            case 'training-summary':
                result = await mailService.sendTrainingSummary(toEmail, toName, details.roundNumber, details.accuracy);
                break;
            default:
                result = await mailService.sendEmail(toEmail, toName, details.subject, details.textContent, details.htmlContent);
        }
        res.json({ success: true, message: 'Email sent successfully', data: result });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`Auth Server running on port ${PORT}`);
    console.log(`Mailjet automation enabled using: ${process.env.MAIL_USERNAME}`);
});
