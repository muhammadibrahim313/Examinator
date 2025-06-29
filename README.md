# WhatsApp Exam Practice Bot with Personalized Learning

A WhatsApp chatbot that helps students practice for computer-based exams like JAMB, WAEC, etc. Now enhanced with LLM agent capabilities and personalized learning that tracks performance, identifies weaknesses, and provides targeted practice.

## 🎯 Key Features

### Personalized Learning System
- **Performance Tracking**: Comprehensive analytics of user performance across subjects and topics
- **Weakness Identification**: AI identifies areas where users struggle most
- **Targeted Practice**: Questions are selected based on user's performance history
- **Adaptive Difficulty**: Question difficulty adjusts based on current performance
- **Progress Monitoring**: Track improvement over time with detailed statistics

### Intelligent Conversations
- **LLM-Powered Responses**: Natural language processing for complex questions
- **Context-Aware**: AI understands exam context and user progress
- **Smart Explanations**: Detailed explanations tailored to user's level
- **Study Recommendations**: Personalized study tips based on performance data

### Comprehensive Exam Support
- **Multiple Exam Types**: JAMB, SAT, and more
- **Various Subjects**: Biology, Chemistry, Physics, Math, English, etc.
- **Performance Analytics**: Detailed insights into strengths and weaknesses
- **Score Tracking**: Historical performance data with trends

## 🚀 How Personalization Works

### 1. **Performance Tracking**
Every question answered is tracked:
- Correct/incorrect responses
- Time taken per question
- Subject and topic performance
- Session completion rates

### 2. **Weakness Analysis**
The system identifies:
- Subjects with low accuracy (< 70%)
- Topics with poor performance (< 60%)
- Consistent problem areas
- Learning patterns

### 3. **Personalized Question Selection**
When users start practice:
- Questions are selected based on identified weaknesses
- Difficulty adapts to current performance
- Focus areas are prioritized
- Balanced mix ensures comprehensive coverage

### 4. **Adaptive Feedback**
During practice sessions:
- Real-time encouragement based on performance
- Targeted study tips for wrong answers
- Progress celebrations for improvements
- Recommendations for next steps

## 📊 Example User Journey

### First-Time User
```
User: start
Bot: Welcome! Choose exam: 1. JAMB 2. SAT
User: 1
Bot: Choose subject: 1. Biology 2. Chemistry
User: 1
Bot: Starting JAMB Biology practice...
[Regular questions, performance tracked]
```

### Returning User with History
```
User: I want to practice biology
Bot: Welcome back! Based on your history, you've struggled with cell biology (45% accuracy). I'll focus on those areas.

[Personalized questions targeting weaknesses]

Bot: Great improvement! Your cell biology accuracy is now 70%. Let's work on genetics next.
```

### Performance Queries
```
User: How am I doing?
Bot: 📊 Your Performance Summary:
• Total Sessions: 15
• Questions Answered: 150
• Recent Accuracy: 78%
• Trend: Improving

🎯 Areas to Focus On:
• Cell Biology (45% accuracy)
• Organic Chemistry (52% accuracy)

💪 Your Strengths:
• Genetics (89% accuracy)
• Ecology (85% accuracy)
```

## 🛠️ Quick Start

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
2. Try: "Help me practice JAMB Biology"
3. Ask: "How am I performing?" or "What are my weak areas?"
4. Use traditional commands: "start", "restart", "exit"

## 🔑 API Keys Required

### Google AI API Key (Required)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GOOGLE_API_KEY`

### Tavily Search API Key (Optional)
1. Go to [Tavily](https://tavily.com/)
2. Sign up and get your API key
3. Add it to your `.env` file as `TAVILY_API_KEY`
4. This enables web search for current information

## 📁 Project Structure

```
whatsapp-bot/
├── venv/                           # Virtual environment
├── app/
│   ├── agent_reflection/           # LLM agent implementation
│   ├── core/
│   │   ├── enhanced_smart_processor.py     # Main message processor
│   │   ├── enhanced_hybrid_handlers.py     # Personalized handlers
│   │   └── ...
│   ├── services/
│   │   ├── user_analytics.py              # Performance tracking
│   │   ├── personalized_question_selector.py  # Smart question selection
│   │   ├── enhanced_llm_agent.py          # Enhanced AI agent
│   │   ├── enhanced_state.py              # State with analytics
│   │   └── ...
│   ├── data/
│   │   ├── user_analytics/         # User performance data (auto-created)
│   │   ├── jamb/                   # Exam questions
│   │   └── sat/
│   └── ...
├── .env                           # Environment variables (create this)
├── requirements.txt               # All dependencies
└── README.md                      # This file
```

## 💬 Interaction Examples

### Natural Language Interactions
```
User: "I'm struggling with biology"
Bot: "I can see you've had difficulty with cell biology (45% accuracy) and genetics (52% accuracy). Let me create a focused practice session for you..."

User: "Explain photosynthesis"
Bot: "Photosynthesis is the process by which plants convert light energy into chemical energy... [detailed explanation] Based on your history, you might want to review the Calvin cycle specifically."

User: "Give me harder questions"
Bot: "Based on your 85% accuracy, I'll select more challenging questions to help you improve further..."
```

### Performance Tracking
```
User: "Show my progress"
Bot: "📈 Progress Report:
Week 1: 45% average
Week 2: 62% average  
Week 3: 78% average
Great improvement! You've increased by 33% in 3 weeks!"
```

## 🔧 Advanced Features

### Analytics API
Access user analytics programmatically:
```
GET /analytics/{user_phone}
```

### Personalized Recommendations
The system provides:
- Study schedule suggestions
- Topic prioritization
- Difficulty progression
- Performance-based encouragement

### Adaptive Learning
- Questions become harder as performance improves
- Focus shifts to weak areas automatically
- Learning patterns are identified and optimized

## 🚀 Development

### Adding New Question Categories
1. Update `_extract_question_topic()` in `personalized_question_selector.py`
2. Add topic keywords for better categorization
3. Questions are automatically categorized and tracked

### Customizing Analytics
1. Modify `user_analytics.py` to track additional metrics
2. Update recommendation algorithms
3. Add new performance indicators

## 📊 Performance Metrics Tracked

- **Overall Accuracy**: Percentage of correct answers
- **Subject Performance**: Accuracy per subject
- **Topic Mastery**: Performance on specific topics
- **Learning Velocity**: Rate of improvement
- **Session Patterns**: Frequency and duration
- **Difficulty Progression**: Advancement through levels
- **Weakness Recovery**: Improvement in problem areas

## 🎯 Future Enhancements

- **Spaced Repetition**: Questions resurface based on forgetting curves
- **Peer Comparison**: Anonymous performance comparisons
- **Study Streaks**: Gamification elements
- **Detailed Reports**: Comprehensive performance reports
- **Teacher Dashboard**: Instructor view of student progress

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review server logs for errors
3. Ensure all API keys are properly configured
4. Verify ngrok tunnel is active

## 📄 License

This project is open source and available under the MIT License.