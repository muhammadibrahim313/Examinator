from typing import Dict, Any, Optional
import logging
import asyncio
from app.core.hybrid_message_handler import HybridMessageHandler
from app.services.enhanced_llm_agent import EnhancedLLMAgentService
from app.services.personalized_question_selector import PersonalizedQuestionSelector

logger = logging.getLogger(__name__)

class PersonalizedExamTypeHandler(HybridMessageHandler):
    """
    Enhanced exam type handler with FIXED immediate loading, navigation, validation, and test controls
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
        """Enhanced LLM usage detection with FAQ and help support"""
        stage = user_state.get('stage', '')
        message_lower = message.lower().strip()
        
        # NEVER use LLM during loading stages
        if stage in ['loading_questions', 'async_loading']:
            return False
        
        # Always use LLM for FAQ, help, and general queries
        faq_keywords = ['help', 'faq', 'question', 'how', 'what', 'why', 'explain', 'tell me', 'can you', 'about', 'info']
        if any(keyword in message_lower for keyword in faq_keywords):
            return True
        
        # Use LLM for navigation commands that need explanation
        navigation_commands = ['back', 'previous', 'return', 'go back']
        if any(cmd in message_lower for cmd in navigation_commands):
            return True
        
        # Use LLM for test control commands that need explanation
        test_control_commands = ['stop', 'quit', 'exit', 'submit', 'pause', 'end']
        if any(cmd in message_lower for cmd in test_control_commands):
            return True
        
        if stage == 'taking_exam':
            # Use structured logic for valid answers, LLM for everything else
            if message_lower in ['a', 'b', 'c', 'd']:
                return False
            else:
                return True  # Use LLM for questions, help, or invalid inputs during exam
        
        # For selection stages, use structured logic for numbers, LLM for queries
        try:
            int(message.strip())
            return False
        except ValueError:
            return True
    
    def _handle_with_logic(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced logic handler with navigation, validation, and test controls"""
        exam = user_state.get('exam')
        stage = user_state.get('stage')
        message_lower = message.lower().strip()
        
        logger.info(f"Handling enhanced {exam} stage {stage} for {user_phone}")
        
        if not exam or not stage:
            return {
                'response': "Session error. Please send 'start' to begin again.",
                'state_updates': {'stage': 'initial'},
                'next_handler': None
            }
        
        # Handle loading_questions stage - trigger immediate loading
        if stage == 'loading_questions':
            logger.info(f"🔄 IMMEDIATE LOADING TRIGGER: Stage is loading_questions for {user_phone}")
            return {
                'response': '',  # Empty response - will be replaced by async loading result
                'state_updates': {'stage': 'async_loading'},
                'next_handler': f'{exam}_handler',
                'immediate_async_load': True
            }
        
        # Handle async_loading stage
        if stage == 'async_loading':
            return {
                'response': "⏳ Still loading questions... Please wait a moment.",
                'state_updates': {},
                'next_handler': f'{exam}_handler'
            }
        
        # Handle navigation commands
        navigation_result = self._handle_navigation_commands(message_lower, user_state)
        if navigation_result:
            return navigation_result
        
        # Handle test control commands during exam
        if stage == 'taking_exam':
            test_control_result = self._handle_test_control_commands(message_lower, user_phone, user_state)
            if test_control_result:
                return test_control_result
        
        # Enhanced input validation with helpful error messages
        validation_result = self._validate_and_guide_input(message, stage, user_state)
        if validation_result:
            return validation_result
        
        try:
            exam_type = self.exam_registry.get_exam_type(exam)
            
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
    
    def _handle_navigation_commands(self, message_lower: str, user_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle navigation commands like 'back', 'previous', etc."""
        navigation_commands = ['back', 'previous', 'return', 'go back', 'menu']
        
        if any(cmd in message_lower for cmd in navigation_commands):
            stage = user_state.get('stage', '')
            exam = user_state.get('exam')
            
            # Define stage hierarchy for navigation
            stage_hierarchy = {
                'taking_exam': 'selecting_practice_option',
                'loading_questions': 'selecting_practice_option',
                'async_loading': 'selecting_practice_option',
                'selecting_practice_option': 'selecting_practice_mode',
                'selecting_practice_mode': 'selecting_subject',
                'selecting_subject': 'selecting_exam',
                'selecting_year': 'selecting_subject',  # For fallback exam types
            }
            
            previous_stage = stage_hierarchy.get(stage)
            
            if previous_stage:
                if previous_stage == 'selecting_exam':
                    # Going back to exam selection
                    exams = self.exam_registry.get_available_exams()
                    exam_list = "\n".join([f"{i+1}. {exam.upper()}" for i, exam in enumerate(exams)])
                    response = (f"🔙 Going back to exam selection\n\n"
                               f"🎓 Available exams:\n{exam_list}\n\n"
                               f"Please reply with the number of your choice.\n\n"
                               f"💡 Commands: 'help' (assistance), 'faq' (common questions)")
                    
                    return {
                        'response': response,
                        'state_updates': {
                            'stage': 'selecting_exam',
                            'exam': None,
                            'subject': None,
                            'practice_mode': None,
                            'selected_option': None,
                            'questions': [],
                            'current_question_index': 0,
                            'score': 0
                        },
                        'next_handler': 'exam_selection'
                    }
                
                elif previous_stage == 'selecting_subject':
                    # Going back to subject selection
                    exam_type = self.exam_registry.get_exam_type(exam)
                    subjects = exam_type.get_available_options('selecting_subject', user_state)
                    
                    response = f"🔙 Going back to subject selection for {exam.upper()}\n\n"
                    response += exam_type.format_options_list(subjects, f"Available {exam.upper()} subjects")
                    response += f"\n\n💡 Commands: 'back' (exam selection), 'help' (assistance)"
                    
                    return {
                        'response': response,
                        'state_updates': {
                            'stage': 'selecting_subject',
                            'subject': None,
                            'practice_mode': None,
                            'selected_option': None,
                            'questions': [],
                            'current_question_index': 0,
                            'score': 0
                        },
                        'next_handler': f'{exam}_handler'
                    }
                
                elif previous_stage == 'selecting_practice_mode':
                    # Going back to practice mode selection
                    subject = user_state.get('subject')
                    response = f"🔙 Going back to practice mode selection\n\n"
                    response += f"✅ Subject: {subject}\n\n"
                    response += "🎯 How would you like to practice?\n\n"
                    response += "1. Practice by Topic\n"
                    response += "2. Practice by Year\n\n"
                    response += "Please reply with 1 or 2.\n\n"
                    response += "💡 Commands: 'back' (subject selection), 'help' (assistance)"
                    
                    return {
                        'response': response,
                        'state_updates': {
                            'stage': 'selecting_practice_mode',
                            'practice_mode': None,
                            'selected_option': None,
                            'questions': [],
                            'current_question_index': 0,
                            'score': 0
                        },
                        'next_handler': f'{exam}_handler'
                    }
                
                elif previous_stage == 'selecting_practice_option':
                    # Going back to practice option selection
                    subject = user_state.get('subject')
                    practice_mode = user_state.get('practice_mode')
                    exam_type = self.exam_registry.get_exam_type(exam)
                    
                    if practice_mode == 'topic':
                        from app.services.topic_based_question_fetcher import TopicBasedQuestionFetcher
                        topic_fetcher = TopicBasedQuestionFetcher()
                        options = topic_fetcher.get_practice_options(exam, subject)
                        response = f"🔙 Going back to topic selection\n\n"
                        response += f"✅ Subject: {subject}\n"
                        response += f"✅ Mode: Practice by Topic\n\n"
                        response += exam_type.format_options_list(options, f"{subject} Topics")
                    else:
                        # Year mode
                        exam_info = exam_type.question_fetcher.get_exam_info(exam)
                        subject_info = exam_info.get('subjects', {}).get(subject, {})
                        years = subject_info.get('years_available', [])
                        response = f"🔙 Going back to year selection\n\n"
                        response += f"✅ Subject: {subject}\n"
                        response += f"✅ Mode: Practice by Year\n\n"
                        response += exam_type.format_options_list(years, "Available Years")
                    
                    response += f"\n\n💡 Commands: 'back' (practice mode), 'help' (assistance)"
                    
                    return {
                        'response': response,
                        'state_updates': {
                            'stage': 'selecting_practice_option',
                            'selected_option': None,
                            'questions': [],
                            'current_question_index': 0,
                            'score': 0
                        },
                        'next_handler': f'{exam}_handler'
                    }
            
            else:
                return {
                    'response': "🔙 You're already at the beginning. Send 'start' to begin a new session or 'restart' to start over.\n\n💡 Commands: 'help' (assistance), 'faq' (common questions)",
                    'state_updates': {},
                    'next_handler': f'{exam}_handler'
                }
        
        return None
    
    def _handle_test_control_commands(self, message_lower: str, user_phone: str, user_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle test control commands like 'stop', 'quit', 'submit', 'pause'"""
        control_commands = ['stop', 'quit', 'exit', 'submit', 'pause', 'end']
        
        if any(cmd in message_lower for cmd in control_commands):
            questions = user_state.get('questions', [])
            current_index = user_state.get('current_question_index', 0)
            score = user_state.get('score', 0)
            total_questions = len(questions)
            
            if total_questions == 0:
                return {
                    'response': "No active test to stop. Send 'start' to begin a new practice session.\n\n💡 Commands: 'help' (assistance), 'faq' (common questions)",
                    'state_updates': {'stage': 'completed'},
                    'next_handler': None
                }
            
            # Calculate performance
            questions_answered = current_index
            if questions_answered > 0:
                percentage = (score / questions_answered) * 100
                performance_text = f"📊 Performance Summary:\n"
                performance_text += f"• Questions answered: {questions_answered}/{total_questions}\n"
                performance_text += f"• Score: {score}/{questions_answered} ({percentage:.1f}%)\n"
                performance_text += f"• Remaining: {total_questions - questions_answered} questions\n\n"
            else:
                performance_text = "📊 No questions were answered.\n\n"
            
            # Determine action based on command
            if 'submit' in message_lower:
                action_text = "📝 Test submitted successfully!"
            elif 'pause' in message_lower:
                action_text = "⏸️ Test paused. You can resume anytime."
            else:
                action_text = "⏹️ Test stopped."
            
            exam = user_state.get('exam', '').upper()
            subject = user_state.get('subject', '')
            
            response = f"{action_text}\n\n"
            response += f"🎯 {exam} {subject} Practice Session\n"
            response += performance_text
            
            # Provide encouragement based on performance
            if questions_answered > 0:
                if percentage >= 80:
                    response += "🌟 Excellent work! You're doing great!\n"
                elif percentage >= 60:
                    response += "👍 Good progress! Keep practicing to improve.\n"
                else:
                    response += "💪 Keep studying and practicing. You'll get better!\n"
            
            response += "\n🎯 Next Steps:\n"
            response += "• Send 'start' - Begin new practice session\n"
            response += "• Send 'help' - Get assistance\n"
            response += "• Send 'faq' - Common questions\n"
            
            if 'pause' in message_lower:
                response += "• Send 'resume' - Continue this test (if supported)"
            
            return {
                'response': response,
                'state_updates': {
                    'stage': 'completed',
                    'final_score': score,
                    'final_percentage': percentage if questions_answered > 0 else 0
                },
                'next_handler': None
            }
        
        return None
    
    def _validate_and_guide_input(self, message: str, stage: str, user_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhanced input validation with helpful error messages and guidance"""
        message_clean = message.strip()
        
        # Check for common invalid inputs in selection stages
        selection_stages = ['selecting_subject', 'selecting_practice_mode', 'selecting_practice_option', 'selecting_year']
        
        if stage in selection_stages:
            # Check if it's a number but invalid range
            try:
                choice = int(message_clean)
                exam = user_state.get('exam')
                exam_type = self.exam_registry.get_exam_type(exam)
                
                # Get valid options for current stage
                if stage == 'selecting_practice_mode':
                    valid_range = 2  # 1 or 2
                    options_text = "1. Practice by Topic\n2. Practice by Year"
                else:
                    options = exam_type.get_available_options(stage, user_state)
                    valid_range = len(options)
                    options_text = exam_type.format_options_list(options, "Available options")
                
                if choice < 1 or choice > valid_range:
                    response = f"❌ Invalid choice: {choice}\n\n"
                    response += f"Please select a number between 1 and {valid_range}.\n\n"
                    response += options_text
                    response += "\n\n💡 Available Commands:\n"
                    response += "• 'back' - Go to previous step\n"
                    response += "• 'restart' - Start over completely\n"
                    response += "• 'help' - Get assistance\n"
                    response += "• 'faq' - Common questions"
                    
                    return {
                        'response': response,
                        'state_updates': {},
                        'next_handler': f'{exam}_handler'
                    }
            
            except ValueError:
                # Not a number - provide specific guidance
                if message_clean.lower() in ['a', 'b', 'c', 'd']:
                    response = f"❌ You sent '{message_clean.upper()}' but we're not in a question yet.\n\n"
                    response += f"Please select a number from the options above.\n\n"
                    response += "💡 Available Commands:\n"
                    response += "• Numbers (1, 2, 3...) - Select options\n"
                    response += "• 'back' - Go to previous step\n"
                    response += "• 'help' - Get assistance\n"
                    response += "• 'faq' - Ask questions"
                    
                    return {
                        'response': response,
                        'state_updates': {},
                        'next_handler': f'{user_state.get("exam")}_handler'
                    }
                
                elif message_clean.isalpha() and len(message_clean) <= 3:
                    response = f"❌ '{message_clean}' is not a valid option.\n\n"
                    response += f"Please enter a number to select from the options above.\n\n"
                    response += "💡 Available Commands:\n"
                    response += "• Numbers (1, 2, 3...) - Select options\n"
                    response += "• 'back' - Go to previous step\n"
                    response += "• 'restart' - Start over\n"
                    response += "• 'help' - Get assistance"
                    
                    return {
                        'response': response,
                        'state_updates': {},
                        'next_handler': f'{user_state.get("exam")}_handler'
                    }
        
        elif stage == 'taking_exam':
            # Enhanced exam answer validation
            if message_clean.lower() not in ['a', 'b', 'c', 'd']:
                # Check for common mistakes
                if message_clean.isdigit():
                    response = f"❌ You sent '{message_clean}' but please reply with A, B, C, or D for your answer.\n\n"
                elif len(message_clean) == 1 and message_clean.lower() in 'abcd':
                    # Single letter but wrong case - this should be handled by the exam logic
                    return None
                else:
                    response = f"❌ Invalid answer format: '{message_clean}'\n\n"
                
                response += "Please reply with A, B, C, or D for your answer.\n\n"
                response += "💡 Available Commands:\n"
                response += "• A, B, C, D - Answer the question\n"
                response += "• 'stop' - End the test\n"
                response += "• 'submit' - Submit current progress\n"
                response += "• 'pause' - Pause the test\n"
                response += "• 'help' - Get assistance\n"
                response += "• 'faq' - Ask questions about the exam"
                
                return {
                    'response': response,
                    'state_updates': {},
                    'next_handler': f'{user_state.get("exam")}_handler'
                }
        
        return None
    
    async def handle_async_loading(self, user_phone: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle async question loading with proper error handling"""
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
                return self._generate_error_response(user_phone, user_state)
                
        except Exception as e:
            logger.error(f"❌ ASYNC LOADING FAILED: Error in async question loading: {str(e)}", exc_info=True)
            return self._generate_error_response(user_phone, user_state)
    
    def _generate_error_response(self, user_phone: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate error response with helpful guidance"""
        exam = user_state.get('exam', '').upper()
        subject = user_state.get('subject', '')
        
        response = f"❌ Sorry, there was an error loading {exam} {subject} questions.\n\n"
        response += f"This could be due to:\n"
        response += f"• Network connectivity issues\n"
        response += f"• Temporary server problems\n\n"
        response += f"💡 What you can do:\n"
        response += f"• Send 'back' - Select another option\n"
        response += f"• Send 'restart' - Start over\n"
        response += f"• Send 'help' - Get assistance\n"
        response += f"• Try again in a few minutes"
        
        return {
            'response': response,
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
        
        # Enhanced response with navigation hints
        response = base_result.get('response', '')
        
        # Add command hints
        response += f"\n\n💡 Commands: 'stop' (end test), 'submit' (submit progress), 'help' (assistance)"
        
        # Add performance insights for longer sessions
        current_score = state_updates.get('score', user_state.get('score', 0))
        questions_answered = current_index + 1
        
        if questions_answered >= 5:  # After several questions
            accuracy = current_score / questions_answered
            
            if accuracy < 0.4:  # Struggling
                response += f"\n\n💡 Tip: Take your time to read each question carefully. Send 'help' if you need study tips."
            elif accuracy > 0.8:  # Doing well
                response += f"\n\n🎉 Excellent! You're mastering these questions with {accuracy:.1%} accuracy!"
        
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

class SmartFAQHandler(HybridMessageHandler):
    """
    Enhanced FAQ and general help handler with comprehensive support
    """
    
    def __init__(self, state_manager, exam_registry):
        super().__init__(state_manager, exam_registry)
        self.llm_agent = EnhancedLLMAgentService()
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        faq_keywords = [
            'help', 'faq', 'question', 'how', 'what', 'why', 'when', 'where',
            'explain', 'tell me', 'can you', 'do you', 'about', 'info',
            'support', 'assistance', 'guide', 'tutorial', 'commands'
        ]
        message_lower = message.lower()
        
        # Don't handle if it's a simple number (likely a selection)
        try:
            int(message.strip())
            return False
        except ValueError:
            pass
        
        # Don't handle if it's a simple answer (A, B, C, D)
        if message.strip().lower() in ['a', 'b', 'c', 'd']:
            return False
        
        return any(keyword in message_lower for keyword in faq_keywords)
    
    def should_use_llm(self, message: str, user_state: Dict[str, Any]) -> bool:
        return True  # Always use LLM for FAQ queries
    
    def _handle_with_logic(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback structured FAQ responses"""
        message_lower = message.lower()
        
        if 'help' in message_lower:
            return self._get_help_response(user_state)
        elif 'command' in message_lower:
            return self._get_commands_response(user_state)
        elif 'faq' in message_lower:
            return self._get_faq_response(user_state)
        else:
            return {
                'response': "I'm here to help! Ask me anything about exam practice or send 'help' for available commands.",
                'state_updates': {},
                'next_handler': None
            }
    
    def _get_help_response(self, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive help response"""
        stage = user_state.get('stage', 'initial')
        exam = user_state.get('exam')
        
        response = "🆘 **Help & Commands**\n\n"
        
        # General commands
        response += "🔧 **General Commands:**\n"
        response += "• 'start' - Begin new practice session\n"
        response += "• 'restart' - Start over completely\n"
        response += "• 'back' - Go to previous step\n"
        response += "• 'help' - Show this help\n"
        response += "• 'faq' - Common questions\n\n"
        
        # Stage-specific help
        if stage == 'taking_exam':
            response += "📝 **During Exam:**\n"
            response += "• A, B, C, D - Answer questions\n"
            response += "• 'stop' - Stop the test\n"
            response += "• 'submit' - Submit current progress\n"
            response += "• 'pause' - Pause the test\n\n"
        
        elif stage in ['selecting_subject', 'selecting_practice_mode', 'selecting_practice_option']:
            response += "🎯 **During Selection:**\n"
            response += "• Send number (1, 2, 3...) to select\n"
            response += "• 'back' - Go to previous step\n\n"
        
        # Available exams
        response += "🎓 **Available Exams:** JAMB, SAT, NEET\n"
        response += "📚 **Practice Modes:** Topic, Year, Mixed, Weak Areas\n\n"
        response += "💡 Ask me anything about exam practice, study tips, or specific subjects!"
        
        return {
            'response': response,
            'state_updates': {},
            'next_handler': user_state.get('exam') and f'{user_state.get("exam")}_handler' or None
        }
    
    def _get_commands_response(self, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get available commands for current stage"""
        stage = user_state.get('stage', 'initial')
        
        response = "🔧 **Available Commands:**\n\n"
        
        if stage == 'initial':
            response += "• 'start' - Begin exam practice\n"
            response += "• 'help' - Get help\n"
            response += "• 'faq' - Common questions\n"
        
        elif stage == 'selecting_exam':
            response += "• 1, 2, 3 - Select exam\n"
            response += "• 'help' - Get help\n"
            response += "• 'restart' - Start over\n"
        
        elif stage in ['selecting_subject', 'selecting_practice_mode', 'selecting_practice_option']:
            response += "• Numbers - Select options\n"
            response += "• 'back' - Previous step\n"
            response += "• 'restart' - Start over\n"
            response += "• 'help' - Get help\n"
        
        elif stage == 'taking_exam':
            response += "• A, B, C, D - Answer questions\n"
            response += "• 'stop' - Stop test\n"
            response += "• 'submit' - Submit progress\n"
            response += "• 'pause' - Pause test\n"
            response += "• 'help' - Get help\n"
        
        else:
            response += "• 'start' - Begin new session\n"
            response += "• 'help' - Get help\n"
        
        response += "\n💡 You can also ask me questions anytime!"
        
        return {
            'response': response,
            'state_updates': {},
            'next_handler': user_state.get('exam') and f'{user_state.get("exam")}_handler' or None
        }
    
    def _get_faq_response(self, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get FAQ response with common questions"""
        response = "❓ **Frequently Asked Questions**\n\n"
        
        response += "🎓 **About Exams:**\n"
        response += "Q: What exams are available?\n"
        response += "A: JAMB, SAT, and NEET with all subjects\n\n"
        
        response += "📚 **Practice Modes:**\n"
        response += "Q: How can I practice?\n"
        response += "A: By Topic (specific topics) or By Year (complete years)\n\n"
        
        response += "🎯 **During Tests:**\n"
        response += "Q: Can I stop a test midway?\n"
        response += "A: Yes! Send 'stop', 'submit', or 'pause'\n\n"
        
        response += "🔄 **Navigation:**\n"
        response += "Q: Can I go back if I make a mistake?\n"
        response += "A: Yes! Send 'back' to go to previous step\n\n"
        
        response += "💡 **Need More Help?**\n"
        response += "Ask me specific questions like:\n"
        response += "• 'How do I practice JAMB Biology?'\n"
        response += "• 'What study tips do you have?'\n"
        response += "• 'How can I improve my scores?'"
        
        return {
            'response': response,
            'state_updates': {},
            'next_handler': user_state.get('exam') and f'{user_state.get("exam")}_handler' or None
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