import os
import json
import random
import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage
from app.agent_reflection.RAG_reflection import agent, hybrid_manager
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TopicBasedQuestionFetcher:
    """
    Service to fetch real past exam questions based on topics from multiple years
    OPTIMIZED VERSION - Reduced API calls for quota management
    """
    
    def __init__(self):
        self.agent = agent
        # OPTIMIZATION: Reduced recursion limit to save API calls
        self.config = {"recursion_limit": 10}  # Reduced from 50 to 10
        self.exam_structure = self._load_exam_structure()
        self.topic_structure = self._load_topic_structure()
        # OPTIMIZATION: Track API usage to prevent quota exhaustion
        self.api_call_count = 0
        self.max_daily_calls = 40  # Leave buffer for other operations
    
    def _load_exam_structure(self) -> Dict[str, Any]:
        """Load exam structure configuration"""
        try:
            # Try multiple possible paths
            possible_paths = [
                'app/data/exam_structure.json',
                './app/data/exam_structure.json',
                '/opt/render/project/src/app/data/exam_structure.json'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        logger.info(f"Successfully loaded exam structure from {path}")
                        return data
            
            logger.warning("No exam structure file found, using default")
            return self._get_default_exam_structure()
            
        except Exception as e:
            logger.error(f"Error loading exam structure: {e}")
            return self._get_default_exam_structure()
    
    def _load_topic_structure(self) -> Dict[str, Any]:
        """Load topic structure configuration"""
        try:
            # Try multiple possible paths
            possible_paths = [
                'app/data/topic_structure.json',
                './app/data/topic_structure.json',
                '/opt/render/project/src/app/data/topic_structure.json'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        logger.info(f"Successfully loaded topic structure from {path}")
                        return data
            
            logger.warning("No topic structure file found, using default")
            return self._get_default_topic_structure()
            
        except Exception as e:
            logger.error(f"Error loading topic structure: {e}")
            return self._get_default_topic_structure()
    
    def _get_default_exam_structure(self) -> Dict[str, Any]:
        """Return default exam structure"""
        return {
            "jamb": {"name": "JAMB", "subjects": {"Biology": {"questions_per_exam": 50, "years_available": ["2023", "2024"]}}},
            "sat": {"name": "SAT", "subjects": {"Math": {"questions_per_exam": 58, "years_available": ["2023", "2024"]}}},
            "neet": {"name": "NEET", "subjects": {"Biology": {"questions_per_exam": 50, "years_available": ["2023", "2024"]}}}
        }
    
    def _get_default_topic_structure(self) -> Dict[str, Any]:
        """Return default topic structure"""
        return {
            "jamb": {
                "Biology": {"topics": ["Cell Biology", "Genetics", "Ecology", "Evolution"]},
                "Chemistry": {"topics": ["Atomic Structure", "Chemical Bonding", "Acids and Bases"]},
                "Physics": {"topics": ["Mechanics", "Electricity", "Waves"]},
                "Mathematics": {"topics": ["Algebra and Equations", "Geometry and Mensuration", "Trigonometry", "Calculus and Differentiation", "Statistics and Probability", "Number Theory", "Coordinate Geometry", "Sequences and Series", "Logarithms and Indices", "Mathematical Logic"]}
            },
            "sat": {
                "Math": {"topics": ["Algebra", "Geometry", "Statistics"]},
                "Reading and Writing": {"topics": ["Reading Comprehension", "Grammar", "Vocabulary"]}
            },
            "neet": {
                "Biology": {"topics": ["Cell Biology", "Genetics", "Ecology"]},
                "Chemistry": {"topics": ["Organic Chemistry", "Inorganic Chemistry"]},
                "Physics": {"topics": ["Mechanics", "Thermodynamics", "Optics"]}
            }
        }
    
    def get_available_topics(self, exam: str, subject: str) -> List[str]:
        """Get available topics for an exam subject"""
        exam_topics = self.topic_structure.get(exam.lower(), {})
        subject_topics = exam_topics.get(subject, {})
        topics = subject_topics.get('topics', [])
        logger.info(f"Available topics for {exam} {subject}: {topics}")
        return topics
    
    def get_practice_options(self, exam: str, subject: str) -> List[str]:
        """Get practice options: topics + mixed practice"""
        topics = self.get_available_topics(exam, subject)
        options = topics.copy()
        options.append("Mixed Practice (All Topics)")
        options.append("Weak Areas Focus")
        logger.info(f"Practice options for {exam} {subject}: {len(options)} options")
        return options

    def _should_use_llm(self) -> bool:
        """Check if we should use LLM or fallback immediately"""
        if self.api_call_count >= self.max_daily_calls:
            logger.warning(f"⚠️ API QUOTA PROTECTION: {self.api_call_count}/{self.max_daily_calls} calls used, using fallback")
            return False
        return True

    async def fetch_questions_by_topic(self, exam: str, subject: str, topic: str, num_questions: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch real past exam questions for a specific topic - HYBRID MODEL VERSION
        """
        logger.info(f"🔍 TOPIC QUESTION FETCH START: {exam.upper()} {subject} - {topic} - requesting {num_questions} questions")
        
        # Get hybrid model stats before operation
        stats_before = hybrid_manager.get_stats()
        logger.info(f"🤖 HYBRID MODEL STATUS: Total calls={stats_before['total_calls']}, Groq={stats_before['groq_calls']}, Gemini={stats_before['gemini_calls']}")
        
        # OPTIMIZATION: Check API quota before making calls
        if not self._should_use_llm():
            logger.info(f"🔄 QUOTA PROTECTION: Using fallback questions immediately")
            return self._generate_fallback_topic_questions(exam, subject, topic, num_questions)
        
        try:
            exam_info = self.exam_structure.get(exam.lower(), {})
            subject_info = exam_info.get('subjects', {}).get(subject, {})
            available_years = subject_info.get('years_available', ["2023", "2024"])
            
            # OPTIMIZATION: Use fewer years to reduce search complexity
            selected_years = random.sample(available_years, min(2, len(available_years)))  # Reduced from 3 to 2
            logger.info(f"📅 Selected years for topic search: {selected_years}")
            
            # OPTIMIZATION: Request fewer questions from LLM, generate more fallback
            llm_questions_to_request = min(10, num_questions // 2)  # Request max 10 from LLM
            logger.info(f"🔍 LLM REQUEST: Asking for {llm_questions_to_request} questions, will generate {num_questions - llm_questions_to_request} fallback")
            
            # Create shorter, more efficient search query
            search_query = self._create_efficient_topic_search_query(exam, subject, topic, selected_years, llm_questions_to_request)
            logger.info(f"🔍 Starting OPTIMIZED LLM agent search for {exam.upper()} {subject} - {topic} questions")
            
            # Track API usage
            self.api_call_count += 1
            
            # Use LLM agent to search and extract questions
            agent_input = {"messages": [HumanMessage(content=search_query)]}
            
            response_chunks = []
            try:
                async for chunk in self.agent.astream(agent_input, config=self.config):
                    logger.debug(f"📦 RAG Chunk keys: {list(chunk.keys())}")
                    if 'messages' in chunk:
                        for msg in chunk['messages']:
                            logger.debug(f"📨 Message type: {type(msg)}, has content: {hasattr(msg, 'content')}")
                            if hasattr(msg, 'content') and msg.content:
                                logger.debug(f"✅ Found content: {msg.content[:100]}...")
                                response_chunks.append(msg.content)
                            elif hasattr(msg, 'content'):
                                logger.debug(f"⚠️ Empty content: '{msg.content}'")
                    
                    # Also check for other possible response formats
                    if 'agent' in chunk and 'messages' in chunk['agent']:
                        for msg in chunk['agent']['messages']:
                            if hasattr(msg, 'content') and msg.content:
                                logger.debug(f"✅ Found agent content: {msg.content[:100]}...")
                                response_chunks.append(msg.content)
                                
            except Exception as e:
                logger.error(f"❌ LLM AGENT ERROR: {str(e)}")
                # Immediate fallback on any error
                logger.info(f"🔄 IMMEDIATE FALLBACK: Using fallback questions due to LLM error")
                return self._generate_fallback_topic_questions(exam, subject, topic, num_questions)
            
            full_response = '\n'.join(response_chunks) if response_chunks else ""
            logger.info(f"📝 LLM agent response: {len(response_chunks)} chunks collected")
            logger.info(f"📝 LLM agent response length: {len(full_response)} characters")
            
            if response_chunks:
                logger.info(f"📝 First chunk preview: {response_chunks[0][:200]}...")
            else:
                logger.warning(f"⚠️ No response chunks collected from agent")
            
            if not full_response.strip():
                logger.error(f"❌ LLM AGENT FAILED: Empty response for {exam.upper()} {subject} - {topic}")
                logger.info(f"🔄 USING FALLBACK: Generating {num_questions} fallback questions for topic")
                return self._generate_fallback_topic_questions(exam, subject, topic, num_questions)
            
            # Parse the response to extract structured questions
            questions = self._parse_questions_from_response(full_response, exam, subject, topic, selected_years)
            logger.info(f"✅ PARSED QUESTIONS: {len(questions)} topic questions extracted from LLM response")
            
            # OPTIMIZATION: Always use significant fallback to reduce LLM dependency
            fallback_needed = max(0, num_questions - len(questions))
            if fallback_needed > 0:
                logger.info(f"🔄 GENERATING FALLBACK: Adding {fallback_needed} fallback questions")
                fallback_questions = self._generate_fallback_topic_questions(exam, subject, topic, fallback_needed)
                questions.extend(fallback_questions)
                logger.info(f"📊 FINAL TOPIC MIX: {len(questions)} total questions ({len(questions) - len(fallback_questions)} LLM + {len(fallback_questions)} fallback)")
            
            # Shuffle and return the requested number
            random.shuffle(questions)
            final_questions = questions[:num_questions]
            
            # Report hybrid model usage statistics
            stats_after = hybrid_manager.get_stats()
            groq_used = stats_after['groq_calls'] - stats_before['groq_calls']
            gemini_used = stats_after['gemini_calls'] - stats_before['gemini_calls']
            
            if groq_used > 0:
                logger.info(f"🚀 HYBRID RESULT: Used Groq for {groq_used} calls (fast & efficient)")
            if gemini_used > 0:
                logger.info(f"🔧 HYBRID RESULT: Used Gemini for {gemini_used} calls (reliable fallback)")
            
            logger.info(f"🎯 TOPIC QUESTION FETCH COMPLETE: Returning {len(final_questions)} questions for {exam.upper()} {subject} - {topic}")
            return final_questions
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in topic question fetching for {exam.upper()} {subject} - {topic}: {str(e)}", exc_info=True)
            logger.info(f"🔄 EMERGENCY FALLBACK: Generating {num_questions} fallback questions due to error")
            return self._generate_fallback_topic_questions(exam, subject, topic, num_questions)
    
    def _generate_fallback_topic_questions(self, exam: str, subject: str, topic: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate realistic, high-quality fallback questions for specific topics"""
        logger.info(f"🔧 GENERATING REALISTIC FALLBACK: Creating {num_questions} quality questions for {exam.upper()} {subject} - {topic}")
        
        questions = []
        
        # Topic-specific question banks with realistic questions
        question_banks = self._get_topic_question_bank(exam.lower(), subject, topic)
        
        # Generate the requested number of questions
        for i in range(num_questions):
            # Select a random question from the bank, cycling if needed
            bank_index = i % len(question_banks)
            base_question = question_banks[bank_index].copy()
            
            # Randomize numerical values if it's a math question
            if subject.lower() in ['mathematics', 'math'] and any(char.isdigit() for char in base_question['question']):
                base_question = self._randomize_numerical_values(base_question)
            
            # Add metadata
            base_question.update({
                "id": i + 1,
                "year": random.choice(["2020", "2021", "2022", "2023", "2024"]),
                "exam": exam.upper(),
                "subject": subject,
                "topic": topic,
                "source": "curated_fallback",
                "difficulty": "standard"
            })
            
            questions.append(base_question)
        
        logger.info(f"✅ REALISTIC FALLBACK COMPLETE: Generated {len(questions)} quality questions for {topic}")
        return questions

    def _get_topic_question_bank(self, exam: str, subject: str, topic: str) -> List[Dict[str, Any]]:
        """Get realistic question bank for specific topics"""
        
        # JAMB Mathematics - Algebra and Equations
        if exam == 'jamb' and subject.lower() == 'mathematics' and 'algebra' in topic.lower():
            return [
                {
                    "question": "Solve for x: 3x + 7 = 22",
                    "options": {
                        "A": "x = 3",
                        "B": "x = 5", 
                        "C": "x = 7",
                        "D": "x = 9"
                    },
                    "correct_answer": "B",
                    "explanation": "3x + 7 = 22, so 3x = 15, therefore x = 5"
                },
                {
                    "question": "If 2x - 5 = 11, what is the value of x?",
                    "options": {
                        "A": "6",
                        "B": "7",
                        "C": "8", 
                        "D": "9"
                    },
                    "correct_answer": "C",
                    "explanation": "2x - 5 = 11, so 2x = 16, therefore x = 8"
                },
                {
                    "question": "Factorize: x² - 9",
                    "options": {
                        "A": "(x - 3)(x + 3)",
                        "B": "(x - 9)(x + 1)", 
                        "C": "(x - 1)(x + 9)",
                        "D": "x(x - 9)"
                    },
                    "correct_answer": "A",
                    "explanation": "x² - 9 is a difference of squares: x² - 3² = (x - 3)(x + 3)"
                },
                {
                    "question": "If y = 2x + 3, find y when x = 4",
                    "options": {
                        "A": "9",
                        "B": "10",
                        "C": "11",
                        "D": "12"
                    },
                    "correct_answer": "C",
                    "explanation": "y = 2(4) + 3 = 8 + 3 = 11"
                },
                {
                    "question": "Solve: 4x - 8 = 2x + 6",
                    "options": {
                        "A": "x = 5",
                        "B": "x = 6",
                        "C": "x = 7",
                        "D": "x = 8"
                    },
                    "correct_answer": "C",
                    "explanation": "4x - 2x = 6 + 8, so 2x = 14, therefore x = 7"
                }
            ]
        
        # JAMB Mathematics - Geometry and Mensuration
        elif exam == 'jamb' and subject.lower() == 'mathematics' and 'geometry' in topic.lower():
            return [
                {
                    "question": "Calculate the area of a circle with radius 7cm (Take π = 22/7)",
                    "options": {
                        "A": "154 cm²",
                        "B": "144 cm²",
                        "C": "164 cm²", 
                        "D": "174 cm²"
                    },
                    "correct_answer": "A",
                    "explanation": "Area = πr² = (22/7) × 7² = (22/7) × 49 = 154 cm²"
                },
                {
                    "question": "Find the perimeter of a rectangle with length 12cm and width 8cm",
                    "options": {
                        "A": "40 cm",
                        "B": "20 cm",
                        "C": "32 cm",
                        "D": "96 cm"
                    },
                    "correct_answer": "A",
                    "explanation": "Perimeter = 2(l + w) = 2(12 + 8) = 2(20) = 40 cm"
                }
            ]
        
        # Default questions for other topics
        else:
            return [
                {
                    "question": f"Which fundamental principle is most important in {topic}?",
                    "options": {
                        "A": "Understanding the basic concepts and definitions",
                        "B": "Memorizing formulas without understanding",
                        "C": "Skipping practice problems",
                        "D": "Avoiding difficult questions"
                    },
                    "correct_answer": "A",
                    "explanation": f"In {topic}, understanding basic concepts is crucial for solving complex problems effectively."
                },
                {
                    "question": f"What is the best approach when studying {topic}?",
                    "options": {
                        "A": "Start with examples and work backwards to theory",
                        "B": "Practice regularly and understand each step",
                        "C": "Focus only on memorization",
                        "D": "Study only the night before exams"
                    },
                    "correct_answer": "B",
                    "explanation": f"Regular practice with understanding is the most effective way to master {topic}."
                }
            ]

    def _randomize_numerical_values(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Randomize numerical values in math questions to create variations"""
        # This is a simple implementation - can be expanded for more sophisticated randomization
        return question  # For now, return as-is to avoid breaking existing questions

    async def fetch_mixed_practice_questions(self, exam: str, subject: str, num_questions: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch mixed practice questions from multiple topics - OPTIMIZED VERSION
        """
        logger.info(f"🔍 MIXED PRACTICE FETCH START: {exam.upper()} {subject} - requesting {num_questions} questions")
        
        try:
            topics = self.get_available_topics(exam, subject)
            if not topics:
                logger.warning(f"⚠️ No topics found for {exam} {subject}, using fallback")
                return self._generate_fallback_topic_questions(exam, subject, "Mixed Topics", num_questions)
            
            # OPTIMIZATION: Limit to fewer topics to reduce API calls
            selected_topics = random.sample(topics, min(3, len(topics)))  # Reduced from 5 to 3
            questions_per_topic = max(1, num_questions // len(selected_topics))
            logger.info(f"📊 MIXED PRACTICE PLAN: {len(selected_topics)} topics, {questions_per_topic} questions each")
            
            all_questions = []
            
            # OPTIMIZATION: Use more fallback, less LLM
            for i, topic in enumerate(selected_topics):
                logger.info(f"🔍 Fetching questions for topic {i+1}/{len(selected_topics)}: {topic}")
                
                # OPTIMIZATION: Use 50% LLM, 50% fallback for mixed practice
                if i < len(selected_topics) // 2 and self._should_use_llm():
                    topic_questions = await self.fetch_questions_by_topic(
                        exam, subject, topic, questions_per_topic
                    )
                else:
                    logger.info(f"🔄 Using fallback for topic {topic} to save API calls")
                    topic_questions = self._generate_fallback_topic_questions(exam, subject, topic, questions_per_topic)
                
                all_questions.extend(topic_questions)
                logger.info(f"✅ Got {len(topic_questions)} questions for {topic}")
            
            # Shuffle and return requested number
            random.shuffle(all_questions)
            final_questions = all_questions[:num_questions]
            logger.info(f"🎯 MIXED PRACTICE COMPLETE: Returning {len(final_questions)} mixed questions from {len(selected_topics)} topics")
            return final_questions
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in mixed practice fetching: {str(e)}", exc_info=True)
            logger.info(f"🔄 EMERGENCY FALLBACK: Generating {num_questions} fallback questions for mixed practice")
            return self._generate_fallback_topic_questions(exam, subject, "Mixed Topics", num_questions)
    
    async def fetch_weak_areas_questions(self, exam: str, subject: str, user_phone: str, num_questions: int = 25) -> List[Dict[str, Any]]:
        """
        Fetch questions focusing on user's weak areas - OPTIMIZED VERSION
        """
        logger.info(f"🔍 WEAK AREAS FETCH START: {exam.upper()} {subject} for user {user_phone} - requesting {num_questions} questions")
        
        try:
            # Get user's weak topics (this would integrate with analytics)
            # For now, we'll select random topics as placeholder
            topics = self.get_available_topics(exam, subject)
            weak_topics = random.sample(topics, min(2, len(topics)))  # Reduced from 3 to 2
            logger.info(f"🎯 Selected weak areas: {weak_topics}")
            
            all_questions = []
            questions_per_topic = num_questions // len(weak_topics)
            
            # OPTIMIZATION: Use mostly fallback for weak areas to save API calls
            for i, topic in enumerate(weak_topics):
                logger.info(f"🔍 Fetching weak area questions for: {topic}")
                
                # Use LLM for only first topic, fallback for rest
                if i == 0 and self._should_use_llm():
                    topic_questions = await self.fetch_questions_by_topic(
                        exam, subject, topic, questions_per_topic
                    )
                else:
                    logger.info(f"🔄 Using fallback for weak area {topic} to save API calls")
                    topic_questions = self._generate_fallback_topic_questions(exam, subject, topic, questions_per_topic)
                
                all_questions.extend(topic_questions)
                logger.info(f"✅ Got {len(topic_questions)} questions for weak area: {topic}")
            
            random.shuffle(all_questions)
            final_questions = all_questions[:num_questions]
            logger.info(f"🎯 WEAK AREAS COMPLETE: Returning {len(final_questions)} questions targeting weak areas")
            return final_questions
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in weak areas fetching: {str(e)}", exc_info=True)
            logger.info(f"🔄 EMERGENCY FALLBACK: Generating {num_questions} fallback questions for weak areas")
            return self._generate_fallback_topic_questions(exam, subject, "Weak Areas", num_questions)
    
    def _create_efficient_topic_search_query(self, exam: str, subject: str, topic: str, years: List[str], num_questions: int) -> str:
        """
        Create a shorter, more efficient topic-specific search query - OPTIMIZED VERSION
        """
        exam_full_name = self.exam_structure.get(exam.lower(), {}).get('name', exam.upper())
        
        # OPTIMIZATION: Much shorter query to reduce token usage
        query = f"""
        Find {num_questions} real {exam.upper()} {subject} questions about "{topic}" from {', '.join(years)}.

        Requirements:
        - Real past {exam.upper()} questions only
        - Topic: "{topic}" specifically  
        - Format: Question, A/B/C/D options, correct answer, brief explanation
        - Include year reference

        Example format:
        **Question 1 (Year: 2023):**
        [Question about {topic}]
        A. [Option A]
        B. [Option B] 
        C. [Option C]
        D. [Option D]
        **Correct Answer:** A
        **Explanation:** [Brief explanation]

        Focus only on {topic}. Provide {num_questions} questions in this format.
        """
        
        return query
    
    def _parse_questions_from_response(self, response: str, exam: str, subject: str, topic: str, years: List[str]) -> List[Dict[str, Any]]:
        """
        Parse structured questions from the LLM response with topic information
        """
        logger.info(f"🔍 PARSING TOPIC RESPONSE: Extracting questions from LLM response for {exam.upper()} {subject} - {topic}")
        
        questions = []
        
        try:
            # Split response into individual questions
            question_blocks = response.split('**Question')
            logger.info(f"📊 Found {len(question_blocks) - 1} potential question blocks in topic response")
            
            for i, block in enumerate(question_blocks[1:], 1):  # Skip first empty block
                try:
                    question_data = self._parse_single_topic_question(block, i, exam, subject, topic, years)
                    if question_data:
                        questions.append(question_data)
                        logger.debug(f"✅ Successfully parsed topic question {i}")
                    else:
                        logger.warning(f"⚠️  Failed to parse topic question {i} - incomplete data")
                except Exception as e:
                    logger.warning(f"❌ Error parsing topic question {i}: {str(e)}")
                    continue
            
            logger.info(f"✅ TOPIC PARSING COMPLETE: Successfully parsed {len(questions)} valid topic questions from response")
            return questions
            
        except Exception as e:
            logger.error(f"❌ TOPIC PARSING FAILED: Error parsing questions from response: {str(e)}")
            return []
    
    def _parse_single_topic_question(self, block: str, question_id: int, exam: str, subject: str, topic: str, years: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parse a single question block with topic information
        """
        try:
            lines = block.strip().split('\n')
            
            # Extract year from first line
            year = self._extract_year(lines[0], years)
            
            # Find question text
            question_text = ""
            options = {}
            correct_answer = ""
            explanation = ""
            
            current_section = "question"
            
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('A.'):
                    current_section = "options"
                    options['A'] = line[2:].strip()
                elif line.startswith('B.'):
                    options['B'] = line[2:].strip()
                elif line.startswith('C.'):
                    options['C'] = line[2:].strip()
                elif line.startswith('D.'):
                    options['D'] = line[2:].strip()
                elif '**Correct Answer:**' in line:
                    current_section = "answer"
                    correct_answer = line.split('**Correct Answer:**')[1].strip()
                elif '**Explanation:**' in line:
                    current_section = "explanation"
                    explanation = line.split('**Explanation:**')[1].strip()
                elif current_section == "question" and not line.startswith('**'):
                    question_text += " " + line
                elif current_section == "explanation":
                    explanation += " " + line
            
            # Validate required fields
            if not question_text or len(options) != 4 or not correct_answer:
                logger.debug(f"❌ Topic question {question_id} validation failed: text={bool(question_text)}, options={len(options)}, answer={bool(correct_answer)}")
                return None
            
            return {
                "id": question_id,
                "question": question_text.strip(),
                "options": options,
                "correct_answer": correct_answer.upper(),
                "explanation": explanation.strip() if explanation else "No explanation provided.",
                "year": year,
                "exam": exam.upper(),
                "subject": subject,
                "topic": topic,
                "source": "past_questions",
                "difficulty": "standard"
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing single topic question {question_id}: {str(e)}")
            return None
    
    def _extract_year(self, text: str, available_years: List[str]) -> str:
        """Extract year from text, fallback to random year if not found"""
        for year in available_years:
            if year in text:
                return year
        return random.choice(available_years) if available_years else "2023"