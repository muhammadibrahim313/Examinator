import os
import json
import random
import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage
from app.agent_reflection.RAG_reflection import agent
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TopicBasedQuestionFetcher:
    """
    Service to fetch real past exam questions based on topics from multiple years
    """
    
    def __init__(self):
        self.agent = agent
        self.config = {"recursion_limit": 50}
        self.exam_structure = self._load_exam_structure()
        self.topic_structure = self._load_topic_structure()
    
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
                "Mathematics": {"topics": ["Algebra", "Geometry", "Calculus"]}
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
    
    async def fetch_questions_by_topic(self, exam: str, subject: str, topic: str, num_questions: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch real past exam questions for a specific topic from multiple years
        """
        logger.info(f"🔍 TOPIC QUESTION FETCH START: {exam.upper()} {subject} - {topic} - requesting {num_questions} questions")
        
        try:
            exam_info = self.exam_structure.get(exam.lower(), {})
            subject_info = exam_info.get('subjects', {}).get(subject, {})
            available_years = subject_info.get('years_available', ["2023", "2024"])
            
            # Use multiple years for diverse questions
            selected_years = random.sample(available_years, min(3, len(available_years)))
            logger.info(f"📅 Selected years for topic search: {selected_years}")
            
            # Create topic-specific search query
            search_query = self._create_topic_search_query(exam, subject, topic, selected_years, num_questions)
            logger.info(f"🔍 Starting LLM agent search for {exam.upper()} {subject} - {topic} questions")
            
            # Use LLM agent to search and extract questions
            agent_input = {"messages": [HumanMessage(content=search_query)]}
            
            response_chunks = []
            async for chunk in self.agent.astream(agent_input, config=self.config):
                if 'messages' in chunk:
                    for msg in chunk['messages']:
                        if hasattr(msg, 'content') and msg.content:
                            response_chunks.append(msg.content)
            
            full_response = '\n'.join(response_chunks) if response_chunks else ""
            logger.info(f"📝 LLM agent response length: {len(full_response)} characters")
            
            if not full_response.strip():
                logger.error(f"❌ LLM AGENT FAILED: Empty response for {exam.upper()} {subject} - {topic}")
                logger.info(f"🔄 USING FALLBACK: Generating {num_questions} fallback questions for topic")
                return self._generate_fallback_topic_questions(exam, subject, topic, num_questions)
            
            # Parse the response to extract structured questions
            questions = self._parse_questions_from_response(full_response, exam, subject, topic, selected_years)
            logger.info(f"✅ PARSED QUESTIONS: {len(questions)} topic questions extracted from LLM response")
            
            # If we don't have enough questions, generate fallback
            if len(questions) < num_questions // 2:
                logger.warning(f"⚠️  INSUFFICIENT TOPIC QUESTIONS: Only got {len(questions)}/{num_questions} questions from LLM")
                logger.info(f"🔄 USING FALLBACK: Generating {num_questions - len(questions)} additional fallback questions for topic")
                fallback_questions = self._generate_fallback_topic_questions(exam, subject, topic, num_questions - len(questions))
                questions.extend(fallback_questions)
                logger.info(f"📊 FINAL TOPIC MIX: {len(questions)} total questions ({len(questions) - len(fallback_questions)} LLM + {len(fallback_questions)} fallback)")
            else:
                logger.info(f"✅ SUCCESS: Using {len(questions)} LLM-generated topic questions (no fallback needed)")
            
            # Shuffle and return the requested number
            random.shuffle(questions)
            final_questions = questions[:num_questions]
            logger.info(f"🎯 TOPIC QUESTION FETCH COMPLETE: Returning {len(final_questions)} questions for {exam.upper()} {subject} - {topic}")
            return final_questions
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in topic question fetching for {exam.upper()} {subject} - {topic}: {str(e)}", exc_info=True)
            logger.info(f"🔄 EMERGENCY FALLBACK: Generating {num_questions} fallback questions due to error")
            return self._generate_fallback_topic_questions(exam, subject, topic, num_questions)
    
    def _generate_fallback_topic_questions(self, exam: str, subject: str, topic: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate fallback questions for a specific topic"""
        logger.info(f"🔧 GENERATING TOPIC FALLBACK: Creating {num_questions} fallback questions for {exam.upper()} {subject} - {topic}")
        
        questions = []
        
        for i in range(min(num_questions, 5)):  # Generate up to 5 fallback questions
            questions.append({
                "id": i + 1,
                "question": f"Sample {exam.upper()} {subject} question about {topic}. This tests your understanding of {topic} concepts.",
                "options": {
                    "A": f"Option A related to {topic}",
                    "B": f"Option B related to {topic}",
                    "C": f"Option C related to {topic}",
                    "D": f"Option D related to {topic}"
                },
                "correct_answer": random.choice(["A", "B", "C", "D"]),
                "explanation": f"This is a sample explanation for {topic} in {subject}.",
                "year": "2023",
                "exam": exam.upper(),
                "subject": subject,
                "topic": topic,
                "source": "fallback",
                "difficulty": "standard"
            })
        
        logger.info(f"✅ TOPIC FALLBACK COMPLETE: Generated {len(questions)} fallback questions for {topic}")
        return questions
    
    async def fetch_mixed_practice_questions(self, exam: str, subject: str, num_questions: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch mixed questions from all topics for comprehensive practice
        """
        logger.info(f"🔍 MIXED PRACTICE FETCH START: {exam.upper()} {subject} - requesting {num_questions} mixed questions")
        
        try:
            topics = self.get_available_topics(exam, subject)
            if not topics:
                logger.warning(f"⚠️  No topics available for {exam} {subject} - using fallback")
                return self._generate_fallback_topic_questions(exam, subject, "Mixed Topics", num_questions)
            
            # Distribute questions across topics
            questions_per_topic = max(2, num_questions // len(topics))
            all_questions = []
            
            logger.info(f"📊 Fetching mixed questions from {len(topics)} topics, {questions_per_topic} per topic")
            
            # Get questions from each topic
            for i, topic in enumerate(topics[:min(5, len(topics))]):  # Limit to 5 topics max
                logger.info(f"🔍 Fetching questions for topic {i+1}/{min(5, len(topics))}: {topic}")
                topic_questions = await self.fetch_questions_by_topic(
                    exam, subject, topic, questions_per_topic
                )
                all_questions.extend(topic_questions)
                logger.info(f"✅ Got {len(topic_questions)} questions for {topic}")
            
            # Shuffle and return requested number
            random.shuffle(all_questions)
            final_questions = all_questions[:num_questions]
            logger.info(f"🎯 MIXED PRACTICE COMPLETE: Returning {len(final_questions)} mixed questions from {len(topics)} topics")
            return final_questions
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in mixed practice fetching: {str(e)}", exc_info=True)
            logger.info(f"🔄 EMERGENCY FALLBACK: Generating {num_questions} fallback questions for mixed practice")
            return self._generate_fallback_topic_questions(exam, subject, "Mixed Topics", num_questions)
    
    async def fetch_weak_areas_questions(self, exam: str, subject: str, user_phone: str, num_questions: int = 25) -> List[Dict[str, Any]]:
        """
        Fetch questions focusing on user's weak areas
        """
        logger.info(f"🔍 WEAK AREAS FETCH START: {exam.upper()} {subject} for user {user_phone} - requesting {num_questions} questions")
        
        try:
            # Get user's weak topics (this would integrate with analytics)
            # For now, we'll select random topics as placeholder
            topics = self.get_available_topics(exam, subject)
            weak_topics = random.sample(topics, min(3, len(topics)))
            logger.info(f"🎯 Selected weak areas: {weak_topics}")
            
            all_questions = []
            questions_per_topic = num_questions // len(weak_topics)
            
            for topic in weak_topics:
                logger.info(f"🔍 Fetching weak area questions for: {topic}")
                topic_questions = await self.fetch_questions_by_topic(
                    exam, subject, topic, questions_per_topic
                )
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
    
    def _create_topic_search_query(self, exam: str, subject: str, topic: str, years: List[str], num_questions: int) -> str:
        """
        Create a topic-specific search query for the LLM agent
        """
        exam_full_name = self.exam_structure.get(exam.lower(), {}).get('name', exam.upper())
        
        query = f"""
        I need you to find and provide {num_questions} real past exam questions specifically about "{topic}" for {exam_full_name} ({exam.upper()}) {subject} from multiple years ({', '.join(years)}).

        CRITICAL REQUIREMENTS:
        1. Questions must be REAL past questions from actual {exam.upper()} exams
        2. ALL questions must be specifically about "{topic}" - no other topics
        3. Each question must have exactly 4 options (A, B, C, D)
        4. Include the correct answer and year reference for each question
        5. Provide detailed explanations focusing on {topic} concepts
        6. Questions should come from different years to show variety

        TOPIC FOCUS: "{topic}"
        - Only include questions that directly test knowledge of {topic}
        - Ensure questions cover different aspects of {topic}
        - Questions should be at {exam.upper()} standard difficulty level

        Please search for official {exam.upper()} past questions about {topic} in {subject} and provide them in this exact format:

        **Question 1 (Year: XXXX - Topic: {topic}):**
        [Question text specifically about {topic}]
        A. [Option A]
        B. [Option B] 
        C. [Option C]
        D. [Option D]
        **Correct Answer:** [Letter]
        **Explanation:** [Detailed explanation focusing on {topic} concepts]

        **Question 2 (Year: XXXX - Topic: {topic}):**
        [Continue with same format...]

        Remember: ALL questions must be about "{topic}" specifically. Do not include questions from other topics.
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