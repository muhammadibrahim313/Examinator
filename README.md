# Examinator - Flexible WhatsApp Exam Practice Bot

A revolutionary WhatsApp chatbot that helps students practice for computer-based exams using **real past questions**. Students can choose to practice by **topics** OR **years** with complete flexibility across all supported exams.

## 🎯 Key Features

### Dual Practice System - Topics OR Years
- **Practice by Topic**: Choose specific topics like "Cell Biology" or "Algebra"
- **Practice by Year**: Select specific years (2015-2024) for complete coverage
- **Mixed Practice**: Get questions from all topics in a subject
- **Weak Areas Focus**: AI identifies and focuses on your weak areas
- **Multi-Year Questions**: Topic practice automatically sources from multiple years

### Real Past Questions
- **Authentic Questions**: Real past questions from official exam bodies
- **Multiple Years**: Questions automatically sourced from 2015-2024 (JAMB), 2018-2024 (SAT), 2016-2024 (NEET)
- **Topic & Year References**: Each question shows its topic and source year
- **Standard Format**: Proper exam format with correct number of questions

### Personalized Analytics & Recommendations 🧠
- **Automatic performance tracking**: Every session and question is logged for analytics.
- **Personalized recommendations**: Get actionable study tips based on your performance, weak areas, and improvement trends.
- **On-demand performance summaries**: Ask "How am I doing?" or "Show my progress" anytime.
- **Strengths & Weaknesses**: See your top strengths and weaknesses by subject and topic.
- **Improvement Trends**: Track if you are improving, stable, or declining over time.

### Smart Performance Reports 📊
- **Natural language queries**: Ask about your stats, progress, or weaknesses in plain English.
- **Detailed feedback**: Get total sessions, questions answered, accuracy, and recommendations.
- **Session history**: Review your recent performance and trends.

### Flexible Navigation & Test Control 🕹️
- **Go back**: Use "back", "menu", or "previous" to return to earlier steps.
- **Pause/Stop/Submit**: Use "pause", "stop", or "submit" during exams.
- **Restart/Exit**: Instantly restart or exit sessions with simple commands.
- **Error recovery**: Easily recover from mistakes or change your mind mid-flow.

### LLM-Powered Help, FAQ & Open-Ended Queries 🤖
- **Ask anything**: Use "ask: <your question>" for open-ended queries or research.
- **Smart help**: Get context-aware help and FAQ at any time.
- **Hybrid LLM**: Uses Groq (primary) and Gemini (fallback) for robust, up-to-date answers.

### Async Question Loading ⚡
- **No loading delays**: Questions are delivered instantly with async backend logic.

### Session Timeout & Cleanup
- **Automatic session cleanup**: Sessions expire after 1 hour of inactivity for privacy and performance.

### Supported Exams & Subjects

#### JAMB (Joint Admissions and Matriculation Board)
**All 12 subjects with flexible practice:**
- **Mathematics**: 50 questions per exam
- **English Language**: 50 questions per exam
- **Biology**: 50 questions per exam
- **Chemistry**: 50 questions per exam
- **Physics**: 50 questions per exam
- **Geography**: 50 questions per exam
- **Economics**: 50 questions per exam
- **Government**: 50 questions per exam
- **Literature in English**: 50 questions per exam
- **History**: 50 questions per exam
- **Agricultural Science**: 50 questions per exam
- **Computer Studies**: 50 questions per exam

#### SAT (Scholastic Assessment Test)
- **Math**: 58 questions per exam
- **Reading and Writing**: 54 questions per exam
- **Biology**: 80 questions per exam
- **Chemistry**: 85 questions per exam
- **Physics**: 75 questions per exam
- **Math Level 2**: 50 questions per exam

#### NEET (National Eligibility cum Entrance Test)
- **Physics**: 50 questions per exam
- **Chemistry**: 50 questions per exam
- **Biology**: 50 questions per exam
- **Botany**: 25 questions per exam
- **Zoology**: 25 questions per exam

## 🚀 How the Flexible Practice System Works

### 1. **Choose Exam and Subject**
```
User: start
Bot: 🎓 Welcome to Examinator!

Available exams:
1. JAMB
2. SAT
3. NEET

User: 1
Bot: ✅ You selected: JAMB

Available JAMB subjects:
1. Mathematics
2. English Language
3. Biology
[... all 12 subjects]

User: 3
Bot: ✅ You selected: Biology
```

### 2. **Choose Practice Mode - Topics OR Years**
```
Bot: 🎯 How would you like to practice?

1. Practice by Topic
   📚 Focus on specific topics like 'Cell Biology' or 'Genetics'
   🎯 Questions from multiple years on your chosen topic

2. Practice by Year
   📅 Practice questions from a specific year (2015-2024)
   📊 Complete year coverage with all topics

Please reply with 1 or 2.
```

