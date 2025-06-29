from typing import List, Dict, Any, Optional
from app.core.hybrid_message_handler import (
    HybridMessageHandler,
    SmartGlobalCommandHandler,
    SmartExamSelectionHandler, 
    SmartExamTypeHandler,
    SmartFallbackHandler
)
import logging
import asyncio

logger = logging.getLogger(__name__)

class SmartMessageProcessor:
    """
    Enhanced message processor that uses hybrid handlers with LLM capabilities
    """
    
    def __init__(self, state_manager, exam_registry):
        self.state_manager = state_manager
        self.exam_registry = exam_registry
        self.handlers: List[HybridMessageHandler] = []
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup hybrid message handlers in priority order"""
        self.handlers = [
            SmartGlobalCommandHandler(self.state_manager, self.exam_registry),
            SmartExamSelectionHandler(self.state_manager, self.exam_registry),
            SmartExamTypeHandler(self.state_manager, self.exam_registry),
            SmartFallbackHandler(self.state_manager, self.exam_registry)  # Always last
        ]
        logger.info(f"Initialized {len(self.handlers)} smart message handlers")
    
    async def process_message(self, user_phone: str, message: str) -> str:
        """
        Process a message using smart handlers with LLM capabilities
        """
        try:
            # Get current user state
            user_state = self.state_manager.get_user_state(user_phone)
            current_stage = user_state.get('stage', 'initial')
            
            logger.info(f"Processing smart message from {user_phone}")
            logger.info(f"Current stage: {current_stage}")
            logger.info(f"Message: '{message}'")
            
            # Find the appropriate handler
            handler = self._find_handler(message, user_state)
            if not handler:
                logger.error(f"No handler found for message from {user_phone}")
                return "Sorry, something went wrong. Please try again or send 'restart'."
            
            logger.info(f"Using handler: {handler.__class__.__name__}")
            
            # Process the message (this may be async now)
            result = await handler.handle(user_phone, message, user_state)
            
            # Apply state updates if any
            state_updates = result.get('state_updates', {})
            if state_updates:
                logger.info(f"Applying state updates for {user_phone}: {state_updates}")
                self.state_manager.update_user_state(user_phone, state_updates)
            
            # Log the result
            response = result.get('response', 'No response generated.')
            next_handler = result.get('next_handler')
            
            logger.info(f"Handler result for {user_phone}:")
            logger.info(f"Response: {response[:100]}...")
            logger.info(f"Next handler: {next_handler}")
            
            # Get updated state for verification
            updated_state = self.state_manager.get_user_state(user_phone)
            logger.info(f"Final state for {user_phone}: stage={updated_state.get('stage')}, exam={updated_state.get('exam')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing smart message from {user_phone}: {str(e)}", exc_info=True)
            return "Sorry, something went wrong. Please try again or send 'restart' to start over."
    
    def _find_handler(self, message: str, user_state: Dict[str, Any]) -> Optional[HybridMessageHandler]:
        """
        Find the appropriate handler for the message
        """
        for handler in self.handlers:
            try:
                if handler.can_handle(message, user_state):
                    return handler
            except Exception as e:
                logger.error(f"Error checking handler {handler.__class__.__name__}: {e}")
                continue
        
        return None