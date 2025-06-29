from typing import Dict, Any, Optional
import logging
import asyncio
from app.core.hybrid_message_handler import HybridMessageHandler
from app.services.enhanced_llm_agent import EnhancedLLMAgentService
from app.services.personalized_question_selector import PersonalizedQuestionSelector

logger = logging.getLogger(__name__)

class PersonalizedExamTypeHandler(HybridMessageHandler):
    """
    Enhanced exam type handler with real past questions and personalized learning
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
        """Enhanced structured logic with real past questions"""
        exam = user_state.get('exam')
        stage = user_state.get('stage')
        
        logger.info(f"Handling enhanced {exam} stage {stage} for {user_phone}")
        
        if not exam or not stage:
            return {
                'response': "Session error. Please send 'start' to begin again.",
                'state_updates': {'stage': 'initial'},
                'next_handler': None
            }
        
        try:
            exam_type = self.exam_registry.get_exam_type(exam)
            
            # Special handling for loading questions stage
            if stage == 'loading_questions':
                return self._handle_question_loading(user_phone, user_state, exam_type)
            
            # Regular handling for other stages
            result = exam_type.handle_stage(stage, user_phone, message, user_state)
            
            # Enhanced answer processing with performance tracking
            if stage == 'taking_exam' and message.strip().lower() in ['a', 'b', 'c', 'd']:
                result = self._handle_enhanced_answer(user_phone, message, user_state, result)
            
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
            logger.error(f"Error in enhanced exam handler: {str(e)}", exc_info=True)
            return {
                'response': "Sorry, something went wrong. Please try again or send 'restart' to start over.",
                'state_updates': {},
                'next_handler': f'{exam}_handler'
            }
    
    def _handle_question_loading(self, user_phone: str, user_state: Dict[str, Any], exam_type) -> Dict[str, Any]:
        """Handle asynchronous question loading"""
        try:
            # Check if exam type supports async question loading
            if hasattr(exam_type, 'load_questions_async'):
                # Create a task to load questions asynchronously
                # For now, we'll use a synchronous approach but indicate loading
                return {
                    'response': "⏳ Loading questions... Please wait a moment.",
                    'state_updates': {'stage': 'loading_questions'},
                    'next_handler': f'{user_state.get("exam")}_handler'
                }
            else:
                # Fallback to regular handling
                return exam_type.handle_stage('selecting_subject', user_phone, '', user_state)
                
        except Exception as e:
            logger.error(f"Error loading questions: {e}")
            return {
                'response': "Sorry, there was an error loading questions. Please try again.",
                'state_updates': {'stage': 'selecting_subject'},
                'next_handler': f'{user_state.get("exam")}_handler'
            }
    
    def _handle_enhanced_answer(self, user_phone: str, message: str, 
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
        
        # Track question performance with enhanced details
        question_detail = {
            'question_id': current_question.get('id'),
            'question': current_question.get('question'),
            'user_answer': user_answer.upper(),
            'correct_answer': correct_answer.upper(),
            'is_correct': is_correct,
            'year': current_question.get('year'),
            'exam': current_question.get('exam'),
            'subject': current_question.get('subject'),
            'timestamp': user_state.get('current_time', 0)
        }
        
        # Update state with enhanced question tracking
        state_updates = base_result.get('state_updates', {})
        question_details = user_state.get('question_details', [])
        question_details.append(question_detail)
        state_updates['question_details'] = question_details
        state_updates['last_question_result'] = question_detail
        
        # Enhanced response with year reference and performance feedback
        response = base_result.get('response', '')
        
        # Add performance insights for longer sessions
        current_score = state_updates.get('score', user_state.get('score', 0))
        questions_answered = current_index + 1
        
        if questions_answered >= 5:  # After several questions
            accuracy = current_score / questions_answered
            
            if accuracy < 0.4:  # Struggling
                response += f"\n\n💡 Tip: Take your time to read each question carefully. These are real past questions from {current_question.get('exam', 'exam')} {current_question.get('year', '')}."
            elif accuracy > 0.8:  # Doing well
                response += f"\n\n🎉 Excellent! You're mastering these {current_question.get('exam', 'exam')} questions with {accuracy:.1%} accuracy!"
        
        return {
            'response': response,
            'state_updates': state_updates,
            'next_handler': base_result.get('next_handler')
        }

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

class AsyncQuestionLoader:
    """
    Helper class to handle asynchronous question loading
    """
    
    @staticmethod
    async def load_questions_for_user(user_phone: str, exam_type, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load questions asynchronously and return result
        """
        try:
            if hasattr(exam_type, 'load_questions_async'):
                return await exam_type.load_questions_async(user_phone, user_state)
            else:
                # Fallback for exam types that don't support async loading
                return {
                    'response': "Questions loaded successfully!",
                    'state_updates': {'stage': 'taking_exam'},
                    'next_handler': f'{user_state.get("exam")}_handler'
                }
        except Exception as e:
            logger.error(f"Error in async question loading: {e}")
            return {
                'response': "Sorry, there was an error loading questions. Please try again.",
                'state_updates': {'stage': 'selecting_subject'},
                'next_handler': f'{user_state.get("exam")}_handler'
            }