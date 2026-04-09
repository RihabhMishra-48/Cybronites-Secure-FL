const mailService = require('./mailService');
const dotenv = require('dotenv');

const path = require('path');
const fs = require('fs');
const envPath = path.resolve(__dirname, '../.env');
console.log('Resolved path:', envPath);
console.log('File exists:', fs.existsSync(envPath));
dotenv.config({ path: envPath });

async function runTest() {
    console.log('--- Testing Mailjet Integration ---');
    console.log(`Using API Key: ${process.env.MAILJET_API_KEY ? 'Set' : 'Missing'}`);
    console.log(`Using API Secret: ${process.env.MAILJET_API_SECRET ? 'Set' : 'Missing'}`);
    
    try {
        console.log('Sending security alert test email...');
        const result = await mailService.sendSecurityAlert(
            'test@example.com', 
            'Test User', 
            'Model Poisoning Attempt', 
            'Unauthorized weights detected from Client 0xAB12'
        );
        console.log('Success!', JSON.stringify(result, null, 2));
    } catch (err) {
        console.error('Test failed:', err.message);
    }
}

runTest();
