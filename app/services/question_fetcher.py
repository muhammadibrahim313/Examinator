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

class QuestionFetcher:
    """
    Service to fetch real past exam questions using LLM agent with web search capabilities
    """
    
    def __init__(self):
        self.agent = agent
        self.config = {"recursion_limit": 50}
        self.exam_structure = self._load_exam_structure()
    
    def _load_exam_structure(self) -> Dict[str, Any]:
        """Load exam structure configuration"""
        try:
            with open('app/data/exam_structure.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading exam structure: {e}")
            return {}
    
    async def fetch_questions(self, exam: str, subject: str, num_questions: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch real past exam questions using LLM agent with web search
        """
        try:
            exam_info = self.exam_structure.get(exam.lower(), {})
            subject_info = exam_info.get('subjects', {}).get(subject, {})
            available_years = subject_info.get('years_available', [])
            
            if not available_years:
                logger.warning(f"No years available for {exam} {subject}")
                return []
            
            # Select random years to get diverse questions
            selected_years = random.sample(available_years, min(3, len(available_years)))
            
            # Create comprehensive search query
            search_query = self._create_search_query(exam, subject, selected_years, num_questions)
            
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
            questions = self._parse_questions_from_response(full_response, exam, subject, selected_years)
            
            # Ensure we have the right number of questions
            if len(questions) < num_questions:
                # If we don't have enough, try to fetch more
                additional_questions = await self._fetch_additional_questions(
                    exam, subject, num_questions - len(questions), selected_years
                )
                questions.extend(additional_questions)
            
            # Shuffle and return the requested number
            random.shuffle(questions)
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error fetching questions for {exam} {subject}: {e}")
            return []
    
    def _create_search_query(self, exam: str, subject: str, years: List[str], num_questions: int) -> str:
        """
        Create a comprehensive search query for the LLM agent
        """
        exam_full_name = self.exam_structure.get(exam.lower(), {}).get('name', exam.upper())
        
        query = f"""
        I need you to find and provide {num_questions} real past exam questions for {exam_full_name} ({exam.upper()}) {subject} from the years {', '.join(years)}.

        IMPORTANT REQUIREMENTS:
        1. These must be REAL past questions from actual {exam.upper()} exams, not generated questions
        2. Each question should have exactly 4 options (A, B, C, D)
        3. Include the correct answer for each question
        4. Include the year reference for each question
        5. Provide detailed explanations for the correct answers
        6. Focus on the standard {exam.upper()} format and difficulty level

        Please search for official {exam.upper()} past questions for {subject} and provide them in this exact format:

        **Question 1 (Year: XXXX):**
        [Question text]
        A. [Option A]
        B. [Option B] 
        C. [Option C]
        D. [Option D]
        **Correct Answer:** [Letter]
        **Explanation:** [Detailed explanation]

        **Question 2 (Year: XXXX):**
        [Continue with same format...]

        Search for questions covering different topics within {subject} to ensure comprehensive coverage.
        Make sure all questions are appropriate for {exam.upper()} standard and difficulty level.
        """
        
        return query
    
    def _parse_questions_from_response(self, response: str, exam: str, subject: str, years: List[str]) -> List[Dict[str, Any]]:
        """
        Parse structured questions from the LLM response
        """
        questions = []
        
        try:
            # Split response into individual questions
            question_blocks = response.split('**Question')
            
            for i, block in enumerate(question_blocks[1:], 1):  # Skip first empty block
                try:
                    question_data = self._parse_single_question(block, i, exam, subject, years)
                    if question_data:
                        questions.append(question_data)
                except Exception as e:
                    logger.warning(f"Error parsing question {i}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(questions)} questions from response")
            return questions
            
        except Exception as e:
            logger.error(f"Error parsing questions from response: {e}")
            return []
    
    def _parse_single_question(self, block: str, question_id: int, exam: str, subject: str, years: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parse a single question block
        """
        try:
            lines = block.strip().split('\n')
            
            # Extract year from first line
            year = self._extract_year(lines[0], years)
            
            # Find question text (usually after the year line)
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
                "source": "past_questions",
                "difficulty": "standard"
            }
            
        except Exception as e:
            logger.error(f"Error parsing single question: {e}")
            return None
    
    def _extract_year(self, text: str, available_years: List[str]) -> str:
        """
        Extract year from text, fallback to random year if not found
        """
        for year in available_years:
            if year in text:
                return year
        
        # Fallback to random year
        return random.choice(available_years) if available_years else "2023"
    
    async def _fetch_additional_questions(self, exam: str, subject: str, needed: int, years: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch additional questions if the initial fetch didn't return enough
        """
        try:
            # Try with different years or more specific search
            additional_years = random.sample(years, min(2, len(years)))
            
            search_query = f"""
            I need {needed} more real {exam.upper()} {subject} past questions from years {', '.join(additional_years)}.
            
            Please provide them in the same format as before:
            **Question X (Year: XXXX):**
            [Question text]
            A. [Option A]
            B. [Option B]
            C. [Option C] 
            D. [Option D]
            **Correct Answer:** [Letter]
            **Explanation:** [Detailed explanation]
            
            Focus on different topics within {subject} that weren't covered in the previous questions.
            """
            
            agent_input = {"messages": [HumanMessage(content=search_query)]}
            
            response_chunks = []
            async for chunk in self.agent.astream(agent_input, config=self.config):
                if 'messages' in chunk:
                    for msg in chunk['messages']:
                        if hasattr(msg, 'content') and msg.content:
                            response_chunks.append(msg.content)
            
            full_response = '\n'.join(response_chunks) if response_chunks else ""
            additional_questions = self._parse_questions_from_response(full_response, exam, subject, additional_years)
            
            return additional_questions
            
        except Exception as e:
            logger.error(f"Error fetching additional questions: {e}")
            return []
    
    def get_exam_info(self, exam: str) -> Dict[str, Any]:
        """
        Get exam information including subjects and structure
        """
        return self.exam_structure.get(exam.lower(), {})
    
    def get_available_subjects(self, exam: str) -> List[str]:
        """
        Get available subjects for an exam
        """
        exam_info = self.exam_structure.get(exam.lower(), {})
        return list(exam_info.get('subjects', {}).keys())
    
    def get_questions_per_exam(self, exam: str, subject: str) -> int:
        """
        Get the standard number of questions for an exam subject
        """
        exam_info = self.exam_structure.get(exam.lower(), {})
        subject_info = exam_info.get('subjects', {}).get(subject, {})
        return subject_info.get('questions_per_exam', 50)