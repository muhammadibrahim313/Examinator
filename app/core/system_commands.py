"""
System Commands Dictionary and Validation
Centralized command management to prevent LLM routing of system commands
"""

from typing import Dict, List, Set, Optional
from enum import Enum

class CommandType(Enum):
    NAVIGATION = "navigation"
    TEST_CONTROL = "test_control"
    HELP = "help"
    SYSTEM = "system"
    SELECTION = "selection"

class SystemCommands:
    """
    Centralized system commands dictionary with validation
    """
    
    # Core system commands that should NEVER go to LLM
    SYSTEM_COMMANDS: Dict[str, CommandType] = {
        # Navigation commands
        'back': CommandType.NAVIGATION,
        'previous': CommandType.NAVIGATION,
        'return': CommandType.NAVIGATION,
        'go back': CommandType.NAVIGATION,
        'menu': CommandType.NAVIGATION,
        
        # Test control commands
        'stop': CommandType.TEST_CONTROL,
        'quit': CommandType.TEST_CONTROL,
        'exit': CommandType.TEST_CONTROL,
        'submit': CommandType.TEST_CONTROL,
        'pause': CommandType.TEST_CONTROL,
        'end': CommandType.TEST_CONTROL,
        'finish': CommandType.TEST_CONTROL,
        
        # Help commands (structured responses only)
        'help': CommandType.HELP,
        'commands': CommandType.HELP,
        'options': CommandType.HELP,
        
        # System commands
        'start': CommandType.SYSTEM,
        'restart': CommandType.SYSTEM,
        'reset': CommandType.SYSTEM,
        'begin': CommandType.SYSTEM,
    }
    
    # FAQ and general queries that CAN go to LLM (with prefix)
    LLM_TRIGGERS: Set[str] = {
        'ask:', 'chat:', 'question:', 'explain:', 'help:', 'faq:', '?'
    }
    
    # Valid exam answers
    EXAM_ANSWERS: Set[str] = {'a', 'b', 'c', 'd'}
    
    @classmethod
    def is_system_command(cls, message: str) -> bool:
        """Check if message is a system command that should use structured logic"""
        message_clean = message.lower().strip()
        
        # Check exact matches
        if message_clean in cls.SYSTEM_COMMANDS:
            return True
        
        # Check for multi-word commands
        for command in cls.SYSTEM_COMMANDS:
            if ' ' in command and command in message_clean:
                return True
        
        return False
    
    @classmethod
    def is_llm_trigger(cls, message: str) -> bool:
        """Check if message has LLM trigger prefix"""
        message_clean = message.lower().strip()
        
        # Check for explicit LLM triggers
        for trigger in cls.LLM_TRIGGERS:
            if message_clean.startswith(trigger):
                return True
        
        return False
    
    @classmethod
    def is_valid_number_selection(cls, message: str, max_options: int) -> bool:
        """Check if message is a valid number selection"""
        try:
            choice = int(message.strip())
            return 1 <= choice <= max_options
        except ValueError:
            return False
    
    @classmethod
    def is_valid_exam_answer(cls, message: str) -> bool:
        """Check if message is a valid exam answer"""
        return message.lower().strip() in cls.EXAM_ANSWERS
    
    @classmethod
    def get_command_type(cls, message: str) -> Optional[CommandType]:
        """Get the type of system command"""
        message_clean = message.lower().strip()
        return cls.SYSTEM_COMMANDS.get(message_clean)
    
    @classmethod
    def extract_llm_query(cls, message: str) -> Optional[str]:
        """Extract the actual query from LLM trigger message"""
        message_clean = message.strip()
        
        for trigger in cls.LLM_TRIGGERS:
            if message_clean.lower().startswith(trigger):
                return message_clean[len(trigger):].strip()
        
        return None
    
    @classmethod
    def should_use_structured_logic(cls, message: str, stage: str, max_options: int = 0) -> bool:
        """
        Determine if message should use structured logic instead of LLM
        
        Args:
            message: User's message
            stage: Current user stage
            max_options: Maximum valid options for current stage
        
        Returns:
            True if should use structured logic, False if can use LLM
        """
        message_clean = message.strip()
        
        # 1. Always use structured logic for system commands
        if cls.is_system_command(message_clean):
            return True
        
        # 2. Always use structured logic for valid exam answers
        if stage == 'taking_exam' and cls.is_valid_exam_answer(message_clean):
            return True
        
        # 3. Always use structured logic for valid number selections
        if stage in ['selecting_exam', 'selecting_subject', 'selecting_practice_mode', 'selecting_practice_option'] and max_options > 0:
            if cls.is_valid_number_selection(message_clean, max_options):
                return True
        
        # 4. Use LLM only if explicit trigger is used
        if cls.is_llm_trigger(message_clean):
            return False
        
        # 5. Default to structured logic for short, simple inputs
        if len(message_clean) <= 3:
            return True
        
        # 6. Use structured logic for single words that might be commands
        if len(message_clean.split()) == 1 and len(message_clean) <= 10:
            return True
        
        # 7. Allow LLM for longer, complex queries
        return False
    
    @classmethod
    def get_help_for_stage(cls, stage: str, exam: str = None) -> str:
        """Get structured help response for current stage"""
        if stage == 'initial':
            return cls._get_initial_help()
        elif stage == 'selecting_exam':
            return cls._get_exam_selection_help()
        elif stage in ['selecting_subject', 'selecting_practice_mode', 'selecting_practice_option']:
            return cls._get_selection_help(stage, exam)
        elif stage == 'taking_exam':
            return cls._get_exam_help(exam)
        else:
            return cls._get_general_help()
    
    @classmethod
    def _get_initial_help(cls) -> str:
        return """🆘 **Help - Getting Started**

🔧 **Available Commands:**
• 'start' - Begin exam practice
• 'help' - Show this help

🎓 **Available Exams:** JAMB, SAT, NEET

💡 **To chat with AI:** Use prefixes like:
• 'ask: How do I improve my scores?'
• 'question: What study tips do you have?'
• 'explain: How does this work?'

Send 'start' to begin practicing!"""
    
    @classmethod
    def _get_exam_selection_help(cls) -> str:
        return """🆘 **Help - Exam Selection**

🔧 **Available Commands:**
• Numbers (1, 2, 3) - Select exam
• 'restart' - Start over
• 'help' - Show this help

🎓 **Available Exams:**
1. JAMB - Nigerian university entrance
2. SAT - US college entrance  
3. NEET - Indian medical entrance

💡 **To ask questions:** Use 'ask: your question'

Select a number to choose your exam!"""
    
    @classmethod
    def _get_selection_help(cls, stage: str, exam: str) -> str:
        stage_name = stage.replace('selecting_', '').replace('_', ' ').title()
        
        return f"""🆘 **Help - {stage_name} Selection**

🔧 **Available Commands:**
• Numbers - Select from options above
• 'back' - Go to previous step
• 'restart' - Start over completely
• 'help' - Show this help

🎓 **Current Exam:** {exam.upper() if exam else 'Not selected'}

💡 **To ask questions:** Use 'ask: your question'
💡 **For study tips:** Use 'question: study tips for {exam}'

Select a number from the options above!"""
    
    @classmethod
    def _get_exam_help(cls, exam: str) -> str:
        return f"""🆘 **Help - Taking {exam.upper()} Exam**

🔧 **Answer Commands:**
• A, B, C, D - Answer the question

🔧 **Test Control:**
• 'stop' - End test with summary
• 'submit' - Submit current progress
• 'pause' - Pause the test

🔧 **Help:**
• 'help' - Show this help

💡 **To ask about the question:** Use 'ask: explain this question'
💡 **For study tips:** Use 'question: study tips for this topic'

Answer with A, B, C, or D!"""
    
    @classmethod
    def _get_general_help(cls) -> str:
        return """🆘 **Help - General Commands**

🔧 **Navigation:**
• 'back' - Go to previous step
• 'restart' - Start over completely

🔧 **System:**
• 'start' - Begin new session
• 'help' - Show this help

💡 **To chat with AI:** Use prefixes:
• 'ask: your question'
• 'question: what you want to know'
• 'explain: topic you need help with'

Follow the instructions above or send 'start' to begin!"""

