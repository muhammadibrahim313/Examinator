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
            with open('app/data/exam_structure.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading exam structure: {e}")
            return {}
    
    def _load_topic_structure(self) -> Dict[str, Any]:
        """Load topic structure configuration"""
        try:
            with open('app/data/topic_structure.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading topic structure: {e}")
            return {}
    
    def get_available_topics(self, exam: str, subject: str) -> List[str]:
        """Get available topics for an exam subject"""
        exam_topics = self.topic_structure.get(exam.lower(), {})
        subject_topics = exam_topics.get(subject, {})
        return subject_topics.get('topics', [])
    
    def get_practice_options(self, exam: str, subject: str) -> List[str]:
        """Get practice options: topics + mixed practice"""
        topics = self.get_available_topics(exam, subject)
        options = topics.copy()
        options.append("Mixed Practice (All Topics)")
        options.append("Weak Areas Focus")
        return options
    
    async def fetch_questions_by_topic(self, exam: str, subject: str, topic: str, num_questions: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch real past exam questions for a specific topic from multiple years
        """
        try:
            exam_info = self.exam_structure.get(exam.lower(), {})
            subject_info = exam_info.get('subjects', {}).get(subject, {})
            available_years = subject_info.get('years_available', [])
            
            if not available_years:
                logger.warning(f"No years available for {exam} {subject}")
                return []
            
            # Use multiple years for diverse questions
            selected_years = random.sample(available_years, min(4, len(available_years)))
            
            # Create topic-specific search query
            search_query = self._create_topic_search_query(exam, subject, topic, selected_years, num_questions)
            
            # Use LLM agent to search and extract questions
            agent_input = {"messages": [HumanMessage(content=search_query)]}
            
            response_chunks = []
            async for chunk in self.agent.astream(agent_input, config=self.config):
                if 'messages' in chunk:
                    for msg in chunk['messages']:
                        if hasattr(msg, 'content') and msg.content:
                            response_chunks.append(msg.content)
            
            full_response = '\n'.join(response_chunks) if response_chunks else ""
            
            # Parse the response to extract structured questions
            questions = self._parse_questions_from_response(full_response, exam, subject, topic, selected_years)
            
            # Ensure we have enough questions
            if len(questions) < num_questions:
                additional_questions = await self._fetch_additional_topic_questions(
                    exam, subject, topic, num_questions - len(questions), selected_years
                )
                questions.extend(additional_questions)
            
            # Shuffle and return the requested number
            random.shuffle(questions)
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error fetching questions for {exam} {subject} - {topic}: {e}")
            return []
    
    async def fetch_mixed_practice_questions(self, exam: str, subject: str, num_questions: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch mixed questions from all topics for comprehensive practice
        """
        try:
            topics = self.get_available_topics(exam, subject)
            if not topics:
                return []
            
            # Distribute questions across topics
            questions_per_topic = max(2, num_questions // len(topics))
            all_questions = []
            
            # Get questions from each topic
            for topic in topics[:min(10, len(topics))]:  # Limit to 10 topics max
                topic_questions = await self.fetch_questions_by_topic(
                    exam, subject, topic, questions_per_topic
                )
                all_questions.extend(topic_questions)
            
            # Shuffle and return requested number
            random.shuffle(all_questions)
            return all_questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error fetching mixed practice questions: {e}")
            return []
    
    async def fetch_weak_areas_questions(self, exam: str, subject: str, user_phone: str, num_questions: int = 25) -> List[Dict[str, Any]]:
        """
        Fetch questions focusing on user's weak areas
        """
        try:
            # Get user's weak topics (this would integrate with analytics)
            # For now, we'll select random topics as placeholder
            topics = self.get_available_topics(exam, subject)
            weak_topics = random.sample(topics, min(3, len(topics)))
            
            all_questions = []
            questions_per_topic = num_questions // len(weak_topics)
            
            for topic in weak_topics:
                topic_questions = await self.fetch_questions_by_topic(
                    exam, subject, topic, questions_per_topic
                )
                all_questions.extend(topic_questions)
            
            random.shuffle(all_questions)
            return all_questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error fetching weak areas questions: {e}")
            return []
    
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
        questions = []
        
        try:
            # Split response into individual questions
            question_blocks = response.split('**Question')
            
            for i, block in enumerate(question_blocks[1:], 1):  # Skip first empty block
                try:
                    question_data = self._parse_single_topic_question(block, i, exam, subject, topic, years)
                    if question_data:
                        questions.append(question_data)
                except Exception as e:
                    logger.warning(f"Error parsing question {i}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(questions)} questions for topic: {topic}")
            return questions
            
        except Exception as e:
            logger.error(f"Error parsing questions from response: {e}")
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
                logger.warning(f"Incomplete question data for question {question_id}")
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
            logger.error(f"Error parsing single topic question: {e}")
            return None
    
    def _extract_year(self, text: str, available_years: List[str]) -> str:
        """Extract year from text, fallback to random year if not found"""
        for year in available_years:
            if year in text:
                return year
        return random.choice(available_years) if available_years else "2023"
    
    async def _fetch_additional_topic_questions(self, exam: str, subject: str, topic: str, needed: int, years: List[str]) -> List[Dict[str, Any]]:
        """Fetch additional questions for a specific topic"""
        try:
            search_query = f"""
            I need {needed} more real {exam.upper()} {subject} past questions specifically about "{topic}" from years {', '.join(years)}.
            
            IMPORTANT: All questions must be about "{topic}" only.
            
            Please provide them in the same format:
            **Question X (Year: XXXX - Topic: {topic}):**
            [Question text about {topic}]
            A. [Option A]
            B. [Option B]
            C. [Option C] 
            D. [Option D]
            **Correct Answer:** [Letter]
            **Explanation:** [Detailed explanation about {topic}]
            
            Focus on different aspects of {topic} that weren't covered in previous questions.
            """
            
            agent_input = {"messages": [HumanMessage(content=search_query)]}
            
            response_chunks = []
            async for chunk in self.agent.astream(agent_input, config=self.config):
                if 'messages' in chunk:
                    for msg in chunk['messages']:
                        if hasattr(msg, 'content') and msg.content:
                            response_chunks.append(msg.content)
            
            full_response = '\n'.join(response_chunks) if response_chunks else ""
            additional_questions = self._parse_questions_from_response(full_response, exam, subject, topic, years)
            
            return additional_questions
            
        except Exception as e:
            logger.error(f"Error fetching additional topic questions: {e}")
            return []