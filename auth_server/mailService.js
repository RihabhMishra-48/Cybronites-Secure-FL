const Mailjet = require('node-mailjet');
const dotenv = require('dotenv');

// Load environment variables from root .env if running from auth_server
dotenv.config({ path: '../.env' });

class MailService {
    constructor() {
        this.mailjet = Mailjet.apiConnect(
            process.env.MAILJET_API_KEY || process.env.MAIL_USERNAME || 'YOUR_API_KEY',
            process.env.MAILJET_API_SECRET || process.env.MAIL_PASSWORD || 'YOUR_API_SECRET'
        );
    }

    /**
     * Send a generic email
     * @param {string} toEmail - Recipient email
     * @param {string} toName - Recipient name
     * @param {string} subject - Email subject
     * @param {string} textContent - Plain text content
     * @param {string} htmlContent - HTML content
     */
    async sendEmail(toEmail, toName, subject, textContent, htmlContent) {
        try {
            const result = await this.mailjet
                .post("send", { 'version': 'v3.1' })
                .request({
                    "Messages": [
                        {
                            "From": {
                                "Email": process.env.MAILJET_FROM_EMAIL || process.env.MAIL_FROM || "no-reply@guardian.sys",
                                "Name": "AI Guardian System"
                            },
                            "To": [
                                {
                                    "Email": toEmail,
                                    "Name": toName
                                }
                            ],
                            "Subject": subject,
                            "TextPart": textContent,
                            "HTMLPart": htmlContent,
                            "CustomID": "AppMailAutomation"
                        }
                    ]
                });
            console.log(`Email sent successfully to ${toEmail}`);
            return result.body;
        } catch (err) {
            console.error(`Failed to send email to ${toEmail}:`, err.statusCode, err.message);
            throw err;
        }
    }

    /**
     * Send security alert email
     */
    async sendSecurityAlert(toEmail, toName, alertType, details) {
        const subject = `🚨 SECURITY ALERT: ${alertType} detected`;
        const html = `
            <div style="font-family: Arial, sans-serif; border: 2px solid #ff4444; padding: 20px; border-radius: 10px;">
                <h2 style="color: #ff4444;">Security Alert</h2>
                <p>Hello <strong>${toName}</strong>,</p>
                <p>Our system has detected a potential security threat in the Federated Learning network.</p>
                <div style="background: #f8f8f8; padding: 15px; border-left: 5px solid #ff4444; margin: 10px 0;">
                    <strong>Alert Type:</strong> ${alertType}<br/>
                    <strong>Details:</strong> ${details}<br/>
                    <strong>Timestamp:</strong> ${new Date().toISOString()}
                </div>
                <p>Please log in to the dashboard to investigate immediately.</p>
                <a href="#" style="display: inline-block; background: #ff4444; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a>
                <p style="font-size: 0.8em; color: #777; margin-top: 20px;">This is an automated message from the AI Guardian System.</p>
            </div>
        `;
        return this.sendEmail(toEmail, toName, subject, `Security Alert: ${alertType} - ${details}`, html);
    }

    /**
     * Send training summary email
     */
    async sendTrainingSummary(toEmail, toName, roundNumber, accuracy) {
        const subject = `📊 Training Summary: Round ${roundNumber} Complete`;
        const html = `
            <div style="font-family: Arial, sans-serif; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                <h2 style="color: #4CAF50;">Federated Learning Round Complete</h2>
                <p>Hello <strong>${toName}</strong>,</p>
                <p>Round <strong>${roundNumber}</strong> of the federated learning process has successfully finished.</p>
                <div style="background: #e7f3fe; padding: 15px; border-left: 5px solid #2196F3; margin: 10px 0;">
                    <strong>Current Global Accuracy:</strong> ${(accuracy * 100).toFixed(2)}%<br/>
                    <strong>Status:</strong> Converging
                </div>
                <p>Check the real-time visualizer for more metrics.</p>
                <p style="font-size: 0.8em; color: #777; margin-top: 20px;">AI Guardian Federated Learning System</p>
            </div>
        `;
        return this.sendEmail(toEmail, toName, subject, `Training Summary: Round ${roundNumber} complete with ${accuracy} accuracy.`, html);
    }
}

module.exports = new MailService();
