# WhatsApp Exam Practice Bot with LLM Agent Integration

A WhatsApp chatbot that helps students practice for computer-based exams like JAMB, WAEC, etc. Now enhanced with LLM agent capabilities for intelligent conversations and explanations.

## Features

- **Intelligent Conversations**: LLM-powered responses for natural interactions
- **Hybrid Processing**: Combines structured bot logic with AI agent capabilities
- **Interactive Exam Practice**: Multiple exam types (JAMB, SAT, etc.)
- **Smart Explanations**: AI-generated explanations and study tips
- **Context-Aware Responses**: Agent understands exam context and progress
- **Web Search Integration**: Real-time information retrieval for questions
- **Multiple Subjects**: Biology, Chemistry, Physics, Math, English, etc.
- **Question Randomization**: Varied practice sessions
- **Score Tracking**: Performance monitoring
- **Image Support**: Visual questions when available

## New LLM Agent Features

- **Natural Language Processing**: Understands complex questions and provides detailed explanations
- **Context-Aware Responses**: Knows your current exam, subject, and progress
- **Smart Help System**: Provides study tips and learning strategies
- **Web Search Integration**: Can search for current information when needed
- **Conversational Interface**: Ask questions naturally instead of using rigid commands

## Quick Start

### 1. Environment Setup
Create a `.env` file with your API keys:
```bash
# Copy the example file
cp .env.example .env

# Edit with your actual API keys
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
```

### 2. Setup and Start Server
```bash
# This will create venv, install dependencies, and start the server
python start_server.py
```

### 3. Setup ngrok (Required for WhatsApp)
```bash
# In a separate terminal
python setup_ngrok.py
```

### 4. Configure Twilio WhatsApp
1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to WhatsApp Sandbox
3. Set your webhook URL to: `https://your-ngrok-url.ngrok.io/webhook/whatsapp`
4. Save the configuration

### 5. Test Your Enhanced Bot
1. Send a WhatsApp message to your Twilio sandbox number
2. Try natural language: "Help me practice JAMB Biology"
3. Ask questions: "Explain photosynthesis" or "What is the powerhouse of the cell?"
4. Use traditional commands: "start", "restart", "exit"

## API Keys Required

### Google AI API Key (Required)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GOOGLE_API_KEY`

### Tavily Search API Key (Optional)
1. Go to [Tavily](https://tavily.com/)
2. Sign up and get your API key
3. Add it to your `.env` file as `TAVILY_API_KEY`
4. This enables web search for current information

## How the LLM Integration Works

### Hybrid Message Processing
The bot now uses a hybrid approach:

1. **Structured Logic**: For specific commands and exam navigation
   - "start", "restart", "exit"
   - Number selections (1, 2, 3)
   - Answer choices (A, B, C, D)

2. **LLM Agent**: For natural language interactions
   - Questions about topics
   - Requests for explanations
   - Study help and tips
   - General conversations

### Context Awareness
The LLM agent receives context about:
- Current exam type (JAMB, SAT, etc.)
- Subject being studied
- Current question and progress
- User's score and performance

### Example Interactions

**Traditional Structured Approach:**
```
User: start
Bot: Welcome! Choose exam: 1. JAMB 2. SAT
User: 1
Bot: Choose subject: 1. Biology 2. Chemistry
```

**New LLM-Enhanced Approach:**
```
User: I want to practice biology for JAMB
Bot: Great! I'll help you practice JAMB Biology. Let me set up some questions for you...

User: What is photosynthesis?
Bot: Photosynthesis is the process by which plants convert light energy into chemical energy (glucose). It occurs in chloroplasts and involves two main stages: light-dependent reactions and the Calvin cycle...

User: Can you explain the answer to question 5?
Bot: [Provides detailed explanation with study tips based on the specific question]
```

## Project Structure

```
whatsapp-bot/
├── venv/                           # Virtual environment
├── app/
│   ├── agent_reflection/           # LLM agent implementation
│   │   ├── RAG_reflection.py      # Main agent with search capabilities
│   │   └── requirements.txt       # Agent-specific dependencies
│   ├── core/
│   │   ├── hybrid_message_handler.py    # Hybrid handlers with LLM
│   │   ├── smart_message_processor.py   # Enhanced message processor
│   │   ├── message_handler.py           # Original handlers (legacy)
│   │   └── message_processor.py         # Original processor (legacy)
│   ├── services/
│   │   ├── llm_agent.py               # LLM agent service
│   │   ├── exam_context_enhancer.py   # Context enhancement for LLM
│   │   ├── state.py                   # State management
│   │   └── exam_registry.py           # Exam type registry
│   ├── data/                       # Exam question data
│   ├── routes/                     # API routes (enhanced)
│   └── utils/                      # Helper functions
├── .env                           # Environment variables (create this)
├── .env.example                   # Environment template
├── main.py                        # FastAPI application
├── requirements.txt               # All dependencies
└── README.md                      # This file
```

## Commands and Interactions

### Traditional Commands (Still Work)
- `start` - Begin a new exam session
- `restart` - Restart current session  
- `exit` - End current session
- `help` - Get help information

### New Natural Language Interactions
- "Help me practice JAMB Biology"
- "Explain photosynthesis"
- "What's the answer to this question?"
- "Give me study tips for chemistry"
- "How do I solve this math problem?"
- "Tell me about cell structure"

### Exam Navigation
- Number selections: "1", "2", "3" (for choosing exams/subjects)
- Answer choices: "A", "B", "C", "D" (for answering questions)
- Natural requests: "I want to practice biology" or "Show me chemistry questions"

## Development

### Environment Management
The `start_server.py` script automatically:
- Creates a virtual environment if it doesn't exist
- Installs/updates all dependencies (including LLM agent requirements)
- Starts the server with auto-reload

### Manual Development Setup
```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install all dependencies (includes LLM agent requirements)
pip install -r requirements.txt

# Run server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing LLM Features
1. Make sure your `.env` file has the required API keys
2. Start the server: `python start_server.py`
3. Test with natural language messages via WhatsApp
4. Check logs for LLM agent activity

## Troubleshooting

### LLM Agent Issues

1. **"LLM agent may not function properly" warning**
   - Check that `GOOGLE_API_KEY` is set in your `.env` file
   - Verify the API key is valid and has quota

2. **Agent responses are slow**
   - This is normal for LLM processing
   - Web search queries take additional time
   - Consider upgrading to faster models if needed

3. **Agent not responding**
   - Check server logs for error messages
   - Verify internet connection for API calls
   - Ensure all dependencies are installed

### Traditional Issues

4. **Virtual environment issues**
   - Delete the `venv` folder and run `python start_server.py` again
   - Make sure Python 3.7+ is installed

5. **ngrok tunnel not working**
   - Make sure you've added your authtoken
   - Check if port 8000 is available
   - Restart ngrok if needed

6. **WhatsApp messages not received**
   - Verify webhook URL in Twilio console
   - Check ngrok tunnel is active
   - Ensure server is running on port 8000

### Logs and Debugging

The enhanced bot provides detailed logging:
- LLM agent processing steps
- Hybrid handler decisions (LLM vs structured logic)
- Context enhancement information
- Traditional bot state changes
- API call results and errors

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /webhook/whatsapp` - Enhanced WhatsApp webhook with LLM
- `GET /webhook/whatsapp` - Webhook verification

## License

This project is open source and available under the MIT License.