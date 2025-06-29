# Examinator - WhatsApp Exam Practice Bot with Real Past Questions

A comprehensive WhatsApp chatbot that helps students practice for computer-based exams using **real past questions** from JAMB, SAT, NEET, and more. Enhanced with AI-powered personalized learning that tracks performance, identifies weaknesses, and provides targeted practice.

## 🎯 Key Features

### Real Past Questions System
- **Authentic Questions**: Real past questions from official exam bodies
- **Multiple Years**: Questions sourced from multiple years (2015-2024)
- **Year References**: Each question shows its source year
- **Standard Format**: Proper exam format with correct number of questions
- **Comprehensive Coverage**: All major subjects for each exam type

### Supported Exams & Subjects

#### JAMB (Joint Admissions and Matriculation Board)
- **50 questions per subject** (standard JAMB format)
- **Subjects**: Mathematics, English Language, Biology, Chemistry, Physics, Geography, Economics, Government, Literature in English, History, Agricultural Science, Computer Studies
- **Years**: 2015-2024

#### SAT (Scholastic Assessment Test)
- **Variable questions per section** (standard SAT format)
- **Subjects**: Math (58 questions), Reading and Writing (54 questions), Math Level 2, Biology, Chemistry, Physics
- **Years**: 2018-2024

#### NEET (National Eligibility cum Entrance Test)
- **50 questions per subject** (standard NEET format)
- **Subjects**: Physics, Chemistry, Biology, Botany, Zoology
- **Years**: 2016-2024

### Intelligent AI Features
- **LLM-Powered Question Fetching**: Uses advanced AI to search and extract real past questions
- **Context-Aware Responses**: AI understands exam context and user progress
- **Smart Explanations**: Detailed explanations tailored to user's level
- **Performance Analytics**: Comprehensive tracking and personalized recommendations

## 🚀 How It Works

### 1. **Real Question Fetching**
When a user selects a subject:
```
User: 1 (selects Biology)
Bot: 🔍 Fetching 50 real JAMB past questions...
     This may take a moment as we search for authentic past questions from multiple years.

[AI searches for real JAMB Biology questions from 2015-2024]

Bot: 🎯 Starting JAMB Biology Practice
     📚 50 real past questions from multiple years
     ⏱️ Standard JAMB format

     Question 1/50 (JAMB 2023):
     Which of the following is the basic unit of life?
     A. Tissue
     B. Cell
     C. Organ
     D. Organism
     
     Reply with A, B, C, or D
```

### 2. **Enhanced Question Format**
Each question includes:
- **Year Reference**: Shows which year the question is from
- **Real Source**: Authentic past exam questions
- **Proper Format**: Standard exam format (A, B, C, D options)
- **Detailed Explanations**: Comprehensive explanations for learning

### 3. **Standard Exam Structure**
- **JAMB**: 50 questions per subject (matches real exam)
- **SAT**: Variable questions per section (matches real exam)
- **NEET**: 50 questions per subject (matches real exam)

## 🛠️ Quick Start

### 1. Environment Setup
```bash
# Copy and configure environment variables
cp .env.example .env

# Add your API keys:
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
```

### 2. Install and Start
```bash
# This will create venv, install dependencies, and start the server
python start_server.py
```

### 3. Setup ngrok for WhatsApp
```bash
# In a separate terminal
python setup_ngrok.py
```

### 4. Configure Twilio WhatsApp
1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to WhatsApp Sandbox
3. Set webhook URL to: `https://your-ngrok-url.ngrok.io/webhook/whatsapp`

## 📊 Example User Experience

### Comprehensive Subject Selection
```
User: start
Bot: 🎓 Welcome to Examinator!

Available exams:
1. JAMB
2. SAT  
3. NEET

Please reply with the number of your choice.

User: 1
Bot: ✅ You selected: JAMB

Available JAMB subjects:
1. Mathematics
2. English Language
3. Biology
4. Chemistry
5. Physics
6. Geography
7. Economics
8. Government
9. Literature in English
10. History
11. Agricultural Science
12. Computer Studies

Please reply with the number of your choice.
```