### 3. **Topic-Based Practice**
```
User: 1 (Practice by Topic)
Bot: ✅ You selected: Practice by Topic

📚 Choose a topic for Biology:

1. Cell Biology and Organization
2. Genetics and Heredity
3. Evolution and Ecology
4. Plant Biology and Physiology
5. Animal Biology and Physiology
6. Human Biology and Health
7. Reproduction and Development
8. Classification of Living Things
9. Biochemistry and Metabolism
10. Environmental Biology
11. Mixed Practice (All Topics)
12. Weak Areas Focus

User: 1 (Cell Biology)
Bot: ✅ You selected: Cell Biology and Organization

🔍 Fetching 25 real JAMB past questions...
📚 Practice questions on Cell Biology and Organization
⏱️ Questions from multiple years (2015-2024)

🎯 Starting JAMB Biology Practice
📚 Topic: Cell Biology and Organization
📊 25 real past questions from multiple years

Question 1/25 (JAMB 2023 - Cell Biology):
Which organelle is known as the powerhouse of the cell?
A. Nucleus
B. Ribosome
C. Mitochondria
D. Endoplasmic reticulum

Reply with A, B, C, or D
```

### 4. **Year-Based Practice**
```
User: 2 (Practice by Year)
Bot: ✅ You selected: Practice by Year

📅 Choose a year for Biology:

1. 2024
2. 2023
3. 2022
4. 2021
5. 2020
6. 2019
7. 2018
8. 2017
9. 2016
10. 2015

User: 2 (2023)
Bot: ✅ You selected: 2023

🔍 Fetching 50 real JAMB 2023 questions...
📚 Complete Biology practice from 2023
📊 Standard JAMB format

🎯 Starting JAMB Biology Practice
📚 JAMB 2023 - Complete Biology
📊 50 real past questions
📅 Questions from 2023

Question 1/50 (JAMB 2023):
[Question from 2023 covering any Biology topic]
```

### 5. **Mixed Practice**
```
User: 11 (Mixed Practice)
Bot: ✅ You selected: Mixed Practice (All Topics)

🔍 Fetching 50 real JAMB past questions...
📚 Mixed practice covering all Biology topics
⏱️ Questions from multiple years

[Questions from various topics: Cell Biology, Genetics, Ecology, etc.]
```

### 6. **On-Demand Performance & Analytics**
```
User: How am I doing in biology?
Bot: 📊 Your Biology Performance:

🎯 Topic Performance:
• Cell Biology: 85% (25 questions from 2020-2024)
• Genetics: 72% (20 questions from 2018-2023)
• Ecology: 90% (15 questions from 2019-2024)

📅 Year Performance:
• JAMB 2023: 78% (50 questions)
• JAMB 2022: 82% (30 questions)

💪 Recommendations:
• Focus more on Genetics concepts
• Practice more 2021-2022 questions
• Review Cell Biology fundamentals
```

### 7. **Personalized Recommendations**
```
User: What should I focus on next?
Bot: 💡 Personalized Recommendations:
• Focus more practice on Genetics - current accuracy: 72%
• Review Cell Biology concepts - you've struggled with this topic
• Consider reviewing fundamental concepts before attempting more questions
```

### 8. **Flexible Navigation & Test Control**
```
User: back
Bot: 🔙 Going back to subject selection for JAMB

[Shows subject list again]

User: stop
Bot: 🛑 Test stopped. Your progress has been saved. Send 'resume' to continue or 'start' for a new session.

User: submit
Bot: ✅ Test submitted! Here is your score and feedback...
```

### 9. **LLM-Powered Help, FAQ & Open-Ended Queries**
```
User: help
Bot: 🆘 Help & Commands
• 'start' - Begin new practice session
• 'restart' - Start over completely
• 'back' - Go to previous step
• 'help' - Show this help
• 'ask: <your question>' - Chat with AI

User: ask: What is photosynthesis?
Bot: [LLM-powered answer with up-to-date information]
```

## 🎯 Benefits of Flexible Practice

### For Students
- **Complete Freedom**: Choose topics OR years based on your study needs
- **Targeted Learning**: Focus on specific topics you need to improve
- **Comprehensive Coverage**: Practice complete years for exam simulation
- **Weakness Identification**: AI tracks which topics you struggle with
- **Efficient Study**: Practice exactly what you need, when you need it
- **Personalized Feedback**: Get actionable recommendations and progress reports

### For Exam Preparation
- **Real Questions**: Authentic past questions maintain exam authenticity
- **Topic Mastery**: Master one topic at a time
- **Year Familiarity**: Practice complete years to understand exam patterns
- **Performance Tracking**: See your progress in each topic and year
- **Adaptive Learning**: System focuses on your weak areas
- **Session Analytics**: Review your improvement trends and session history

## 🛠️ Quick Start

### 1. Environment Setup
```bash
cp .env.example .env
# Add your API keys to .env file
```

