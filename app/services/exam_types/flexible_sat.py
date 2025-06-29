from typing import Dict, Any, List
from app.services.exam_types.base import BaseExamType
from app.services.topic_based_question_fetcher import TopicBasedQuestionFetcher
from app.services.question_fetcher import QuestionFetcher
import logging

logger = logging.getLogger(__name__)

class FlexibleSATExamType(BaseExamType):
    """
    SAT exam type - TOPIC-BASED PRACTICE ONLY (SAT doesn't have yearly versions like JAMB/NEET)
    """
    
    def __init__(self):
        super().__init__("SAT")
        self.topic_fetcher = TopicBasedQuestionFetcher()
        self.question_fetcher = QuestionFetcher()
    
    def get_flow_stages(self) -> List[str]:
        # SAT only supports topic-based practice, no year selection
        return ['selecting_subject', 'selecting_practice_option', 'taking_exam']
    
    def get_initial_stage(self) -> str:
        return 'selecting_subject'
    
    def handle_stage(self, stage: str, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SAT stages - topic-based practice only"""
        self.logger.info(f"Handling SAT stage '{stage}' for {user_phone}")
        
        if stage == 'selecting_subject':
            return self._handle_subject_selection(user_phone, message, user_state)
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
            subjects = self.question_fetcher.get_available_subjects('sat')
            return self.parse_choice(message, subjects) is not None
        elif stage == 'selecting_practice_option':
            subject = user_state.get('subject')
            if subject:
                options = self.topic_fetcher.get_practice_options('sat', subject)
                return self.parse_choice(message, options) is not None
        elif stage == 'taking_exam':
            return message.strip().lower() in ['a', 'b', 'c', 'd']
        return False
    
    def get_available_options(self, stage: str, user_state: Dict[str, Any]) -> List[str]:
        if stage == 'selecting_subject':
            return self.question_fetcher.get_available_subjects('sat')
        elif stage == 'selecting_practice_option':
            subject = user_state.get('subject')
            if subject:
                return self.topic_fetcher.get_practice_options('sat', subject)
        elif stage == 'taking_exam':
            return ['A', 'B', 'C', 'D']
        return []
    
    def _handle_subject_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subject selection for SAT"""
        subjects = self.question_fetcher.get_available_subjects('sat')
        
        if not subjects:
            return {
                'response': "Sorry, no subjects available for SAT. Please contact support.",
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
        
        selected_subject = self.parse_choice(message, subjects)
        
        if selected_subject:
            self.logger.info(f"User {user_phone} selected SAT subject: {selected_subject}")
            
            # Get topic options for SAT (no year selection for SAT)
            topic_options = self.topic_fetcher.get_practice_options('sat', selected_subject)
            
            response = f"✅ You selected: {selected_subject}\n\n"
            response += f"📚 Choose your practice type for {selected_subject}:\n\n"
            response += self.format_options_list(topic_options, f"{selected_subject} Practice Types")
            
            return {
                'response': response,
                'next_stage': 'selecting_practice_option',
                'state_updates': {
                    'subject': selected_subject,
                    'stage': 'selecting_practice_option'
                }
            }
        else:
            return {
                'response': f"Invalid choice. Please select a number between 1 and {len(subjects)}.\n\n" + 
                           self.format_options_list(subjects, "Available SAT subjects"),
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
    
    def _handle_practice_option_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle practice option selection for SAT (topic-based only) - FIXED: No more empty responses"""
        subject = user_state.get('subject')
        if not subject:
            return {
                'response': "Session error. Please send 'restart' to start over.",
                'next_stage': 'selecting_subject',
                'state_updates': {'stage': 'selecting_subject'}
            }
        
        # Get topic options
        topic_options = self.topic_fetcher.get_practice_options('sat', subject)
        selected_option = self.parse_choice(message, topic_options)
        
        if selected_option:
            # Determine practice type and number of questions
            if selected_option == "Mixed Practice (All Topics)":
                practice_type = "mixed"
                num_questions = self.question_fetcher.get_questions_per_exam('sat', subject)
            elif selected_option == "Weak Areas Focus":
                practice_type = "weak_areas"
                num_questions = 30
            else:
                # It's a specific topic
                practice_type = "topic"
                num_questions = 25
            
            # FIXED: Return proper loading message instead of empty response
            loading_message = f"✅ You selected: {selected_option}\n\n"
            loading_message += f"🔄 Loading {num_questions} SAT {subject} questions...\n"
            loading_message += f"📚 {selected_option}\n"
            loading_message += f"⏱️ This may take a moment..."
            
            return {
                'response': loading_message,
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
                           self.format_options_list(topic_options, f"{subject} Practice Types"),
                'next_stage': 'selecting_practice_option',
                'state_updates': {}
            }
    
    async def load_questions_async(self, user_phone: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Load questions based on practice type (topic-based only for SAT)"""
        subject = user_state.get('subject')
        practice_type = user_state.get('practice_type')
        selected_option = user_state.get('selected_option')
        num_questions = user_state.get('questions_needed', 25)
        
        try:
            # Topic-based practice only for SAT
            if practice_type == "topic":
                questions = await self.topic_fetcher.fetch_questions_by_topic(
                    'sat', subject, selected_option, num_questions
                )
                practice_description = f"Topic: {selected_option}"
            elif practice_type == "mixed":
                questions = await self.topic_fetcher.fetch_mixed_practice_questions(
                    'sat', subject, num_questions
                )
                practice_description = "Mixed Practice (All Topics)"
            elif practice_type == "weak_areas":
                questions = await self.topic_fetcher.fetch_weak_areas_questions(
                    'sat', subject, user_phone, num_questions
                )
                practice_description = "Weak Areas Focus"
            else:
                questions = []
            
            if not questions:
                return {
                    'response': f"Sorry, could not fetch questions for {subject}. Please try again.",
                    'next_stage': 'selecting_practice_option',
                    'state_updates': {'stage': 'selecting_practice_option'}
                }
            
            # Format first question - FIXED: Remove the fetching message from here
            first_question = self._format_question(questions[0], 1, len(questions))
            
            # FIXED: Clean intro without the fetching message
            intro = f"🎯 Starting SAT {subject} Practice\n"
            intro += f"📚 {practice_description}\n"
            intro += f"📊 {len(questions)} practice questions\n"
            intro += f"⏱️ Standard SAT format\n\n"
            
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
            logger.error(f"Error loading SAT questions: {e}")
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
        
        if user_answer not in ['a', 'b', 'c', 'd']:
            return {
                'response': "Please reply with A, B, C, or D for your answer.\n\n" + 
                           self._format_question(current_question, current_index + 1, len(questions)),
                'next_stage': 'taking_exam',
                'state_updates': {}
            }
        
        correct_answer = current_question.get('correct_answer', '').lower()
        is_correct = user_answer == correct_answer
        new_score = user_state.get('score', 0) + (1 if is_correct else 0)
        next_index = current_index + 1
        
        year = current_question.get('year', 'Practice')
        topic = current_question.get('topic', 'General')
        explanation = current_question.get('explanation', 'No explanation available.')
        
        response = f"{'✅ Correct!' if is_correct else '❌ Wrong!'} Answer: {correct_answer.upper()}\n\n"
        response += f"📚 Topic: {topic}\n"
        response += f"💡 {explanation}\n\n"
        
        if next_index >= len(questions):
            percentage = (new_score / len(questions)) * 100
            practice_description = user_state.get('practice_description', 'Practice')
            
            response += f"🎉 SAT {user_state.get('subject')} Complete!\n"
            response += f"📈 Score: {new_score}/{len(questions)} ({percentage:.1f}%)\n"
            response += f"📚 {practice_description}\n\n"
            response += "Send 'start' to practice another topic or subject."
            
            return {
                'response': response,
                'next_stage': 'completed',
                'state_updates': {'score': new_score, 'stage': 'completed'}
            }
        else:
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
        topic = question.get('topic')
        
        if topic and topic != "General":
            formatted = f"Question {question_num}/{total_questions} (SAT - {topic}):\n{question_text}\n\n"
        else:
            formatted = f"Question {question_num}/{total_questions} (SAT):\n{question_text}\n\n"
        
        for key in ['A', 'B', 'C', 'D']:
            if key in options:
                formatted += f"{key}. {options[key]}\n"
        
        formatted += "\nReply with A, B, C, or D"
        return formatted