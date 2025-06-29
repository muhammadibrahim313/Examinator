import os
import asyncio
import logging
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage
from app.agent_reflection.RAG_reflection import agent, hybrid_manager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMAgentService:
    """
    Service to handle LLM agent interactions for the WhatsApp bot
    """
    
    def __init__(self):
        self.agent = agent
        self.config = {"recursion_limit": 50}
        self._validate_environment()
    
    def _validate_environment(self):
        """Validate that required environment variables are set"""
        required_vars = ['GOOGLE_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
            logger.warning("LLM agent may not function properly without these variables")
    
    async def process_message(self, user_phone: str, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a message using the LLM agent
        
        Args:
            user_phone: User's phone number
            message: User's message
            context: Optional context about the user's exam session
            
        Returns:
            Agent's response
        """
        try:
            logger.info(f"Processing LLM message from {user_phone}: {message}")
            
            # Enhance the message with context if available
            enhanced_message = self._enhance_message_with_context(message, context)
            
            # Create the input for the agent
            agent_input = {"messages": [HumanMessage(content=enhanced_message)]}
            
            # Process with the agent
            response_chunks = []
            async for chunk in self.agent.astream(agent_input, config=self.config):
                if 'messages' in chunk:
                    for msg in chunk['messages']:
                        if hasattr(msg, 'content') and msg.content:
                            response_chunks.append(msg.content)
                            logger.debug(f"Agent chunk: {msg.content[:100]}...")
            
            # Combine all response chunks
            full_response = '\n'.join(response_chunks) if response_chunks else "I'm sorry, I couldn't process your request right now."
            
            # Clean and format the response for WhatsApp
            formatted_response = self._format_response_for_whatsapp(full_response)
            
            logger.info(f"LLM response for {user_phone}: {formatted_response[:100]}...")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error processing LLM message from {user_phone}: {str(e)}", exc_info=True)
            
            # Check hybrid model status for better error messages
            stats = hybrid_manager.get_stats()
            
            # Provide more helpful error responses based on the context
            if "hello" in message.lower() or "hi" in message.lower():
                return "Hello! 👋 I'm your Exam Practice Bot. Send 'start' to begin practicing for exams!"
            elif context and context.get('exam'):
                exam_name = context.get('exam', '').upper()
                return f"I'm having trouble processing that request. You're practicing for {exam_name}. Send 'restart' to start over or try a different question."
            else:
                return "I'm having a technical issue right now. Please send 'start' to begin exam practice or try again in a moment."
    
    def _enhance_message_with_context(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """
        Enhance the user message with exam context and word limit enforcement
        """
        # Base system prompt with word limit
        system_prompt = """
You are a helpful exam practice assistant.

CRITICAL RESPONSE RULES:
- MAXIMUM 50 WORDS per response
- Be direct and helpful
- Use 1-2 emojis if appropriate 
- Keep responses brief and actionable
- Focus on exam practice for JAMB, SAT, NEET

WORD LIMIT: Your response must be under 50 words total!
"""
        
        if not context:
            return f"{system_prompt}\n\nUser message: {message}"
        
        # Add exam context to help the agent understand the user's situation
        context_parts = []
        
        if context.get('exam'):
            context_parts.append(f"User is practicing for {context['exam'].upper()} exam")
        
        if context.get('subject'):
            context_parts.append(f"Subject: {context['subject']}")
        
        if context.get('year'):
            context_parts.append(f"Year: {context['year']}")
        
        if context.get('current_question_index') is not None and context.get('total_questions'):
            current = context['current_question_index'] + 1
            total = context['total_questions']
            context_parts.append(f"Currently on question {current} of {total}")
        
        if context.get('score') is not None:
            context_parts.append(f"Current score: {context['score']}")
        
        # Special handling for greetings
        if context.get('is_greeting'):
            context_parts.append(f"GREETING: {context.get('greeting_context', 'General greeting')}")
        
        if context_parts:
            context_info = " | ".join(context_parts)
            enhanced_message = f"{system_prompt}\n\n[EXAM CONTEXT: {context_info}]\n\nUser message: {message}"
            return enhanced_message
        
        return f"{system_prompt}\n\nUser message: {message}"
    
    def _format_response_for_whatsapp(self, response: str) -> str:
        """
        Format the agent response for WhatsApp delivery with 50-word limit
        """
        # Remove excessive formatting that doesn't work well in WhatsApp
        formatted = response.strip()
        
        # Clean up any problematic characters or formatting
        formatted = formatted.replace('```', '').replace('**', '*')
        
        # Enforce 50-word limit
        formatted = self._enforce_word_limit(formatted, 50)
        
        return formatted
    
    def _enforce_word_limit(self, text: str, max_words: int) -> str:
        """
        Enforce word limit on response text
        """
        words = text.split()
        word_count = len(words)
        
        if word_count <= max_words:
            return text
        
        # Truncate to word limit and add indicator
        truncated_words = words[:max_words-2]  # Save space for "..."
        truncated_text = ' '.join(truncated_words) + "..."
        
        logger.info(f"Response truncated from {word_count} to {len(truncated_words)} words")
        return truncated_text
    
    def _count_words(self, text: str) -> int:
        """
        Count words in text (excluding emojis)
        """
        # Remove emojis and special characters for accurate word count
        import re
        clean_text = re.sub(r'[^\w\s]', ' ', text)
        words = clean_text.split()
        return len(words)
    
    def is_exam_related_query(self, message: str) -> bool:
        """
        Check if the message is related to exam practice
        """
        exam_keywords = [
            'exam', 'test', 'question', 'answer', 'jamb', 'sat', 'waec',
            'biology', 'chemistry', 'physics', 'math', 'english',
            'practice', 'study', 'score', 'result'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in exam_keywords)