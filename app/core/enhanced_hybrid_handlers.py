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
            
            # FIXED: Handle loading_questions stage asynchronously
            if stage == 'loading_questions':
                return self._handle_question_loading_async(user_phone, user_state, exam_type)
            
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
    
    def _handle_question_loading_async(self, user_phone: str, user_state: Dict[str, Any], exam_type) -> Dict[str, Any]:
        """
        FIXED: Handle question loading asynchronously using real LLM fetching
        """
        try:
            logger.info(f"🔄 ASYNC QUESTION LOADING START: Loading questions asynchronously for {user_phone}")
            
            # Get the required parameters
            subject = user_state.get('subject')
            practice_type = user_state.get('practice_type', 'mixed')
            selected_option = user_state.get('selected_option', 'Mixed Practice')
            num_questions = user_state.get('questions_needed', 25)
            
            if not subject:
                logger.error(f"❌ LOADING ERROR: No subject found for {user_phone}")
                return {
                    'response': "Session error. Please send 'restart' to start over.",
                    'state_updates': {'stage': 'selecting_subject'},
                    'next_handler': f'{user_state.get("exam")}_handler'
                }
            
            logger.info(f"📊 LOADING PARAMS: {user_state.get('exam')} {subject} - {practice_type} - {selected_option} - {num_questions} questions")
            
            # Return a loading message and trigger async loading
            exam = user_state.get('exam', '').upper()
            intro = f"🔍 Fetching {num_questions} real {exam} {subject} questions...\n"
            
            if practice_type == "topic":
                intro += f"📚 Topic: {selected_option}\n"
            elif practice_type == "mixed":
                intro += f"📚 Mixed Practice (All Topics)\n"
            elif practice_type == "weak_areas":
                intro += f"📚 Weak Areas Focus\n"
            else:
                intro += f"📚 {selected_option}\n"
            
            intro += f"⏱️ This may take a moment as we search for authentic past questions...\n"
            intro += f"🔍 Searching multiple years for the best questions"
            
            # Set up async loading - this will be handled by the async method
            return {
                'response': intro,
                'state_updates': {
                    'stage': 'async_loading',  # New intermediate stage
                    'loading_start_time': user_state.get('current_time', 0)
                },
                'next_handler': f'{user_state.get("exam")}_handler',
                'async_task': 'load_questions'  # Signal that async loading is needed
            }
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in async question loading setup: {str(e)}", exc_info=True)
            return {
                'response': "Sorry, there was an error setting up question loading. Please try selecting another option.",
                'state_updates': {'stage': 'selecting_practice_option'},
                'next_handler': f'{user_state.get("exam")}_handler'
            }
    
    async def handle_async_loading(self, user_phone: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the actual async question loading using LLM
        """
        try:
            logger.info(f"🔄 ASYNC LOADING: Starting real question fetch for {user_phone}")
            
            exam = user_state.get('exam')
            exam_type = self.exam_registry.get_exam_type(exam)
            
            # Use the exam type's async loading method
            if hasattr(exam_type, 'load_questions_async'):
                result = await exam_type.load_questions_async(user_phone, user_state)
                logger.info(f"✅ ASYNC LOADING COMPLETE: Got questions for {user_phone}")
                return result
            else:
                logger.error(f"❌ ASYNC LOADING ERROR: Exam type {exam} doesn't support async loading")
                return self._generate_fallback_response(user_phone, user_state)
                
        except Exception as e:
            logger.error(f"❌ ASYNC LOADING FAILED: Error in async question loading: {str(e)}", exc_info=True)
            return self._generate_fallback_response(user_phone, user_state)
    
    def _generate_fallback_response(self, user_phone: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback response when async loading fails"""
        return {
            'response': "Sorry, there was an error loading questions. Please try again or select another option.",
            'state_updates': {'stage': 'selecting_practice_option'},
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
                response += f"\n\n💡 Tip: Take your time to read each question carefully. These are practice questions based on {current_question.get('exam', 'exam')} standards."
            elif accuracy > 0.8:  # Doing well
                response += f"\n\n🎉 Excellent! You're mastering these {current_question.get('exam', 'exam')} questions with {accuracy:.1%} accuracy!"
        
        return {
            'response': response,
            'state_updates': state_updates,
            'next_handler': base_result.get('next_handler')
        }
    
    def _format_question(self, question: Dict[str, Any], question_num: int, total_questions: int) -> str:
        """Format a question for display"""
        question_text = question.get('question', 'No question text available')
        options = question.get('options', {})
        year = question.get('year', 'Unknown')
        topic = question.get('topic')
        exam = question.get('exam', '')
        
        # Format header based on available information
        if topic and topic != "General":
            formatted = f"Question {question_num}/{total_questions} ({exam} {year} - {topic}):\n{question_text}\n\n"
        else:
            formatted = f"Question {question_num}/{total_questions} ({exam} {year}):\n{question_text}\n\n"
        
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
            logger.error(f"❌ ASYNC LOADING ERROR: Error in async question loading: {str(e)}")
            return {
                'response': "Sorry, there was an error loading questions. Please try again.",
                'state_updates': {'stage': 'selecting_subject'},
                'next_handler': f'{user_state.get("exam")}_handler'
            }