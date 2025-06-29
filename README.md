# Examinator - Topic-Based WhatsApp Exam Practice Bot

A revolutionary WhatsApp chatbot that helps students practice for computer-based exams using **real past questions** organized by **topics**. Students can practice specific topics or get mixed questions from multiple years without having to select specific years.

## 🎯 Key Features

### Topic-Based Practice System
- **Practice by Topic**: Choose specific topics like "Cell Biology" or "Algebra"
- **Mixed Practice**: Get questions from all topics in a subject
- **Weak Areas Focus**: AI identifies and focuses on your weak areas
- **Multi-Year Questions**: Questions automatically sourced from multiple years (2015-2024)
- **No Year Selection Required**: Students focus on topics, not years

### Real Past Questions
- **Authentic Questions**: Real past questions from official exam bodies
- **Multiple Years**: Questions automatically sourced from 2015-2024
- **Topic References**: Each question shows its topic and source year
- **Standard Format**: Proper exam format with correct number of questions

### Supported Exams & Subjects

#### JAMB (Joint Admissions and Matriculation Board)
**All 12 subjects with topic-based practice:**
- **Mathematics**: Algebra, Geometry, Trigonometry, Calculus, Statistics, etc.
- **English Language**: Comprehension, Grammar, Vocabulary, Writing Skills, etc.
- **Biology**: Cell Biology, Genetics, Evolution, Ecology, Physiology, etc.
- **Chemistry**: Atomic Structure, Chemical Bonding, Organic Chemistry, etc.
- **Physics**: Mechanics, Electricity, Waves, Thermodynamics, etc.
- **Geography**: Physical Geography, Human Geography, Map Reading, etc.
- **Economics**: Basic Concepts, Market Structure, National Income, etc.
- **Government**: Political Theory, Constitutional Development, etc.
- **Literature**: Poetry, Prose, Drama, Literary Devices, etc.
- **History**: Nigerian History, African History, World History, etc.
- **Agricultural Science**: Crop Production, Animal Production, Soil Science, etc.
- **Computer Studies**: Fundamentals, Programming, Networks, etc.

#### SAT & NEET
- Similar topic-based structure for all subjects

## 🚀 How Topic-Based Practice Works

### 1. **Choose Subject, Then Practice Type**
```
User: start
Bot: Choose exam: 1. JAMB 2. SAT 3. NEET

User: 1
Bot: Choose subject: 1. Mathematics 2. Biology 3. Chemistry...

User: 2 (Biology)
Bot: 📚 Choose your practice type:

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

Please reply with the number of your choice.
```

### 2. **Topic-Specific Practice**
```
User: 1 (Cell Biology)
Bot: ✅ You selected: Cell Biology and Organization

🔍 Fetching 20 real JAMB past questions...
📚 Practice questions on Cell Biology and Organization
⏱️ Questions from multiple years (2015-2024)

🎯 Starting JAMB Biology Practice
📚 Topic: Cell Biology and Organization
📊 20 real past questions from multiple years

Question 1/20 (JAMB 2023 - Cell Biology):
Which organelle is known as the powerhouse of the cell?
A. Nucleus
B. Ribosome
C. Mitochondria
D. Endoplasmic reticulum

Reply with A, B, C, or D
```

### 3. **Mixed Practice**
```
User: 11 (Mixed Practice)
Bot: ✅ You selected: Mixed Practice (All Topics)

🔍 Fetching 30 real JAMB past questions...
📚 Mixed practice covering all Biology topics
⏱️ Questions from multiple years (2015-2024)

[Questions from various topics: Cell Biology, Genetics, Ecology, etc.]
```

### 4. **Weak Areas Focus**
```
User: 12 (Weak Areas Focus)
Bot: ✅ You selected: Weak Areas Focus

🔍 Fetching 25 real JAMB past questions...
📚 Focus on your weak areas in Biology
⏱️ Questions from multiple years

[AI selects questions from topics where user has struggled]
```

## 🎯 Benefits of Topic-Based Practice

### For Students
- **Targeted Learning**: Focus on specific topics you need to improve
- **Flexible Practice**: No need to choose specific years
- **Comprehensive Coverage**: Questions from multiple years ensure variety
- **Weakness Identification**: AI tracks which topics you struggle with
- **Efficient Study**: Practice exactly what you need

