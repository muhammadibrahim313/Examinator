# WhatsApp Exam Practice Bot( bolt new hack)

A WhatsApp chatbot that helps students practice for computer-based exams like JAMB, WAEC, etc.

## Features

- Interactive exam practice via WhatsApp
- Multiple exam types (JAMB, etc.)
- Multiple subjects (Biology, Chemistry, etc.)
- Question randomization
- Score tracking
- Image support for questions

## Quick Start

### 1. Setup and Start Server (Recommended)
```bash
# This will create venv, install dependencies, and start the server
python start_server.py
```

### 2. Setup ngrok (Required for WhatsApp)
```bash
# In a separate terminal
python setup_ngrok.py
```

### 3. Configure Twilio WhatsApp
1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to WhatsApp Sandbox
3. Set your webhook URL to: `https://your-ngrok-url.ngrok.io/webhook/whatsapp`
4. Save the configuration

### 4. Test Your Bot
1. Send a WhatsApp message to your Twilio sandbox number
2. Type "start" to begin
3. Follow the prompts to select exam, subject, and year
4. Answer the questions!

## Manual Setup (Alternative)

### 1. Create Virtual Environment
```bash
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Install and Configure ngrok

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
   
   # On macOS with Homebrew
   brew install ngrok/ngrok/ngrok
   
   # On Windows, download from https://ngrok.com/download
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

### 4. Start the Server

#### Option A: Using the startup script (handles venv automatically)
```bash
python start_server.py
```

#### Option B: Manual startup (requires activated venv)
```bash
# Make sure virtual environment is activated first
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Project Structure

```
whatsapp-bot/
├── venv/               # Virtual environment (auto-created)
├── app/
│   ├── data/           # Exam question data
│   │   └── jamb/       # JAMB exam questions
│   ├── routes/         # API routes
│   ├── services/       # Business logic
│   └── utils/          # Helper functions
├── main.py             # FastAPI application
├── requirements.txt    # Python dependencies
├── setup_ngrok.py      # ngrok setup script
├── start_server.py     # Server startup script (with venv management)
└── ngrok_url.txt       # Auto-generated ngrok URLs
```

## Adding New Exams

1. Create a new folder in `app/data/` with the exam name (e.g., `waec`)
2. Add JSON files with the format: `Subject-Year.json`
3. Follow the existing JSON structure for questions

Example JSON structure:
```json
{
  "exam": "JAMB",
  "subject": "Biology",
  "year": "2023",
  "questions": [
    {
      "id": 1,
      "question": "Which of the following is the basic unit of life?",
      "options": {
        "A": "Tissue",
        "B": "Cell",
        "C": "Organ",
        "D": "Organism"
      },
      "correct_answer": "B",
      "explanation": "The cell is the basic structural and functional unit of all living organisms.",
      "image_ref": "https://example.com/image.jpg"
    }
  ]
}
```

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

### Environment Management
The `start_server.py` script automatically:
- Creates a virtual environment if it doesn't exist
- Installs/updates dependencies
- Starts the server with auto-reload

### Manual Development Setup
```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install development dependencies
pip install -r requirements.txt

# Run server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Troubleshooting

### Common Issues

1. **Virtual environment issues**
   - Delete the `venv` folder and run `python start_server.py` again
   - Make sure Python 3.7+ is installed

2. **ngrok tunnel not working**
   - Make sure you've added your authtoken
   - Check if port 8000 is available
   - Restart ngrok if needed

3. **WhatsApp messages not received**
   - Verify webhook URL in Twilio console
   - Check ngrok tunnel is active
   - Ensure server is running on port 8000

4. **Questions not loading**
   - Check JSON file format
   - Verify file paths in `app/data/`
   - Check server logs for errors

5. **Dependencies not installing**
   - Make sure you have internet connection
   - Try upgrading pip: `pip install --upgrade pip`
   - Check Python version (3.7+ required)

### Logs

Server logs will show:
- Incoming WhatsApp messages
- User state changes
- Errors and debugging information

### File Locations

- Virtual environment: `./venv/`
- ngrok URLs: `./ngrok_url.txt` (auto-generated)
- Server logs: Console output
- User states: In-memory (resets on server restart)

## License

This project is open source and available under the MIT License.