class InputValidator:
    """
    Enhanced input validation with helpful error messages
    """
    
    @staticmethod
    def validate_exam_selection(message: str, available_exams: List[str]) -> Dict[str, any]:
        """Validate exam selection input"""
        message_clean = message.strip()
        
        # Check if it's a system command first
        if SystemCommands.is_system_command(message_clean):
            return {'valid': True, 'type': 'system_command', 'value': message_clean}
        
        # Check if it's a valid number
        try:
            choice = int(message_clean)
            if 1 <= choice <= len(available_exams):
                return {'valid': True, 'type': 'selection', 'value': choice - 1}
            else:
                return {
                    'valid': False, 
                    'type': 'invalid_range',
                    'error': f"Invalid choice: {choice}. Please select 1-{len(available_exams)}.",
                    'help': f"Available exams:\n" + "\n".join([f"{i+1}. {exam.upper()}" for i, exam in enumerate(available_exams)])
                }
        except ValueError:
            # Not a number
            if message_clean.lower() in ['a', 'b', 'c', 'd']:
                return {
                    'valid': False,
                    'type': 'wrong_context',
                    'error': f"You sent '{message_clean.upper()}' but we're selecting an exam, not answering a question.",
                    'help': "Please enter a number to select an exam."
                }
            else:
                return {
                    'valid': False,
                    'type': 'invalid_format',
                    'error': f"'{message_clean}' is not a valid choice.",
                    'help': "Please enter a number to select an exam."
                }
    
    @staticmethod
    def validate_exam_answer(message: str) -> Dict[str, any]:
        """Validate exam answer input"""
        message_clean = message.strip()
        
        # Check if it's a system command first
        if SystemCommands.is_system_command(message_clean):
            return {'valid': True, 'type': 'system_command', 'value': message_clean}
        
        # Check if it's a valid answer
        if SystemCommands.is_valid_exam_answer(message_clean):
            return {'valid': True, 'type': 'answer', 'value': message_clean.lower()}
        
        # Invalid answer
        if message_clean.isdigit():
            return {
                'valid': False,
                'type': 'wrong_format',
                'error': f"You sent '{message_clean}' but please reply with A, B, C, or D.",
                'help': "Answer with A, B, C, or D for your choice."
            }
        else:
            return {
                'valid': False,
                'type': 'invalid_answer',
                'error': f"'{message_clean}' is not a valid answer.",
                'help': "Please reply with A, B, C, or D for your answer."
            }
    
    @staticmethod
    def validate_number_selection(message: str, max_options: int, context: str = "option") -> Dict[str, any]:
        """Validate number selection input"""
        message_clean = message.strip()
        
        # Check if it's a system command first
        if SystemCommands.is_system_command(message_clean):
            return {'valid': True, 'type': 'system_command', 'value': message_clean}
        
        # Check if it's a valid number
        try:
            choice = int(message_clean)
            if 1 <= choice <= max_options:
                return {'valid': True, 'type': 'selection', 'value': choice - 1}
            else:
                return {
                    'valid': False,
                    'type': 'invalid_range',
                    'error': f"Invalid choice: {choice}. Please select 1-{max_options}.",
                    'help': f"Select a number between 1 and {max_options} to choose your {context}."
                }
        except ValueError:
            # Not a number
            if message_clean.lower() in ['a', 'b', 'c', 'd']:
                return {
                    'valid': False,
                    'type': 'wrong_context',
                    'error': f"You sent '{message_clean.upper()}' but we're selecting a {context}, not answering a question.",
                    'help': f"Please enter a number to select your {context}."
                }
            else:
                return {
                    'valid': False,
                    'type': 'invalid_format',
                    'error': f"'{message_clean}' is not a valid choice.",
                    'help': f"Please enter a number to select your {context}."
                }