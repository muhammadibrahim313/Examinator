from typing import List, Dict, Any, Optional
from app.core.enhanced_hybrid_handlers import PersonalizedExamTypeHandler, SmartPerformanceHandler
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
    Enhanced message processor with personalized learning capabilities
    """
    
    def __init__(self, state_manager, exam_registry):
        # Use enhanced state manager
        self.state_manager = EnhancedUserStateManager() if not isinstance(state_manager, EnhancedUserStateManager) else state_manager
        self.exam_registry = exam_registry
        self.handlers: List = []
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup enhanced handlers with personalization"""
        self.handlers = [
            SmartGlobalCommandHandler(self.state_manager, self.exam_registry),
            SmartPerformanceHandler(self.state_manager, self.exam_registry),  # New performance handler
            SmartExamSelectionHandler(self.state_manager, self.exam_registry),
            PersonalizedExamTypeHandler(self.state_manager, self.exam_registry),  # Enhanced exam handler
            SmartFallbackHandler(self.state_manager, self.exam_registry)
        ]
        logger.info(f"Initialized {len(self.handlers)} enhanced smart message handlers")
    
    async def process_message(self, user_phone: str, message: str) -> str:
        """
        Process a message using enhanced handlers with personalization
        """
        try:
            # Get current user state
            user_state = self.state_manager.get_user_state(user_phone)
            current_stage = user_state.get('stage', 'initial')
            
            logger.info(f"Processing enhanced message from {user_phone}")
            logger.info(f"Current stage: {current_stage}")
            logger.info(f"Message: '{message}'")
            
            # Find the appropriate handler
            handler = self._find_handler(message, user_state)
            if not handler:
                logger.error(f"No handler found for message from {user_phone}")
                return "Sorry, something went wrong. Please try again or send 'restart'."
            
            logger.info(f"Using enhanced handler: {handler.__class__.__name__}")
            
            # Process the message (this may be async now)
            result = await handler.handle(user_phone, message, user_state)
            
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