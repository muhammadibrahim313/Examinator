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
from app.services.enhanced_state import EnhancedUserStateManager
import logging
import asyncio

logger = logging.getLogger(__name__)

class EnhancedSmartMessageProcessor:
    """
    Enhanced message processor with strict input validation and comprehensive features
    """
    
    def __init__(self, state_manager, exam_registry):
        # Use enhanced state manager
        self.state_manager = EnhancedUserStateManager() if not isinstance(state_manager, EnhancedUserStateManager) else state_manager
        self.exam_registry = exam_registry
        self.handlers: List = []
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup enhanced handlers with strict validation and FAQ support"""
        self.handlers = [
            SmartGlobalCommandHandler(self.state_manager, self.exam_registry),
            SmartFAQHandler(self.state_manager, self.exam_registry),  # FAQ handler for help queries
            SmartPerformanceHandler(self.state_manager, self.exam_registry),
            SmartExamSelectionHandler(self.state_manager, self.exam_registry),  # FIXED: Strict validation
            PersonalizedExamTypeHandler(self.state_manager, self.exam_registry),  # Enhanced with navigation
            SmartFallbackHandler(self.state_manager, self.exam_registry)
        ]
        logger.info(f"Initialized {len(self.handlers)} enhanced smart message handlers with strict validation")
    
    async def process_message(self, user_phone: str, message: str) -> str:
        """
        Process a message using enhanced handlers with strict validation and comprehensive features
        FIXED: Handle async loading immediately within the same request-response cycle
        """
        try:
            # Get current user state
            user_state = self.state_manager.get_user_state(user_phone)
            current_stage = user_state.get('stage', 'initial')
            
            logger.info(f"Processing enhanced message from {user_phone}")
            logger.info(f"Current stage: {current_stage}")
            logger.info(f"Message: '{message}'")
            
            # Handle async loading stage
            if current_stage == 'async_loading':
                return await self._handle_async_loading(user_phone, user_state)
            
            # Find the appropriate handler
            handler = self._find_handler(message, user_state)
            if not handler:
                logger.error(f"No handler found for message from {user_phone}")
                return "Sorry, something went wrong. Please try again or send 'restart'."
            
            logger.info(f"Using enhanced handler: {handler.__class__.__name__}")
            
            # Process the message (this may be async now)
            result = await handler.handle(user_phone, message, user_state)
            
            # FIXED: Check if async loading is needed and handle it immediately
            if result.get('async_task') == 'load_questions':
                logger.info(f"🔄 IMMEDIATE ASYNC LOADING: Processing async loading for {user_phone} in same request")
                
                # Apply state updates first
                state_updates = result.get('state_updates', {})
                if state_updates:
                    self.state_manager.update_user_state(user_phone, state_updates)
                
                # Perform async loading immediately and return the final result
                loading_result = await self._handle_async_loading(user_phone, self.state_manager.get_user_state(user_phone))
                
                # Apply any additional state updates from loading
                loading_state_updates = loading_result.get('state_updates', {})
                if loading_state_updates:
                    self.state_manager.update_user_state(user_phone, loading_state_updates)
                
                # Return the final response (first question)
                final_response = loading_result.get('response', 'Questions loaded successfully!')
                logger.info(f"✅ IMMEDIATE ASYNC COMPLETE: Returning final response for {user_phone}")
                return final_response
            
            # Apply state updates if any
            state_updates = result.get('state_updates', {})
            if state_updates:
                logger.info(f"Applying enhanced state updates for {user_phone}: {list(state_updates.keys())}")
                self.state_manager.update_user_state(user_phone, state_updates)
            
            # Log the result
            response = result.get('response', 'No response generated.')
            next_handler = result.get('next_handler')
            
            logger.info(f"Enhanced handler result for {user_phone}:")
            logger.info(f"Response length: {len(response)} characters")
            logger.info(f"Next handler: {next_handler}")
            
            # Get updated state for verification
            updated_state = self.state_manager.get_user_state(user_phone)
            logger.info(f"Final enhanced state for {user_phone}: stage={updated_state.get('stage')}, exam={updated_state.get('exam')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing enhanced message from {user_phone}: {str(e)}", exc_info=True)
            return "Sorry, something went wrong. Please try again or send 'restart' to start over."
    
    async def _handle_async_loading(self, user_phone: str, user_state: Dict[str, Any]) -> Dict[str, str]:
        """
        Handle async question loading
        FIXED: Return dict with response and state_updates for consistency
        """
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
                return {
                    'response': "Sorry, there was an error loading questions. Please try again.",
                    'state_updates': {'stage': 'selecting_practice_option'}
                }
            
            # Perform async loading
            result = await exam_handler.handle_async_loading(user_phone, user_state)
            
            logger.info(f"✅ ASYNC LOADING COMPLETE: Loaded questions for {user_phone}")
            return result
            
        except Exception as e:
            logger.error(f"❌ ASYNC LOADING FAILED: Error in async loading for {user_phone}: {str(e)}", exc_info=True)
            
            return {
                'response': "Sorry, there was an error loading questions. Please try selecting another option.",
                'state_updates': {'stage': 'selecting_practice_option'}
            }
    
    def _find_handler(self, message: str, user_state: Dict[str, Any]) -> Optional:
        """
        Find the appropriate handler for the message
        """
        for handler in self.handlers:
            try:
                if handler.can_handle(message, user_state):
                    return handler
            except Exception as e:
                logger.error(f"Error checking enhanced handler {handler.__class__.__name__}: {e}")
                continue
        
        return None