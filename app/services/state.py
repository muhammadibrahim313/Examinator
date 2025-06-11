from typing import Dict, Any
import time

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
        # Clean up expired sessions
        self._cleanup_expired_sessions()
        
        if user_phone not in self.user_states:
            self.user_states[user_phone] = self._create_initial_state()
        
        # Update last activity
        self.user_states[user_phone]['last_activity'] = time.time()
        
        return self.user_states[user_phone]
    
    def update_user_state(self, user_phone: str, updates: Dict[str, Any]) -> None:
        """
        Update user's state with new values
        """
        if user_phone not in self.user_states:
            self.user_states[user_phone] = self._create_initial_state()
        
        self.user_states[user_phone].update(updates)
        self.user_states[user_phone]['last_activity'] = time.time()
    
    def reset_user_state(self, user_phone: str) -> None:
        """
        Reset user's state to initial values
        """
        self.user_states[user_phone] = self._create_initial_state()
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """
        Create initial state for a new user
        """
        return {
            'stage': 'initial',  # initial, selecting_exam, selecting_subject, selecting_year, taking_exam
            'exam': None,
            'subject': None,
            'year': None,
            'current_question_index': 0,
            'score': 0,
            'total_questions': 0,
            'questions': [],
            'last_activity': time.time()
        }
    
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
            del self.user_states[user_phone]
    
    def get_all_active_users(self) -> int:
        """
        Get count of active users
        """
        self._cleanup_expired_sessions()
        return len(self.user_states)