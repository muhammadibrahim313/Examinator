from typing import List, Dict, Any, Optional
from app.core.enhanced_hybrid_handlers import (
    PersonalizedExamTypeHandler, 
    SmartPerformanceHandler,
    SmartFAQHandler
)
from app.core.hybrid_message_handler import (
    SmartGlobalCommandHandler,
    SmartExamSelectionHandler,
    SmartFallbackHandler
)
from app.core.system_commands import SystemCommands, InputValidator
from app.services.enhanced_state import EnhancedUserStateManager
import logging
import asyncio

logger = logging.getLogger(__name__)

class EnhancedSmartMessageProcessor:
    """
    Enhanced message processor with FIXED system command validation
    """
    
    def __init__(self, state_manager, exam_registry):
        # Use enhanced state manager
        self.state_manager = EnhancedUserStateManager() if not isinstance(state_manager, EnhancedUserStateManager) else state_manager
        self.exam_registry = exam_registry
        self.handlers: List = []
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup enhanced handlers with system command validation"""
        self.handlers = [
            SmartGlobalCommandHandler(self.state_manager, self.exam_registry),
            SmartFAQHandler(self.state_manager, self.exam_registry),
            SmartPerformanceHandler(self.state_manager, self.exam_registry),
            SmartExamSelectionHandler(self.state_manager, self.exam_registry),
            PersonalizedExamTypeHandler(self.state_manager, self.exam_registry),
            SmartFallbackHandler(self.state_manager, self.exam_registry)
        ]
        logger.info(f"Initialized {len(self.handlers)} enhanced smart message handlers with system command validation")
    
    async def process_message(self, user_phone: str, message: str) -> str:
        """
        Process a message with FIXED system command validation
        """
        try:
            # Get current user state
            user_state = self.state_manager.get_user_state(user_phone)
            current_stage = user_state.get('stage', 'initial')
            
            logger.info(f"Processing enhanced message from {user_phone}")
            logger.info(f"Current stage: {current_stage}")
            logger.info(f"Message: '{message}'")
            
            # STEP 1: Check for system commands FIRST (before any handler routing)
            if self._should_handle_as_system_command(message, current_stage, user_state):
                logger.info(f"🔧 SYSTEM COMMAND DETECTED: '{message}' - using structured logic")
                return await self._handle_system_command(user_phone, message, user_state)
            
            # STEP 2: Check for LLM trigger prefixes
            if SystemCommands.is_llm_trigger(message):
                logger.info(f"🤖 LLM TRIGGER DETECTED: '{message}' - routing to LLM")
                return await self._handle_llm_query(user_phone, message, user_state)
            
            # STEP 3: Handle async loading stage
            if current_stage == 'async_loading':
                return await self._handle_async_loading(user_phone, user_state)
            
            # STEP 4: Validate input for current stage
            validation_result = self._validate_input_for_stage(message, current_stage, user_state)
            if not validation_result['valid']:
                logger.info(f"❌ INPUT VALIDATION FAILED: {validation_result['error']}")
                return self._format_validation_error(validation_result, current_stage, user_state)
            
            # STEP 5: Find the appropriate handler for valid inputs
            handler = self._find_handler(message, user_state)
            if not handler:
                logger.error(f"No handler found for message from {user_phone}")
                return "Sorry, something went wrong. Please try again or send 'restart'."
            
            logger.info(f"Using enhanced handler: {handler.__class__.__name__}")
            
            # STEP 6: Process the message
            result = await handler.handle(user_phone, message, user_state)
            
            # STEP 7: Check for immediate async loading signal
            if result.get('immediate_async_load'):
                logger.info(f"🔄 IMMEDIATE ASYNC LOADING: Processing async loading for {user_phone} in same request")
                
                # Apply state updates first (set to async_loading)
                state_updates = result.get('state_updates', {})
                if state_updates:
                    self.state_manager.update_user_state(user_phone, state_updates)
                
                # Perform async loading immediately and return the final result
                loading_result = await self._handle_async_loading(user_phone, self.state_manager.get_user_state(user_phone))
                
                # Apply any additional state updates from loading
                if isinstance(loading_result, dict):
                    loading_state_updates = loading_result.get('state_updates', {})
                    if loading_state_updates:
                        self.state_manager.update_user_state(user_phone, loading_state_updates)
                    
                    # Return the final response (first question)
                    final_response = loading_result.get('response', 'Questions loaded successfully!')
                else:
                    final_response = loading_result
                
                logger.info(f"✅ IMMEDIATE ASYNC COMPLETE: Returning final response for {user_phone}")
                return final_response
            
            # STEP 8: Apply state updates if any
            state_updates = result.get('state_updates', {})
            if state_updates:
                logger.info(f"Applying enhanced state updates for {user_phone}: {list(state_updates.keys())}")
                self.state_manager.update_user_state(user_phone, state_updates)
            
            # STEP 9: Return response
            response = result.get('response', 'No response generated.')
            logger.info(f"Enhanced handler result for {user_phone}: {len(response)} characters")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing enhanced message from {user_phone}: {str(e)}", exc_info=True)
            return "Sorry, something went wrong. Please try again or send 'restart' to start over."
    
    def _should_handle_as_system_command(self, message: str, stage: str, user_state: Dict[str, Any]) -> bool:
        """
        Determine if message should be handled as system command
        """
        # Get max options for current stage
        max_options = self._get_max_options_for_stage(stage, user_state)
        
        # Use system command logic to determine routing
        return SystemCommands.should_use_structured_logic(message, stage, max_options)
    
    def _get_max_options_for_stage(self, stage: str, user_state: Dict[str, Any]) -> int:
        """Get maximum valid options for current stage"""
        try:
            if stage == 'selecting_exam':
                return len(self.exam_registry.get_available_exams())
            elif stage == 'selecting_practice_mode':
                return 2  # Topic or Year
            elif stage in ['selecting_subject', 'selecting_practice_option']:
                exam = user_state.get('exam')
                if exam:
                    exam_type = self.exam_registry.get_exam_type(exam)
                    options = exam_type.get_available_options(stage, user_state)
                    return len(options)
            return 0
        except Exception:
            return 0
    
    def _validate_input_for_stage(self, message: str, stage: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input for current stage"""
        if stage == 'selecting_exam':
            available_exams = self.exam_registry.get_available_exams()
            return InputValidator.validate_exam_selection(message, available_exams)
        
        elif stage == 'taking_exam':
            return InputValidator.validate_exam_answer(message)
        
        elif stage in ['selecting_subject', 'selecting_practice_mode', 'selecting_practice_option']:
            max_options = self._get_max_options_for_stage(stage, user_state)
            context = stage.replace('selecting_', '')
            return InputValidator.validate_number_selection(message, max_options, context)
        
        else:
            # For other stages, assume valid
            return {'valid': True, 'type': 'general'}
    
    def _format_validation_error(self, validation_result: Dict[str, Any], stage: str, user_state: Dict[str, Any]) -> str:
        """Format validation error with helpful guidance"""
        error = validation_result.get('error', 'Invalid input')
        help_text = validation_result.get('help', '')
        
        response = f"❌ {error}\n\n"
        
        if help_text:
            response += f"{help_text}\n\n"
        
        # Add stage-specific commands
        response += "💡 Available Commands:\n"
        
        if stage == 'selecting_exam':
            response += "• Numbers (1, 2, 3) - Select exam\n"
            response += "• 'restart' - Start over\n"
            response += "• 'help' - Get help\n"
        elif stage in ['selecting_subject', 'selecting_practice_mode', 'selecting_practice_option']:
            response += "• Numbers - Select from options above\n"
            response += "• 'back' - Go to previous step\n"
            response += "• 'restart' - Start over\n"
            response += "• 'help' - Get help\n"
        elif stage == 'taking_exam':
            response += "• A, B, C, D - Answer the question\n"
            response += "• 'stop' - End the test\n"
            response += "• 'submit' - Submit progress\n"
            response += "• 'help' - Get help\n"
        else:
            response += "• 'start' - Begin new session\n"
            response += "• 'help' - Get help\n"
        
        response += "\n💡 To chat with AI: Use 'ask: your question'"
        
        return response
    
    async def _handle_system_command(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> str:
        """Handle system commands with structured logic"""
        command_type = SystemCommands.get_command_type(message)
        stage = user_state.get('stage', 'initial')
        
        if command_type == SystemCommands.CommandType.HELP:
            exam = user_state.get('exam')
            return SystemCommands.get_help_for_stage(stage, exam)
        
        # For other system commands, find appropriate handler
        handler = self._find_handler(message, user_state)
        if handler:
            result = await handler.handle(user_phone, message, user_state)
            
            # Apply state updates
            state_updates = result.get('state_updates', {})
            if state_updates:
                self.state_manager.update_user_state(user_phone, state_updates)
            
            return result.get('response', 'Command processed.')
        
        return "Command not recognized. Send 'help' for available commands."
    
    async def _handle_llm_query(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> str:
        """Handle LLM queries with explicit triggers"""
        # Extract the actual query from the trigger
        query = SystemCommands.extract_llm_query(message)
        if not query:
            return "Please provide a question after the prefix. Example: 'ask: How do I improve my scores?'"
        
        # Find FAQ handler for LLM processing
        for handler in self.handlers:
            if isinstance(handler, SmartFAQHandler):
                result = await handler.handle(user_phone, query, user_state)
                return result.get('response', 'I could not process your question right now.')
        
        return "I could not process your question right now. Please try again or send 'help' for available commands."
    
    async def _handle_async_loading(self, user_phone: str, user_state: Dict[str, Any]) -> str:
        """Handle async question loading"""
        try:
            logger.info(f"🔄 ASYNC LOADING: Processing async loading for {user_phone}")
            
            # Find the exam handler
            exam_handler = None
            for handler in self.handlers:
                if isinstance(handler, PersonalizedExamTypeHandler):
                    exam_handler = handler
                    break
            
            if not exam_handler:
                logger.error(f"❌ ASYNC LOADING ERROR: No exam handler found for {user_phone}")
                return "Sorry, there was an error loading questions. Please try again."
            
            # Perform async loading
            result = await exam_handler.handle_async_loading(user_phone, user_state)
            
            # Apply state updates if result is a dict
            if isinstance(result, dict):
                state_updates = result.get('state_updates', {})
                if state_updates:
                    logger.info(f"Applying async loading state updates for {user_phone}: {list(state_updates.keys())}")
                    self.state_manager.update_user_state(user_phone, state_updates)
                
                response = result.get('response', 'Questions loaded successfully!')
            else:
                response = result
            
            logger.info(f"✅ ASYNC LOADING COMPLETE: Loaded questions for {user_phone}")
            return response
            
        except Exception as e:
            logger.error(f"❌ ASYNC LOADING FAILED: Error in async loading for {user_phone}: {str(e)}", exc_info=True)
            
            # Reset to practice option selection on error
            self.state_manager.update_user_state(user_phone, {'stage': 'selecting_practice_option'})
            
            return "Sorry, there was an error loading questions. Please try selecting another option."
    
    def _find_handler(self, message: str, user_state: Dict[str, Any]) -> Optional:
        """Find the appropriate handler for the message"""
        for handler in self.handlers:
            try:
                if handler.can_handle(message, user_state):
                    return handler
            except Exception as e:
                logger.error(f"Error checking enhanced handler {handler.__class__.__name__}: {e}")
                continue
        
        return None