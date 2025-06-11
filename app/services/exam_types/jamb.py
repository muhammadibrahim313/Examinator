from typing import Dict, Any, List
from app.services.exam_types.base import BaseExamType
from app.utils.helpers import get_available_subjects, get_available_years, load_exam_data
import random

class JAMBExamType(BaseExamType):
    """
    JAMB exam type implementation
    Flow: selecting_subject -> selecting_year -> taking_exam
    """
    
    def __init__(self):
        super().__init__("JAMB")
    
    def get_flow_stages(self) -> List[str]:
        return ['selecting_subject', 'selecting_year', 'taking_exam']
    
    def get_initial_stage(self) -> str:
        return 'selecting_subject'
    
    def handle_stage(self, stage: str, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle JAMB-specific stages
        """
        if stage == 'selecting_subject':
            return self._handle_subject_selection(user_phone, message, user_state)
        elif stage == 'selecting_year':
            return self._handle_year_selection(user_phone, message, user_state)
        elif stage == 'taking_exam':
            return self._handle_answer(user_phone, message, user_state)
        else:
            return {
                'response': f"Unknown stage: {stage}. Please send 'restart' to start over.",
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
    
    def validate_stage_input(self, stage: str, message: str, user_state: Dict[str, Any]) -> bool:
        """
        Validate input for JAMB stages
        """
        if stage == 'selecting_subject':
            subjects = get_available_subjects('jamb')
            return self.parse_choice(message, subjects) is not None
        elif stage == 'selecting_year':
            subject = user_state.get('subject')
            if not subject:
                return False
            years = get_available_years('jamb', subject)
            return self.parse_choice(message, years) is not None
        elif stage == 'taking_exam':
            return message.strip().lower() in ['a', 'b', 'c', 'd']
        return False
    
    def get_available_options(self, stage: str, user_state: Dict[str, Any]) -> List[str]:
        """
        Get available options for JAMB stages
        """
        if stage == 'selecting_subject':
            return get_available_subjects('jamb')
        elif stage == 'selecting_year':
            subject = user_state.get('subject')
            if subject:
                return get_available_years('jamb', subject)
            return []
        elif stage == 'taking_exam':
            return ['A', 'B', 'C', 'D']
        return []
    
    def _handle_subject_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle subject selection for JAMB
        """
        subjects = get_available_subjects('jamb')
        self.logger.info(f"Available subjects for JAMB: {subjects}")
        
        if not subjects:
            return {
                'response': "Sorry, no subjects available for JAMB. Please contact support.",
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
        
        selected_subject = self.parse_choice(message, subjects)
        
        if selected_subject:
            self.logger.info(f"User {user_phone} selected subject: {selected_subject}")
            
            # Check if years are available for this subject
            years = get_available_years('jamb', selected_subject)
            if not years:
                return {
                    'response': f"Sorry, no years available for {selected_subject}. Please try another subject.\n\n" + 
                               self.format_options_list(subjects, "Available subjects"),
                    'next_stage': 'selecting_subject',
                    'state_updates': {}
                }
            
            return {
                'response': f"✅ You selected: {selected_subject}\n\n" + 
                           self.format_options_list(years, "Available years"),
                'next_stage': 'selecting_year',
                'state_updates': {'subject': selected_subject}
            }
        else:
            return {
                'response': f"Invalid choice. Please select a number between 1 and {len(subjects)}.\n\n" + 
                           self.format_options_list(subjects, "Available subjects"),
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
    
    def _handle_year_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle year selection for JAMB
        """
        subject = user_state.get('subject')
        if not subject:
            return {
                'response': "Session error. Please send 'restart' to start over.",
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
        
        years = get_available_years('jamb', subject)
        self.logger.info(f"Available years for JAMB {subject}: {years}")
        
        selected_year = self.parse_choice(message, years)
        
        if selected_year:
            self.logger.info(f"User {user_phone} selected year: {selected_year}")
            
            # Load questions
            questions = load_exam_data('jamb', subject, selected_year)
            if not questions:
                return {
                    'response': f"Sorry, no questions available for {subject} {selected_year}. Please try another year.\n\n" + 
                               self.format_options_list(years, "Available years"),
                    'next_stage': 'selecting_year',
                    'state_updates': {}
                }
            
            # Shuffle questions for variety
            random.shuffle(questions)
            
            # Format first question
            first_question = self._format_question(questions[0], 1, len(questions))
            intro = f"🎯 Starting JAMB {subject} {selected_year} Practice\n\n"
            
            return {
                'response': intro + first_question,
                'next_stage': 'taking_exam',
                'state_updates': {
                    'year': selected_year,
                    'questions': questions,
                    'total_questions': len(questions),
                    'current_question_index': 0,
                    'score': 0
                }
            }
        else:
            return {
                'response': f"Invalid choice. Please select a number between 1 and {len(years)}.\n\n" + 
                           self.format_options_list(years, "Available years"),
                'next_stage': 'selecting_year',
                'state_updates': {}
            }
    
    def _handle_answer(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle answer submission for JAMB
        """
        questions = user_state.get('questions', [])
        current_index = user_state.get('current_question_index', 0)
        
        if not questions or current_index >= len(questions):
            return {
                'response': "No more questions available. Send 'start' to begin a new session.",
                'next_stage': 'completed',
                'state_updates': {}
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
        
        # Prepare response with explanation
        explanation = current_question.get('explanation', 'No explanation available.')
        response = f"{'✅ Correct!' if is_correct else '❌ Wrong!'} The correct answer is {correct_answer.upper()}.\n\n"
        response += f"💡 {explanation}\n\n"
        
        if next_index >= len(questions):
            # End of exam
            percentage = (new_score / len(questions)) * 100
            response += (f"🎉 Exam completed!\n\n"
                        f"Your Score: {new_score}/{len(questions)} ({percentage:.1f}%)\n\n"
                        f"Send 'start' to take another exam.")
            
            return {
                'response': response,
                'next_stage': 'completed',
                'state_updates': {'score': new_score}
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
        """
        Format a JAMB question for display
        """
        question_text = question.get('question', 'No question text available')
        options = question.get('options', {})
        image_ref = question.get('image_ref')
        
        formatted = f"Question {question_num}/{total_questions}:\n{question_text}\n\n"
        
        # Add image reference if available
        if image_ref:
            formatted += f"📷 Image: {image_ref}\n\n"
        
        # Add options in order
        for key in ['A', 'B', 'C', 'D']:
            if key in options:
                formatted += f"{key}. {options[key]}\n"
        
        formatted += "\nReply with A, B, C, or D"
        
        return formatted