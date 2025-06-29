from typing import Dict, Any, Optional
import logging
from app.core.hybrid_message_handler import HybridMessageHandler
from app.services.enhanced_llm_agent import EnhancedLLMAgentService
from app.services.personalized_question_selector import PersonalizedQuestionSelector

logger = logging.getLogger(__name__)

class PersonalizedExamTypeHandler(HybridMessageHandler):
    """
    Enhanced exam type handler with personalized question selection
    """
    
    def __init__(self, state_manager, exam_registry):
        super().__init__(state_manager, exam_registry)
        self.llm_agent = EnhancedLLMAgentService()
        self.question_selector = PersonalizedQuestionSelector()
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        stage = user_state.get('stage', '')
        exam = user_state.get('exam')
        
        return (exam is not None and 
                stage not in ['initial', 'selecting_exam'] and
                self.exam_registry.is_exam_supported(exam))
    
    def should_use_llm(self, message: str, user_state: Dict[str, Any]) -> bool:
        """Enhanced logic to determine when to use LLM"""
        stage = user_state.get('stage', '')
        
        if stage == 'taking_exam':
            answer = message.strip().lower()
            if answer in ['a', 'b', 'c', 'd']:
                return False  # Use structured logic for answer processing
            else:
                return True  # Use LLM for questions about the exam
        
        # For selection stages, use structured logic for numbers, LLM for queries
        try:
            int(message.strip())
            return False
        except ValueError:
            return True
    
    def _handle_with_logic(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced structured logic with personalized question selection"""
        exam = user_state.get('exam')
        stage = user_state.get('stage')
        
        logger.info(f"Handling personalized {exam} stage {stage} for {user_phone}")
        
        if not exam or not stage:
            return {
                'response': "Session error. Please send 'start' to begin again.",
                'state_updates': {'stage': 'initial'},
                'next_handler': None
            }
        
        try:
            exam_type = self.exam_registry.get_exam_type(exam)
            
            # Special handling for year selection to use personalized questions
            if stage == 'selecting_year' and message.strip().isdigit():
                return self._handle_personalized_year_selection(user_phone, message, user_state, exam_type)
            
            # Regular handling for other stages
            result = exam_type.handle_stage(stage, user_phone, message, user_state)
            
            # Enhanced answer processing with performance tracking
            if stage == 'taking_exam' and message.strip().lower() in ['a', 'b', 'c', 'd']:
                result = self._handle_personalized_answer(user_phone, message, user_state, result)
            
            state_updates = result.get('state_updates', {})
            next_stage = result.get('next_stage')
            
            if next_stage and next_stage != stage:
                state_updates['stage'] = next_stage
                logger.info(f"Stage transition for {user_phone}: {stage} -> {next_stage}")
            
            return {
                'response': result.get('response', 'No response generated.'),
                'state_updates': state_updates,
                'next_handler': f'{exam}_handler' if next_stage != 'completed' else None
            }
            
        except Exception as e:
            logger.error(f"Error in personalized exam handler: {str(e)}", exc_info=True)
            return {
                'response': "Sorry, something went wrong. Please try again or send 'restart' to start over.",
                'state_updates': {},
                'next_handler': f'{exam}_handler'
            }
    
    def _handle_personalized_year_selection(self, user_phone: str, message: str, 
                                          user_state: Dict[str, Any], exam_type) -> Dict[str, Any]:
        """Handle year selection with personalized question loading"""
        subject = user_state.get('subject')
        exam = user_state.get('exam')
        
        if not subject or not exam:
            return {
                'response': "Session error. Please send 'restart' to start over.",
                'state_updates': {'stage': 'selecting_subject'},
                'next_handler': f'{exam}_handler'
            }
        
        # Get available years
        from app.utils.helpers import get_available_years
        years = get_available_years(exam, subject)
        
        try:
            choice = int(message.strip()) - 1
            if 0 <= choice < len(years):
                selected_year = years[choice]
                
                # Load personalized questions instead of random ones
                personalized_questions = self.question_selector.get_personalized_questions(
                    user_phone, exam, subject, selected_year, num_questions=10
                )
                
                if not personalized_questions:
                    return {
                        'response': f"Sorry, no questions available for {subject} {selected_year}. Please try another year.",
                        'state_updates': {},
                        'next_handler': f'{exam}_handler'
                    }
                
                # Format first question
                first_question = self._format_question(personalized_questions[0], 1, len(personalized_questions))
                intro = f"🎯 Starting Personalized {exam.upper()} {subject} {selected_year} Practice\n"
                intro += f"📊 Questions selected based on your performance history\n\n"
                
                return {
                    'response': intro + first_question,
                    'state_updates': {
                        'year': selected_year,
                        'stage': 'taking_exam',
                        'questions': personalized_questions,
                        'total_questions': len(personalized_questions),
                        'current_question_index': 0,
                        'score': 0,
                        'question_details': []  # Track individual question performance
                    },
                    'next_handler': f'{exam}_handler'
                }
            else:
                return {
                    'response': f"Invalid choice. Please select a number between 1 and {len(years)}.",
                    'state_updates': {},
                    'next_handler': f'{exam}_handler'
                }
        except ValueError:
            return {
                'response': f"Please enter a valid number between 1 and {len(years)}.",
                'state_updates': {},
                'next_handler': f'{exam}_handler'
            }
    
    def _handle_personalized_answer(self, user_phone: str, message: str, 
                                  user_state: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced answer handling with performance tracking"""
        questions = user_state.get('questions', [])
        current_index = user_state.get('current_question_index', 0)
        
        if not questions or current_index >= len(questions):
            return base_result
        
        current_question = questions[current_index]
        user_answer = message.strip().lower()
        correct_answer = current_question.get('correct_answer', '').lower()
        is_correct = user_answer == correct_answer
        
        # Track question performance
        question_detail = {
            'question_id': current_question.get('id'),
            'question': current_question.get('question'),
            'user_answer': user_answer.upper(),
            'correct_answer': correct_answer.upper(),
            'is_correct': is_correct,
            'timestamp': time.time()
        }
        
        # Update state with question tracking
        state_updates = base_result.get('state_updates', {})
        question_details = user_state.get('question_details', [])
        question_details.append(question_detail)
        state_updates['question_details'] = question_details
        state_updates['last_question_result'] = question_detail
        
        # Enhanced response with personalized feedback
        response = base_result.get('response', '')
        
        # Add adaptive feedback based on performance
        current_score = state_updates.get('score', user_state.get('score', 0))
        questions_answered = current_index + 1
        
        if questions_answered >= 3:  # After a few questions
            accuracy = current_score / questions_answered
            
            if accuracy < 0.4:  # Struggling
                response += f"\n\n💡 Tip: Take your time to read each question carefully. Review the explanations to understand the concepts better."
            elif accuracy > 0.8:  # Doing well
                response += f"\n\n🎉 Great job! You're performing excellently with {accuracy:.1%} accuracy!"
        
        return {
            'response': response,
            'state_updates': state_updates,
            'next_handler': base_result.get('next_handler')
        }
    
    def _format_question(self, question: Dict[str, Any], question_num: int, total_questions: int) -> str:
        """Format a question for display"""
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

class SmartPerformanceHandler(HybridMessageHandler):
    """
    Handler for performance-related queries and commands
    """
    
    def __init__(self, state_manager, exam_registry):
        super().__init__(state_manager, exam_registry)
        self.llm_agent = EnhancedLLMAgentService()
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        performance_keywords = [
            'performance', 'score', 'progress', 'summary', 'stats', 'statistics',
            'how am i doing', 'my results', 'weakness', 'strength', 'improve'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in performance_keywords)
    
    def should_use_llm(self, message: str, user_state: Dict[str, Any]) -> bool:
        return True  # Always use enhanced LLM for performance queries
    
    def _handle_with_logic(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """This shouldn't be called since we always use LLM"""
        return {
            'response': "Let me get your performance summary...",
            'state_updates': {},
            'next_handler': None
        }