from typing import Dict, Any
import time
import logging

logger = logging.getLogger(__name__)

class UserStateManager:
    """
    Manages user session state in memory with improved persistence and validation
    """
    
    def __init__(self):
        self.user_states: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 3600  # 1 hour timeout
    
    def get_user_state(self, user_phone: str) -> Dict[str, Any]:
        """
        Get user's current state, creating a new one ONLY if doesn't exist
        """
        # Clean up expired sessions first
        self._cleanup_expired_sessions()
        
        current_state = self.user_states.get(user_phone)
        
        # Only create new state if user doesn't exist
        if current_state is None:
            logger.info(f"Creating new state for user {user_phone}")
            current_state = self._create_initial_state()
            self.user_states[user_phone] = current_state
        else:
            # Update last activity without changing other state
            current_state['last_activity'] = time.time()
            logger.info(f"Retrieved existing state for {user_phone}: {current_state}")
        
        return current_state.copy()  # Return a copy to prevent accidental direct modifications
    
    def update_user_state(self, user_phone: str, updates: Dict[str, Any]) -> None:
        """
        Update user's state with new values, ensuring state consistency
        """
        if not isinstance(updates, dict):
            logger.error(f"Invalid state update for {user_phone}: updates must be a dictionary")
            return
            
        # Get existing state or create new one
        current_state = self.user_states.get(user_phone)
        if current_state is None:
            current_state = self._create_initial_state()
            self.user_states[user_phone] = current_state
        
        # Store old values for logging
        old_stage = current_state.get('stage', 'unknown')
        old_exam = current_state.get('exam')
        
        # Update timestamp first to prevent expiration during update
        updates['last_activity'] = time.time()
        
        # Update state
        current_state.update(updates)
        
        # Log state changes
        new_stage = current_state.get('stage', 'unknown')
        new_exam = current_state.get('exam')
        
        logger.info(f"State update for {user_phone}:")
        if old_stage != new_stage:
            logger.info(f"Stage changed: {old_stage} -> {new_stage}")
        if old_exam != new_exam:
            logger.info(f"Exam changed: {old_exam} -> {new_exam}")
        logger.info(f"Full state after update: {current_state}")
    
    def reset_user_state(self, user_phone: str) -> None:
        """
        Reset user's state to initial values
        """
        logger.info(f"Resetting state for user {user_phone}")
        initial_state = self._create_initial_state()
        self.user_states[user_phone] = initial_state
        logger.info(f"State reset complete. New state: {initial_state}")
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """
        Create initial state for a new user with mandatory fields
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
        return initial_state.copy()  # Return a copy to ensure each user gets a fresh state
    
    def _cleanup_expired_sessions(self) -> None:
        """
        Remove expired user sessions and log removals
        """
        current_time = time.time()
        expired_users = [
            user_phone for user_phone, state in self.user_states.items()
            if current_time - state.get('last_activity', 0) > self.session_timeout
        ]
        
        for user_phone in expired_users:
            expired_state = self.user_states[user_phone]
            logger.info(f"Removing expired session for {user_phone}. Last state: {expired_state}")
            del self.user_states[user_phone]
            
        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired sessions")
    
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