### For Exam Preparation
- **Real Questions**: Authentic past questions maintain exam authenticity
- **Topic Mastery**: Master one topic at a time or practice everything
- **Performance Tracking**: See your progress in each topic
- **Adaptive Learning**: System focuses on your weak areas

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

## 📊 Example User Experience

### Topic Selection Flow
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

📚 Choose your practice type:
1. Cell Biology and Organization
2. Genetics and Heredity
3. Evolution and Ecology
[... all Biology topics]
11. Mixed Practice (All Topics)
12. Weak Areas Focus
```

### Practice Session
```
User: 2 (Genetics)
Bot: 🎯 Starting JAMB Biology Practice
     📚 Topic: Genetics and Heredity
     📊 20 real past questions from multiple years

     Question 1/20 (JAMB 2022 - Genetics):
     What is the basic unit of heredity?
     A. Chromosome
     B. Gene
     C. DNA
     D. RNA

User: B
Bot: ✅ Correct! The correct answer is B.

     📅 Source: JAMB 2022
     📚 Topic: Genetics and Heredity
     💡 A gene is the basic unit of heredity that carries genetic information...
     
     📊 Progress: 1/1 correct (100.0%)

     Question 2/20 (JAMB 2019 - Genetics):
     [Next genetics question...]
```

## 🔧 Technical Architecture

### Topic-Based Question Fetching
```python
# app/services/topic_based_question_fetcher.py
class TopicBasedQuestionFetcher:
    async def fetch_questions_by_topic(self, exam: str, subject: str, topic: str, num_questions: int):
        # Fetches real questions for specific topic from multiple years
        # Uses AI to search and extract authentic past questions
        # Returns structured questions with topic and year references
```

### Enhanced Exam Flow
```python
# app/services/exam_types/topic_based_jamb.py
class TopicBasedJAMBExamType:
    def get_flow_stages(self) -> List[str]:
        return ['selecting_subject', 'selecting_practice_type', 'taking_exam']
    
    # Handles topic selection and question fetching
```

### Topic Structure
```json
// app/data/topic_structure.json
{
  "jamb": {
    "Biology": {
      "topics": [
        "Cell Biology and Organization",
        "Genetics and Heredity",
        "Evolution and Ecology",
        // ... all Biology topics
      ]
    }
  }
}
```

## 📈 Performance Tracking

### Enhanced Analytics
- **Topic-Level Performance**: Track performance in each topic
- **Multi-Year Analysis**: See how you perform on questions from different years
- **Weakness Identification**: AI identifies topics you struggle with
- **Progress Monitoring**: Track improvement over time

### Performance Reports
```
User: How am I doing?
Bot: 📊 Your Performance Summary:

🎯 Topic Performance:
• Cell Biology: 85% (20 questions answered)
• Genetics: 72% (15 questions answered)
• Ecology: 90% (10 questions answered)

📚 Recent Practice:
• JAMB Biology - Genetics: 80% (from multiple years)
• JAMB Chemistry - Bonding: 65% (needs improvement)

💪 Recommendations:
• Focus more on Genetics concepts
• Practice Chemical Bonding questions
• Review Cell Biology fundamentals
```

## 🚀 Future Enhancements

### Advanced Topic Features
- **Subtopic Breakdown**: Further divide topics into subtopics
- **Difficulty Levels**: Easy, Medium, Hard questions within topics
- **Topic Dependencies**: Understand prerequisite topics
- **Mastery Tracking**: Track when you've mastered a topic

### Smart Recommendations
- **Study Path**: AI suggests optimal topic sequence
- **Time Allocation**: Recommend time to spend on each topic
- **Review Schedule**: Spaced repetition for topic review

## 📞 Support

For issues or questions:
1. Ensure all API keys are configured in `.env`
2. Verify ngrok tunnel is active
3. Check server logs for errors
4. Test with simple commands like "start"

## 📄 License

This project is open source and available under the MIT License.

---

**Examinator** - Master topics, not years! Practice with real past questions organized by topics. 🎓📚