### 2. Install and Start
```bash
python start_server.py
```

### 3. Setup ngrok for WhatsApp
```bash
python setup_ngrok.py
```

### 4. Configure Twilio WhatsApp
Set webhook URL to: `https://your-ngrok-url.ngrok.io/webhook/whatsapp`

## 📊 Example User Experiences

### Topic-Focused Student
```
User: "I'm weak in genetics, help me practice"
Bot: [Guides to JAMB Biology → Practice by Topic → Genetics]
Result: 25 genetics questions from multiple years (2015-2024)
```

### Year-Specific Student
```
User: "I want to practice JAMB 2023 biology"
Bot: [Guides to JAMB Biology → Practice by Year → 2023]
Result: 50 complete JAMB 2023 biology questions
```

### Comprehensive Student
```
User: "Give me mixed biology practice"
Bot: [Guides to JAMB Biology → Practice by Topic → Mixed Practice]
Result: 50 questions covering all biology topics from multiple years
```

### Performance-Focused Student
```
User: "Show my progress"
Bot: [Shows performance summary, strengths, weaknesses, and recommendations]
```

### Navigation & Recovery
```
User: "back"
Bot: [Returns to previous step, e.g., subject selection]

User: "stop"
Bot: [Pauses or ends the test, saves progress]
```

### LLM/AI Chat
```
User: "ask: What is the difference between mitosis and meiosis?"
Bot: [LLM-powered answer with up-to-date information]
```

## 🔧 Technical Architecture

### Flexible Question Fetching & Async Flows
- All exam types support both topic and year-based fetching.
- Questions are loaded asynchronously for instant delivery.
- Navigation and control commands are handled at every stage.

### Enhanced State & Analytics
- **EnhancedUserStateManager**: Tracks sessions, question-level performance, and analytics.
- **UserAnalytics**: Stores and analyzes user progress, strengths, weaknesses, and learning patterns.
- **Personalized Recommendations**: Generated after each session and available on demand.

### Hybrid LLM Integration
- **Groq (primary) + Gemini (fallback)**: Used for open-ended queries, help, and FAQ.
- **LLM triggers**: Users can explicitly ask for research or explanations at any time.

### Universal UX Pattern
All exams (JAMB, SAT, NEET) follow the same user experience:
1. **Select Exam** → 2. **Select Subject** → 3. **Choose Practice Mode** → 4. **Select Option** → 5. **Practice**

### Enhanced Performance Tracking
- **Topic-Level Performance**: Track performance in each topic
- **Year-Level Analysis**: See how you perform on questions from different years
- **Cross-Year Comparison**: Compare your performance across years
- **Weakness Identification**: AI identifies topics you struggle with
- **Progress Monitoring**: Track improvement over time

## 📈 Performance Reports

### Topic Performance
```
User: How am I doing in biology?
Bot: 📊 Your Biology Performance:

🎯 Topic Performance:
• Cell Biology: 85% (25 questions from 2020-2024)
• Genetics: 72% (20 questions from 2018-2023)
• Ecology: 90% (15 questions from 2019-2024)

📅 Year Performance:
• JAMB 2023: 78% (50 questions)
• JAMB 2022: 82% (30 questions)

💪 Recommendations:
• Focus more on Genetics concepts
• Practice more 2021-2022 questions
• Review Cell Biology fundamentals
```

## 🚀 Advanced Features

### Smart Question Selection
- **Topic Questions**: AI searches for questions specifically about chosen topics
- **Year Questions**: Complete question sets from specific years
- **Mixed Questions**: Balanced selection across all topics
- **Weak Area Questions**: Targeted questions for improvement areas

### Adaptive Feedback
- **Topic Context**: Shows which topic each question belongs to
- **Year Context**: Shows which year each question is from
- **Performance Insights**: Real-time feedback on progress
- **Study Recommendations**: Personalized suggestions based on performance

### Cross-Exam Consistency
- **Universal Flow**: Same user experience across JAMB, SAT, and NEET
- **Consistent Options**: Topics and years available for all exams
- **Standardized Feedback**: Same quality feedback across all exams

## 🎯 Future Enhancements

### Advanced Practice Modes
- **Difficulty Levels**: Easy, Medium, Hard questions within topics
- **Time-Based Practice**: Timed sessions for exam simulation
- **Custom Practice**: Mix topics and years in custom combinations

### Enhanced Analytics
- **Topic Mastery Tracking**: Track when you've mastered each topic
- **Year Pattern Analysis**: Understand how exam patterns change over years
- **Predictive Recommendations**: AI predicts which topics to study next

## 📞 Support

For issues or questions:
1. Ensure all API keys are configured in `.env`
2. Verify ngrok tunnel is active
3. Check server logs for errors
4. Test with simple commands like "start"

## 📄 License

This project is open source and available under the MIT License.

---

**Examinator** - Practice your way! Choose topics OR years with real past questions. 🎓📚