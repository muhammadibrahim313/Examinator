"""
Comprehensive test to verify WhatsApp bot functionality
"""
import sys
import os
import asyncio
from unittest.mock import AsyncMock, patch

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.enhanced_smart_processor import EnhancedSmartMessageProcessor
from services.enhanced_state import EnhancedUserStateManager
from services.exam_registry import ExamRegistry

async def test_bot_functionality():
    """Test comprehensive bot functionality"""
    print("🧪 Testing WhatsApp Bot Comprehensive Functionality...")
    
    # Initialize components
    state_manager = EnhancedUserStateManager()
    exam_registry = ExamRegistry()
    processor = EnhancedSmartMessageProcessor(state_manager, exam_registry)
    test_user = "+1234567890"
    
    # Test 1: Basic Greetings
    print("\n📱 Test 1: Basic Greetings")
    greeting_tests = ["hello", "hi", "good morning", "hey there", "sup"]
    
    for greeting in greeting_tests:
        try:
            response = await processor.process_message(test_user, greeting)
            word_count = len(response.split())
            print(f"   '{greeting}' -> {response[:60]}... ({word_count} words)")
            print(f"   ✅ Under 50 words: {word_count <= 50}")
        except Exception as e:
            print(f"   ❌ Error with '{greeting}': {e}")
    
    # Test 2: Bot Commands
    print("\n🤖 Test 2: Bot Commands")
    commands = ["start", "restart", "help", "exit"]
    
    for command in commands:
        try:
            response = await processor.process_message(test_user, command)
            word_count = len(response.split())
            print(f"   '{command}' -> {response[:60]}... ({word_count} words)")
            print(f"   ✅ Under 50 words: {word_count <= 50}")
        except Exception as e:
            print(f"   ❌ Error with '{command}': {e}")
    
    # Test 3: Exam Selection Flow
    print("\n📚 Test 3: Exam Selection Flow")
    exam_queries = [
        "I want to practice JAMB",
        "Can you help me with SAT?",
        "NEET preparation please",
        "1",  # Selecting option 1
        "jamb"
    ]
    
    for query in exam_queries:
        try:
            response = await processor.process_message(test_user, query)
            word_count = len(response.split())
            print(f"   '{query}' -> {response[:60]}... ({word_count} words)")
            print(f"   ✅ Under 50 words: {word_count <= 50}")
        except Exception as e:
            print(f"   ❌ Error with '{query}': {e}")
    
    # Test 4: General Study Queries
    print("\n📖 Test 4: General Study Queries")
    study_queries = [
        "How do I improve my math scores?",
        "What are the best study techniques?",
        "I'm struggling with physics",
        "Can you give me study tips?",
        "How to prepare for exams effectively?"
    ]
    
    for query in study_queries:
        try:
            response = await processor.process_message(test_user, query)
            word_count = len(response.split())
            print(f"   '{query}' -> {response[:60]}... ({word_count} words)")
            print(f"   ✅ Under 50 words: {word_count <= 50}")
        except Exception as e:
            print(f"   ❌ Error with '{query}': {e}")
    
    # Test 5: Question Answering Simulation
    print("\n❓ Test 5: Question Answering Simulation")
    
    # Set up a mock exam session
    state = EnhancedUserStateManager()
    state.update_user_state(test_user, {"exam": "jamb", "subject": "mathematics"})
    
    answer_queries = ["A", "B", "C", "D", "next", "explain"]
    
    for query in answer_queries:
        try:
            response = await processor.process_message(test_user, query)
            word_count = len(response.split())
            print(f"   '{query}' -> {response[:60]}... ({word_count} words)")
            print(f"   ✅ Under 50 words: {word_count <= 50}")
        except Exception as e:
            print(f"   ❌ Error with '{query}': {e}")
    
    # Test 6: Error Handling
    print("\n⚠️ Test 6: Error Handling")
    error_queries = [
        "",  # Empty message
        "asdfghjkl",  # Random text
        "🤔🤔🤔",  # Only emojis
        "123456789",  # Only numbers
    ]
    
    for query in error_queries:
        try:
            response = await processor.process_message(test_user, query)
            word_count = len(response.split())
            print(f"   '{query or 'empty'}' -> {response[:60]}... ({word_count} words)")
            print(f"   ✅ Under 50 words: {word_count <= 50}")
            print(f"   ✅ No error messages: {'error' not in response.lower()}")
        except Exception as e:
            print(f"   ❌ Error with '{query or 'empty'}': {e}")
    
    # Test 7: Context Awareness
    print("\n🧠 Test 7: Context Awareness")
    
    # Set exam context
    state.update_user_state(test_user, {"subject": "physics", "score": 5, "total_questions": 10})
    
    context_queries = [
        "How am I doing?",
        "What should I focus on?",
        "I need help",
        "Give me advice"
    ]
    
    for query in context_queries:
        try:
            response = await processor.process_message(test_user, query)
            word_count = len(response.split())
            print(f"   '{query}' -> {response[:60]}... ({word_count} words)")
            print(f"   ✅ Under 50 words: {word_count <= 50}")
            print(f"   ✅ Context-aware: {'physics' in response.lower() or 'score' in response.lower()}")
        except Exception as e:
            print(f"   ❌ Error with '{query}': {e}")
    
    # Test 8: Performance Summary
    print("\n📊 Test 8: Performance & Analytics")
    performance_queries = [
        "show my stats",
        "how many questions have I answered?",
        "what's my accuracy?",
        "performance summary"
    ]
    
    for query in performance_queries:
        try:
            response = await processor.process_message(test_user, query)
            word_count = len(response.split())
            print(f"   '{query}' -> {response[:60]}... ({word_count} words)")
            print(f"   ✅ Under 50 words: {word_count <= 50}")
        except Exception as e:
            print(f"   ❌ Error with '{query}': {e}")
    
    print("\n✅ Comprehensive Bot Functionality Tests Completed!")
    print("\n📋 Summary:")
    print("   - All responses should be under 50 words")
    print("   - Greetings should be friendly and helpful")
    print("   - Commands should work properly")
    print("   - Exam flow should be smooth")
    print("   - Error handling should be graceful")
    print("   - Context awareness should be maintained")

if __name__ == "__main__":
    asyncio.run(test_bot_functionality()) 