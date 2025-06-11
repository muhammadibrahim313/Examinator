from typing import Dict, Any
import time
import logging

logger = logging.getLogger(__name__)

class UserStateManager:
    """
    Manages user session state in memory
    """
    
    def __init__(self):
        self.user_states: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 3600  # 1 hour timeout
    
    def get_user_state(self, user_phone: str) -> Dict[str, Any]:
        """
        Get user's current state, creating a new one if doesn't exist
        """
        # Clean up expired sessions first
        self._cleanup_expired_sessions()
        
        # If user doesn't exist, create new state
        if user_phone not in self.user_states:
            logger.info(f"Creating new state for user {user_phone}")
            self.user_states[user_phone] = self._create_initial_state()
        
        # Update last activity timestamp
        self.user_states[user_phone]['last_activity'] = time.time()
        
        # Log current state for debugging
        current_stage = self.user_states[user_phone].get('stage', 'unknown')
        logger.info(f"Retrieved state for {user_phone}: stage={current_stage}")
        
        # Return the existing state (not a copy)
        return self.user_states[user_phone]
    
    def update_user_state(self, user_phone: str, updates: Dict[str, Any]) -> None:
        """
        Update user's state with new values
        """
        # Ensure user state exists
        if user_phone not in self.user_states:
            logger.info(f"Creating new state for user {user_phone} during update")
            self.user_states[user_phone] = self._create_initial_state()
        
        # Store old state for logging
        old_stage = self.user_states[user_phone].get('stage', 'unknown')
        
        # Apply updates
        self.user_states[user_phone].update(updates)
        self.user_states[user_phone]['last_activity'] = time.time()
        
        # Log state transition
        new_stage = self.user_states[user_phone].get('stage', 'unknown')
        logger.info(f"State updated for {user_phone}: {old_stage} -> {new_stage}")
        logger.info(f"Full updated state: {self.user_states[user_phone]}")
    
    def reset_user_state(self, user_phone: str) -> None:
        """
        Reset user's state to initial values
        """
        logger.info(f"Resetting state for user {user_phone}")
        self.user_states[user_phone] = self._create_initial_state()
        logger.info(f"State reset complete for {user_phone}")
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """
        Create initial state for a new user
        """
        initial_state = {
            'stage': 'initial',
            'exam': None,
            'subject': None,
            'year': None,
            'section': None,  # For SAT
            'difficulty': None,  # For SAT
            'current_question_index': 0,
            'score': 0,
            'total_questions': 0,
            'questions': [],
            'last_activity': time.time()
        }
        logger.info(f"Created initial state: {initial_state}")
        return initial_state
    
    def _cleanup_expired_sessions(self) -> None:
        """
        Remove expired user sessions
        """
        current_time = time.time()
        expired_users = [
            user_phone for user_phone, state in self.user_states.items()
            if current_time - state.get('last_activity', 0) > self.session_timeout
        ]
        
        for user_phone in expired_users:
            logger.info(f"Removing expired session for user {user_phone}")
            del self.user_states[user_phone]
    
    def get_all_active_users(self) -> int:
        """
        Get count of active users
        """
        self._cleanup_expired_sessions()
        return len(self.user_states)
    
    def debug_user_state(self, user_phone: str) -> Dict[str, Any]:
        """
        Get user state for debugging purposes
        """
        return self.user_states.get(user_phone, {})