### Real Question Practice
```
User: 3 (Biology)
Bot: 🔍 Fetching 50 real JAMB past questions...

[AI fetches authentic questions]

Bot: 🎯 Starting JAMB Biology Practice
     📚 50 real past questions from multiple years
     ⏱️ Standard JAMB format

     Question 1/50 (JAMB 2023):
     Which organelle is known as the powerhouse of the cell?
     A. Nucleus
     B. Ribosome  
     C. Mitochondria
     D. Endoplasmic reticulum

     Reply with A, B, C, or D

User: C
Bot: ✅ Correct! The correct answer is C.

     📅 Source: JAMB 2023
     💡 Mitochondria are known as the powerhouse of the cell because they produce ATP through cellular respiration.
     
     📊 Progress: 1/1 correct (100.0%)

     Question 2/50 (JAMB 2021):
     [Next question...]
```

## 🔧 Technical Architecture

### Question Fetching System
```python
# app/services/question_fetcher.py
class QuestionFetcher:
    async def fetch_questions(self, exam: str, subject: str, num_questions: int):
        # Uses LLM agent to search for real past questions
        # Parses and structures questions properly
        # Returns authentic exam questions with year references
```

### Enhanced Exam Types
```python
# app/services/exam_types/enhanced_jamb.py
class EnhancedJAMBExamType:
    async def load_questions_async(self, user_phone: str, user_state: Dict):
        # Fetches real JAMB questions using QuestionFetcher
        # Ensures 50 questions per subject (JAMB standard)
        # Includes year references and proper formatting
```

### Exam Structure Configuration
```json
// app/data/exam_structure.json
{
  "jamb": {
    "subjects": {
      "Biology": {
        "questions_per_exam": 50,
        "time_limit_minutes": 60,
        "years_available": ["2015", "2016", ..., "2024"]
      }
    }
  }
}
```

## 📈 Performance Tracking

### Enhanced Analytics
- **Question-Level Tracking**: Each question answer is recorded with year and source
- **Subject Performance**: Track performance across all subjects
- **Year-Based Analysis**: See how you perform on questions from different years
- **Real Exam Simulation**: Practice with authentic exam conditions

### Performance Reports
```
User: How am I doing?
Bot: 📊 Your Performance Summary:

• Total Sessions: 15
• Questions Answered: 750 (real past questions)
• Recent Accuracy: 78%
• Trend: Improving

🎯 Subject Performance:
• JAMB Biology: 85% (2023: 90%, 2022: 80%)
• JAMB Chemistry: 72% (2023: 75%, 2022: 69%)

💪 Your Strengths:
• Cell Biology (89% accuracy)
• Genetics (85% accuracy)

📚 Recommendations:
• Focus on Organic Chemistry questions
• Practice more 2021-2022 JAMB Chemistry questions
```

## 🔑 API Keys Required

### Google AI API Key (Required)
- Needed for LLM agent to search and extract real questions
- Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Tavily Search API Key (Recommended)
- Enhances question search capabilities
- Get from [Tavily](https://tavily.com/)

## 📁 Project Structure

```
examinator/
├── app/
│   ├── services/
│   │   ├── question_fetcher.py          # Real question fetching
│   │   ├── exam_types/
│   │   │   ├── enhanced_jamb.py         # JAMB with real questions
│   │   │   ├── enhanced_sat.py          # SAT with real questions
│   │   │   └── neet.py                  # NEET with real questions
│   │   └── ...
│   ├── data/
│   │   ├── exam_structure.json          # Exam configurations
│   │   └── user_analytics/              # User performance data
│   └── ...
├── requirements.txt                     # Includes supabase for future features
└── README.md
```

## 🚀 Future Enhancements

### Database Integration (Planned)
- **Supabase Integration**: Store questions and user data in database
- **Question Bank**: Comprehensive database of past questions
- **Leaderboards**: Compare performance with other users
- **Advanced Analytics**: Detailed performance insights

### Additional Features
- **Timed Exams**: Full exam simulation with time limits
- **Mixed Practice**: Questions from multiple years in one session
- **Difficulty Progression**: Adaptive difficulty based on performance
- **Study Plans**: Personalized study schedules

## 📞 Support

For issues or questions:
1. Check that all API keys are properly configured
2. Ensure ngrok tunnel is active for WhatsApp integration
3. Verify server is running on port 8000
4. Review server logs for any errors

## 📄 License

This project is open source and available under the MIT License.

---

**Examinator** - Practice with real past questions, master your exams! 🎓