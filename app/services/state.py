from typing import Dict, Any
import time
import logging

logger = logging.getLogger(__name__)

class UserStateManager:
    """
    Clean, simple state management with clear responsibilities
    """
    
    def __init__(self):
        self.user_states: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 3600  # 1 hour timeout
    
    def get_user_state(self, user_phone: str) -> Dict[str, Any]:
        """
        Get user's current state, creating initial state if needed
        """
        self._cleanup_expired_sessions()
        
        if user_phone not in self.user_states:
            logger.info(f"Creating new state for user {user_phone}")
            self.user_states[user_phone] = self._create_initial_state()
        
        # Update last activity
        self.user_states[user_phone]['last_activity'] = time.time()
        
        # Return a copy to prevent accidental modifications
        return self.user_states[user_phone].copy()
    
    def update_user_state(self, user_phone: str, updates: Dict[str, Any]) -> None:
        """
        Update user's state with new values
        """
        if not isinstance(updates, dict):
            logger.error(f"Invalid state update for {user_phone}: updates must be a dictionary")
            return
        
        # Ensure user exists
        if user_phone not in self.user_states:
            logger.info(f"Creating state for {user_phone} during update")
            self.user_states[user_phone] = self._create_initial_state()
        
        # Log changes
        old_state = self.user_states[user_phone].copy()
        
        # Apply updates
        self.user_states[user_phone].update(updates)
        self.user_states[user_phone]['last_activity'] = time.time()
        
        # Log what changed
        new_state = self.user_states[user_phone]
        self._log_state_changes(user_phone, old_state, new_state)
    
    def reset_user_state(self, user_phone: str) -> None:
        """
        Reset user's state to initial values
        """
        logger.info(f"Resetting state for user {user_phone}")
        self.user_states[user_phone] = self._create_initial_state()
        logger.info(f"State reset complete for {user_phone}")
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """
        Create clean initial state
        """
        return {
            'stage': 'initial',
            'exam': None,
            'subject': None,
            'year': None,
            'section': None,
            'difficulty': None,
            'current_question_index': 0,
            'score': 0,
            'total_questions': 0,
            'questions': [],
            'last_activity': time.time()
        }
    
    def _log_state_changes(self, user_phone: str, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        """
        Log meaningful state changes
        """
        changes = []
        
        # Check important fields for changes
        important_fields = ['stage', 'exam', 'subject', 'year', 'section', 'difficulty', 'score']
        
        for field in important_fields:
            old_value = old_state.get(field)
            new_value = new_state.get(field)
            if old_value != new_value:
                changes.append(f"{field}: {old_value} -> {new_value}")
        
        if changes:
            logger.info(f"State changes for {user_phone}: {', '.join(changes)}")
        else:
            logger.debug(f"No significant state changes for {user_phone}")
    
    def _cleanup_expired_sessions(self) -> None:
        """
        Remove expired sessions
        """
        current_time = time.time()
        expired_users = [
            user_phone for user_phone, state in self.user_states.items()
            if current_time - state.get('last_activity', 0) > self.session_timeout
        ]
        
        for user_phone in expired_users:
            logger.info(f"Removing expired session for {user_phone}")
            del self.user_states[user_phone]
    
    def get_all_active_users(self) -> int:
        """Get count of active users"""
        self._cleanup_expired_sessions()
        return len(self.user_states)