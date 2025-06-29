from typing import Dict, Any, List
from app.services.exam_types.base import BaseExamType
from app.services.topic_based_question_fetcher import TopicBasedQuestionFetcher
from app.services.question_fetcher import QuestionFetcher
import logging

logger = logging.getLogger(__name__)

class FlexibleJAMBExamType(BaseExamType):
    """
    Flexible JAMB exam type supporting both topic-based and year-based practice
    """
    
    def __init__(self):
        super().__init__("JAMB")
        self.topic_fetcher = TopicBasedQuestionFetcher()
        self.question_fetcher = QuestionFetcher()
    
    def get_flow_stages(self) -> List[str]:
        return ['selecting_subject', 'selecting_practice_mode', 'selecting_practice_option', 'taking_exam']
    
    def get_initial_stage(self) -> str:
        return 'selecting_subject'
    
    def handle_stage(self, stage: str, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JAMB stages with flexible practice options"""
        self.logger.info(f"Handling Flexible JAMB stage '{stage}' for {user_phone}")
        
        if stage == 'selecting_subject':
            return self._handle_subject_selection(user_phone, message, user_state)
        elif stage == 'selecting_practice_mode':
            return self._handle_practice_mode_selection(user_phone, message, user_state)
        elif stage == 'selecting_practice_option':
            return self._handle_practice_option_selection(user_phone, message, user_state)
        elif stage == 'taking_exam':
            return self._handle_answer(user_phone, message, user_state)
        else:
            return {
                'response': f"Unknown stage: {stage}. Please send 'restart' to start over.",
                'next_stage': 'selecting_subject',
                'state_updates': {'stage': 'selecting_subject'}
            }
    
    def validate_stage_input(self, stage: str, message: str, user_state: Dict[str, Any]) -> bool:
        if stage == 'selecting_subject':
            subjects = self.question_fetcher.get_available_subjects('jamb')
            return self.parse_choice(message, subjects) is not None
        elif stage == 'selecting_practice_mode':
            return self.parse_choice(message, ['Practice by Topic', 'Practice by Year']) is not None
        elif stage == 'selecting_practice_option':
            practice_mode = user_state.get('practice_mode')
            subject = user_state.get('subject')
            if practice_mode == 'topic' and subject:
                options = self.topic_fetcher.get_practice_options('jamb', subject)
                return self.parse_choice(message, options) is not None
            elif practice_mode == 'year' and subject:
                years = self._get_available_years('jamb', subject)
                return self.parse_choice(message, years) is not None
        elif stage == 'taking_exam':
            return message.strip().lower() in ['a', 'b', 'c', 'd']
        return False
    
    def get_available_options(self, stage: str, user_state: Dict[str, Any]) -> List[str]:
        if stage == 'selecting_subject':
            return self.question_fetcher.get_available_subjects('jamb')
        elif stage == 'selecting_practice_mode':
            return ['Practice by Topic', 'Practice by Year']
        elif stage == 'selecting_practice_option':
            practice_mode = user_state.get('practice_mode')
            subject = user_state.get('subject')
            if practice_mode == 'topic' and subject:
                return self.topic_fetcher.get_practice_options('jamb', subject)
            elif practice_mode == 'year' and subject:
                return self._get_available_years('jamb', subject)
        elif stage == 'taking_exam':
            return ['A', 'B', 'C', 'D']
        return []
    
    def _get_available_years(self, exam: str, subject: str) -> List[str]:
        """Get available years for an exam subject"""
        exam_info = self.question_fetcher.get_exam_info(exam)
        subject_info = exam_info.get('subjects', {}).get(subject, {})
        return subject_info.get('years_available', [])
    
    def _handle_subject_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subject selection for JAMB"""
        subjects = self.question_fetcher.get_available_subjects('jamb')
        
        if not subjects:
            return {
                'response': "Sorry, no subjects available for JAMB. Please contact support.",
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
        
        selected_subject = self.parse_choice(message, subjects)
        
        if selected_subject:
            self.logger.info(f"User {user_phone} selected JAMB subject: {selected_subject}")
            
            return {
                'response': f"✅ You selected: {selected_subject}\n\n🎯 How would you like to practice?\n\n1. Practice by Topic\n   📚 Focus on specific topics like 'Cell Biology' or 'Genetics'\n   🎯 Questions from multiple years on your chosen topic\n\n2. Practice by Year\n   📅 Practice questions from a specific year (2015-2024)\n   📊 Complete year coverage with all topics\n\nPlease reply with 1 or 2.",
                'next_stage': 'selecting_practice_mode',
                'state_updates': {
                    'subject': selected_subject,
                    'stage': 'selecting_practice_mode'
                }
            }
        else:
            return {
                'response': f"Invalid choice. Please select a number between 1 and {len(subjects)}.\n\n" + 
                           self.format_options_list(subjects, "Available JAMB subjects"),
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
    
    def _handle_practice_mode_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle practice mode selection (topic vs year)"""
        subject = user_state.get('subject')
        if not subject:
            return {
                'response': "Session error. Please send 'restart' to start over.",
                'next_stage': 'selecting_subject',
                'state_updates': {'stage': 'selecting_subject'}
            }
        
        modes = ['Practice by Topic', 'Practice by Year']
        selected_mode = self.parse_choice(message, modes)
        
        if selected_mode:
            practice_mode = 'topic' if '1' in message or 'topic' in selected_mode.lower() else 'year'
            self.logger.info(f"User {user_phone} selected practice mode: {practice_mode}")
            
            if practice_mode == 'topic':
                # Get topic options
                topic_options = self.topic_fetcher.get_practice_options('jamb', subject)
                response = f"✅ You selected: Practice by Topic\n\n📚 Choose a topic for {subject}:\n\n"
                response += self.format_options_list(topic_options, f"{subject} Topics")
                
            else:  # year mode
                # Get year options
                year_options = self._get_available_years('jamb', subject)
                response = f"✅ You selected: Practice by Year\n\n📅 Choose a year for {subject}:\n\n"
                response += self.format_options_list(year_options, f"Available Years")
            
            return {
                'response': response,
                'next_stage': 'selecting_practice_option',
                'state_updates': {
                    'practice_mode': practice_mode,
                    'stage': 'selecting_practice_option'
                }
            }
        else:
            return {
                'response': "Invalid choice. Please reply with 1 for Topic or 2 for Year.\n\n🎯 How would you like to practice?\n\n1. Practice by Topic\n2. Practice by Year",
                'next_stage': 'selecting_practice_mode',
                'state_updates': {}
            }
    
    def _handle_practice_option_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle specific topic or year selection"""
        subject = user_state.get('subject')
        practice_mode = user_state.get('practice_mode')
        
        if not subject or not practice_mode:
            return {
                'response': "Session error. Please send 'restart' to start over.",
                'next_stage': 'selecting_subject',
                'state_updates': {'stage': 'selecting_subject'}
            }
        
        if practice_mode == 'topic':
            # Handle topic selection
            topic_options = self.topic_fetcher.get_practice_options('jamb', subject)
            selected_option = self.parse_choice(message, topic_options)
            
            if selected_option:
                # Determine practice type and number of questions
                if selected_option == "Mixed Practice (All Topics)":
                    practice_type = "mixed"
                    num_questions = 50  # Full JAMB standard
                    description = f"Mixed practice covering all {subject} topics"
                elif selected_option == "Weak Areas Focus":
                    practice_type = "weak_areas"
                    num_questions = 30
                    description = f"Focus on your weak areas in {subject}"
                else:
                    # It's a specific topic
                    practice_type = "topic"
                    num_questions = 25
                    description = f"Practice questions on {selected_option}"
                
                return {
                    'response': f"✅ You selected: {selected_option}\n\n🔍 Fetching {num_questions} real JAMB past questions...\n📚 {description}\n⏱️ Questions from multiple years (2015-2024)\n\nThis may take a moment...",
                    'next_stage': 'loading_questions',
                    'state_updates': {
                        'practice_type': practice_type,
                        'selected_option': selected_option,
                        'questions_needed': num_questions,
                        'stage': 'loading_questions'
                    }
                }
            else:
                return {
                    'response': f"Invalid choice. Please select a number between 1 and {len(topic_options)}.\n\n" + 
                               self.format_options_list(topic_options, f"{subject} Topics"),
                    'next_stage': 'selecting_practice_option',
                    'state_updates': {}
                }
        
        else:  # year mode
            # Handle year selection
            year_options = self._get_available_years('jamb', subject)
            selected_year = self.parse_choice(message, year_options)
            
            if selected_year:
                num_questions = 50  # Standard JAMB questions per subject
                
                return {
                    'response': f"✅ You selected: {selected_year}\n\n🔍 Fetching {num_questions} real JAMB {selected_year} questions...\n📚 Complete {subject} practice from {selected_year}\n📊 Standard JAMB format\n\nThis may take a moment...",
                    'next_stage': 'loading_questions',
                    'state_updates': {
                        'practice_type': 'year',
                        'selected_option': selected_year,
                        'questions_needed': num_questions,
                        'stage': 'loading_questions'
                    }
                }
            else:
                return {
                    'response': f"Invalid choice. Please select a number between 1 and {len(year_options)}.\n\n" + 
                               self.format_options_list(year_options, "Available Years"),
                    'next_stage': 'selecting_practice_option',
                    'state_updates': {}
                }
    
    async def load_questions_async(self, user_phone: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Load questions based on practice type (topic or year)"""
        subject = user_state.get('subject')
        practice_mode = user_state.get('practice_mode')
        practice_type = user_state.get('practice_type')
        selected_option = user_state.get('selected_option')
        num_questions = user_state.get('questions_needed', 25)
        
        try:
            if practice_mode == 'topic':
                # Topic-based practice
                if practice_type == "topic":
                    questions = await self.topic_fetcher.fetch_questions_by_topic(
                        'jamb', subject, selected_option, num_questions
                    )
                    practice_description = f"Topic: {selected_option}"
                elif practice_type == "mixed":
                    questions = await self.topic_fetcher.fetch_mixed_practice_questions(
                        'jamb', subject, num_questions
                    )
                    practice_description = "Mixed Practice (All Topics)"
                elif practice_type == "weak_areas":
                    questions = await self.topic_fetcher.fetch_weak_areas_questions(
                        'jamb', subject, user_phone, num_questions
                    )
                    practice_description = "Weak Areas Focus"
                else:
                    questions = []
            
            else:  # year mode
                # Year-based practice
                questions = await self.question_fetcher.fetch_questions('jamb', subject, num_questions)
                # Filter or mark questions as being from the selected year
                practice_description = f"JAMB {selected_option} - Complete {subject}"
            
            if not questions:
                return {
                    'response': f"Sorry, could not fetch questions for {subject}. Please try again.",
                    'next_stage': 'selecting_practice_option',
                    'state_updates': {'stage': 'selecting_practice_option'}
                }
            
            # Format first question
            first_question = self._format_question(questions[0], 1, len(questions))
            intro = f"🎯 Starting JAMB {subject} Practice\n"
            intro += f"📚 {practice_description}\n"
            intro += f"📊 {len(questions)} real past questions\n"
            
            if practice_mode == 'topic':
                intro += f"⏱️ Questions from multiple years (2015-2024)\n\n"
            else:
                intro += f"📅 Questions from {selected_option}\n\n"
            
            return {
                'response': intro + first_question,
                'next_stage': 'taking_exam',
                'state_updates': {
                    'stage': 'taking_exam',
                    'questions': questions,
                    'total_questions': len(questions),
                    'current_question_index': 0,
                    'score': 0,
                    'practice_description': practice_description
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading questions: {e}")
            return {
                'response': f"Sorry, there was an error loading questions. Please try again.",
                'next_stage': 'selecting_practice_option',
                'state_updates': {'stage': 'selecting_practice_option'}
            }
    
    def _handle_answer(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle answer submission with flexible feedback"""
        questions = user_state.get('questions', [])
        current_index = user_state.get('current_question_index', 0)
        
        if not questions or current_index >= len(questions):
            return {
                'response': "Practice completed! Send 'start' to begin a new session.",
                'next_stage': 'completed',
                'state_updates': {'stage': 'completed'}
            }
        
        current_question = questions[current_index]
        user_answer = message.strip().lower()
        
        # Validate answer format
        if user_answer not in ['a', 'b', 'c', 'd']:
            return {
                'response': "Please reply with A, B, C, or D for your answer.\n\n" + 
                           self._format_question(current_question, current_index + 1, len(questions)),
                'next_stage': 'taking_exam',
                'state_updates': {}
            }
        
        # Check if answer is correct
        correct_answer = current_question.get('correct_answer', '').lower()
        is_correct = user_answer == correct_answer
        
        # Update score
        new_score = user_state.get('score', 0)
        if is_correct:
            new_score += 1
        
        # Move to next question
        next_index = current_index + 1
        
        # Prepare response with enhanced feedback
        year = current_question.get('year', 'Unknown')
        topic = current_question.get('topic', 'General')
        explanation = current_question.get('explanation', 'No explanation available.')
        practice_mode = user_state.get('practice_mode', 'topic')
        
        response = f"{'✅ Correct!' if is_correct else '❌ Wrong!'} The correct answer is {correct_answer.upper()}.\n\n"
        response += f"📅 Source: JAMB {year}\n"
        
        if practice_mode == 'topic':
            response += f"📚 Topic: {topic}\n"
        
        response += f"💡 {explanation}\n\n"
        response += f"📊 Progress: {new_score}/{next_index} correct ({(new_score/next_index)*100:.1f}%)\n\n"
        
        if next_index >= len(questions):
            # End of practice
            percentage = (new_score / len(questions)) * 100
            practice_description = user_state.get('practice_description', 'Practice')
            
            response += (f"🎉 JAMB {user_state.get('subject')} Practice Completed!\n\n"
                        f"📈 Final Score: {new_score}/{len(questions)} ({percentage:.1f}%)\n"
                        f"📚 {practice_description}\n\n")
            
            # Performance feedback
            if percentage >= 80:
                response += "🌟 Excellent! You're well prepared for JAMB.\n"
            elif percentage >= 60:
                response += "👍 Good work! Keep practicing to improve.\n"
            else:
                response += "💪 Keep studying. Focus on understanding the concepts.\n"
            
            response += "\nSend 'start' to practice another topic, year, or subject."
            
            return {
                'response': response,
                'next_stage': 'completed',
                'state_updates': {
                    'score': new_score,
                    'stage': 'completed',
                    'final_percentage': percentage
                }
            }
        else:
            # Continue with next question
            next_question = questions[next_index]
            response += self._format_question(next_question, next_index + 1, len(questions))
            
            return {
                'response': response,
                'next_stage': 'taking_exam',
                'state_updates': {
                    'current_question_index': next_index,
                    'score': new_score
                }
            }
    
    def _format_question(self, question: Dict[str, Any], question_num: int, total_questions: int) -> str:
        """Format a question with appropriate context"""
        question_text = question.get('question', 'No question text available')
        options = question.get('options', {})
        year = question.get('year', 'Unknown')
        topic = question.get('topic')
        
        # Format header based on available information
        if topic:
            formatted = f"Question {question_num}/{total_questions} (JAMB {year} - {topic}):\n{question_text}\n\n"
        else:
            formatted = f"Question {question_num}/{total_questions} (JAMB {year}):\n{question_text}\n\n"
        
        # Add options in order
        for key in ['A', 'B', 'C', 'D']:
            if key in options:
                formatted += f"{key}. {options[key]}\n"
        
        formatted += "\nReply with A, B, C, or D"
        
        return formatted