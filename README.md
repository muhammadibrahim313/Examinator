# WhatsApp Exam Practice Bot

A WhatsApp chatbot that helps students practice for computer-based exams like JAMB, WAEC, etc.

## Features

- Interactive exam practice via WhatsApp
- Multiple exam types (JAMB, etc.)
- Multiple subjects (Biology, Chemistry, etc.)
- Question randomization
- Score tracking
- Image support for questions

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install and Configure ngrok

ngrok creates a secure tunnel to your local server, making it accessible from the internet (required for WhatsApp webhooks).

#### Option A: Automatic Setup (Recommended)
```bash
python setup_ngrok.py
```

#### Option B: Manual Setup
1. Install ngrok:
   ```bash
   # On Ubuntu/Debian
   curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
   echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
   sudo apt update && sudo apt install ngrok
   ```

2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken

3. Configure ngrok:
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
   ```

4. Start ngrok tunnel:
   ```bash
   ngrok http 8000
   ```

### 3. Start the Server

#### Option A: Using the startup script
```bash
python start_server.py
```

#### Option B: Manual startup
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Configure Twilio WhatsApp

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to WhatsApp Sandbox
3. Set your webhook URL to: `https://your-ngrok-url.ngrok.io/webhook/whatsapp`
4. Save the configuration

### 5. Test Your Bot

1. Send a WhatsApp message to your Twilio sandbox number
2. Type "start" to begin
3. Follow the prompts to select exam, subject, and year
4. Answer the questions!

## Project Structure

```
whatsapp-bot/
├── app/
│   ├── data/           # Exam question data
│   │   └── jamb/       # JAMB exam questions
│   ├── routes/         # API routes
│   ├── services/       # Business logic
│   └── utils/          # Helper functions
├── main.py             # FastAPI application
├── requirements.txt    # Python dependencies
├── setup_ngrok.py      # ngrok setup script
└── start_server.py     # Server startup script
```

## Adding New Exams

1. Create a new folder in `app/data/` with the exam name (e.g., `waec`)
2. Add JSON files with the format: `Subject-Year.json`
3. Follow the existing JSON structure for questions

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /webhook/whatsapp` - WhatsApp webhook
- `GET /webhook/whatsapp` - Webhook verification

## Commands

Users can send these commands via WhatsApp:
- `start` - Begin a new exam session
- `restart` - Restart current session
- `exit` - End current session

## Development

The server runs with auto-reload enabled, so changes to the code will automatically restart the server.

## Troubleshooting

### Common Issues

1. **ngrok tunnel not working**
   - Make sure you've added your authtoken
   - Check if port 8000 is available
   - Restart ngrok if needed

2. **WhatsApp messages not received**
   - Verify webhook URL in Twilio console
   - Check ngrok tunnel is active
   - Ensure server is running on port 8000

3. **Questions not loading**
   - Check JSON file format
   - Verify file paths in `app/data/`
   - Check server logs for errors

### Logs

Server logs will show:
- Incoming WhatsApp messages
- User state changes
- Errors and debugging information

## License

This project is open source and available under the MIT License.