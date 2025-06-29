from typing import Dict, Any, List
from app.services.exam_types.base import BaseExamType
from app.services.topic_based_question_fetcher import TopicBasedQuestionFetcher
import logging

logger = logging.getLogger(__name__)

class TopicBasedJAMBExamType(BaseExamType):
    """
    Topic-based JAMB exam type with questions from multiple years
    """
    
    def __init__(self):
        super().__init__("JAMB")
        self.question_fetcher = TopicBasedQuestionFetcher()
    
    def get_flow_stages(self) -> List[str]:
        return ['selecting_subject', 'selecting_practice_type', 'taking_exam']
    
    def get_initial_stage(self) -> str:
        return 'selecting_subject'
    
    def handle_stage(self, stage: str, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JAMB stages with topic-based practice"""
        self.logger.info(f"Handling Topic-Based JAMB stage '{stage}' for {user_phone}")
        
        if stage == 'selecting_subject':
            return self._handle_subject_selection(user_phone, message, user_state)
        elif stage == 'selecting_practice_type':
            return self._handle_practice_type_selection(user_phone, message, user_state)
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
        elif stage == 'selecting_practice_type':
            subject = user_state.get('subject')
            if subject:
                options = self.question_fetcher.get_practice_options('jamb', subject)
                return self.parse_choice(message, options) is not None
        elif stage == 'taking_exam':
            return message.strip().lower() in ['a', 'b', 'c', 'd']
        return False
    
    def get_available_options(self, stage: str, user_state: Dict[str, Any]) -> List[str]:
        if stage == 'selecting_subject':
            return self.question_fetcher.get_available_subjects('jamb')
        elif stage == 'selecting_practice_type':
            subject = user_state.get('subject')
            if subject:
                return self.question_fetcher.get_practice_options('jamb', subject)
        elif stage == 'taking_exam':
            return ['A', 'B', 'C', 'D']
        return []
    
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
            
            # Get practice options for this subject
            practice_options = self.question_fetcher.get_practice_options('jamb', selected_subject)
            
            return {
                'response': f"✅ You selected: {selected_subject}\n\n📚 Choose your practice type:\n\n" + 
                           self.format_options_list(practice_options, "Practice Options"),
                'next_stage': 'selecting_practice_type',
                'state_updates': {
                    'subject': selected_subject,
                    'stage': 'selecting_practice_type'
                }
            }
        else:
            return {
                'response': f"Invalid choice. Please select a number between 1 and {len(subjects)}.\n\n" + 
                           self.format_options_list(subjects, "Available JAMB subjects"),
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
    
    def _handle_practice_type_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle practice type selection (topic, mixed, weak areas)"""
        subject = user_state.get('subject')
        if not subject:
            return {
                'response': "Session error. Please send 'restart' to start over.",
                'next_stage': 'selecting_subject',
                'state_updates': {'stage': 'selecting_subject'}
            }
        
        practice_options = self.question_fetcher.get_practice_options('jamb', subject)
        selected_option = self.parse_choice(message, practice_options)
        
        if selected_option:
            self.logger.info(f"User {user_phone} selected practice type: {selected_option}")
            
            # Determine practice type and number of questions
            if selected_option == "Mixed Practice (All Topics)":
                practice_type = "mixed"
                num_questions = 30
                description = f"Mixed practice covering all {subject} topics"
            elif selected_option == "Weak Areas Focus":
                practice_type = "weak_areas"
                num_questions = 25
                description = f"Focus on your weak areas in {subject}"
            else:
                # It's a specific topic
                practice_type = "topic"
                num_questions = 20
                description = f"Practice questions on {selected_option}"
            
            return {
                'response': f"✅ You selected: {selected_option}\n\n🔍 Fetching {num_questions} real JAMB past questions...\n📚 {description}\n⏱️ Questions from multiple years (2015-2024)\n\nThis may take a moment...",
                'next_stage': 'loading_questions',
                'state_updates': {
                    'practice_type': practice_type,
                    'selected_topic': selected_option if practice_type == "topic" else None,
                    'questions_needed': num_questions,
                    'stage': 'loading_questions'
                }
            }
        else:
            return {
                'response': f"Invalid choice. Please select a number between 1 and {len(practice_options)}.\n\n" + 
                           self.format_options_list(practice_options, "Practice Options"),
                'next_stage': 'selecting_practice_type',
                'state_updates': {}
            }
    
    async def load_questions_async(self, user_phone: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Load questions based on practice type"""
        subject = user_state.get('subject')
        practice_type = user_state.get('practice_type')
        selected_topic = user_state.get('selected_topic')
        num_questions = user_state.get('questions_needed', 20)
        
        try:
            # Fetch questions based on practice type
            if practice_type == "topic":
                questions = await self.question_fetcher.fetch_questions_by_topic(
                    'jamb', subject, selected_topic, num_questions
                )
                practice_description = f"Topic: {selected_topic}"
            elif practice_type == "mixed":
                questions = await self.question_fetcher.fetch_mixed_practice_questions(
                    'jamb', subject, num_questions
                )
                practice_description = "Mixed Practice (All Topics)"
            elif practice_type == "weak_areas":
                questions = await self.question_fetcher.fetch_weak_areas_questions(
                    'jamb', subject, user_phone, num_questions
                )
                practice_description = "Weak Areas Focus"
            else:
                questions = []
            
            if not questions:
                return {
                    'response': f"Sorry, could not fetch questions for {subject}. Please try again.",
                    'next_stage': 'selecting_practice_type',
                    'state_updates': {'stage': 'selecting_practice_type'}
                }
            
            # Format first question
            first_question = self._format_question(questions[0], 1, len(questions))
            intro = f"🎯 Starting JAMB {subject} Practice\n"
            intro += f"📚 {practice_description}\n"
            intro += f"📊 {len(questions)} real past questions from multiple years\n"
            intro += f"⏱️ Standard JAMB format\n\n"
            
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
                'next_stage': 'selecting_practice_type',
                'state_updates': {'stage': 'selecting_practice_type'}
            }
    
    def _handle_answer(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle answer submission with topic information"""
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
        
        response = f"{'✅ Correct!' if is_correct else '❌ Wrong!'} The correct answer is {correct_answer.upper()}.\n\n"
        response += f"📅 Source: JAMB {year}\n"
        response += f"📚 Topic: {topic}\n"
        response += f"💡 {explanation}\n\n"
        response += f"📊 Progress: {new_score}/{next_index} correct ({(new_score/next_index)*100:.1f}%)\n\n"
        
        if next_index >= len(questions):
            # End of practice
            percentage = (new_score / len(questions)) * 100
            practice_description = user_state.get('practice_description', 'Practice')
            
            response += (f"🎉 JAMB {user_state.get('subject')} Practice Completed!\n\n"
                        f"📈 Final Score: {new_score}/{len(questions)} ({percentage:.1f}%)\n"
                        f"📚 {practice_description}\n"
                        f"🗓️ Questions from multiple years\n\n")
            
            # Performance feedback
            if percentage >= 80:
                response += "🌟 Excellent! You've mastered this area.\n"
            elif percentage >= 60:
                response += "👍 Good work! Keep practicing to improve.\n"
            else:
                response += "💪 Keep studying. Focus on understanding the concepts.\n"
            
            response += "\nSend 'start' to practice another topic or subject."
            
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
        """Format a question with topic and year information"""
        question_text = question.get('question', 'No question text available')
        options = question.get('options', {})
        year = question.get('year', 'Unknown')
        topic = question.get('topic', 'General')
        
        formatted = f"Question {question_num}/{total_questions} (JAMB {year} - {topic}):\n{question_text}\n\n"
        
        # Add options in order
        for key in ['A', 'B', 'C', 'D']:
            if key in options:
                formatted += f"{key}. {options[key]}\n"
        
        formatted += "\nReply with A, B, C, or D"
        
        return formatted