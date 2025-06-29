#!/usr/bin/env python3
"""
Quick test to verify greeting handling is fixed
"""

import asyncio
from app.services.enhanced_state import EnhancedUserStateManager
from app.services.exam_registry import ExamRegistry
from app.core.enhanced_smart_processor import EnhancedSmartMessageProcessor

async def test_greetings():
    """Test various greeting messages"""
    print("🧪 TESTING GREETING HANDLING FIX")
    print("=" * 50)
    
    # Initialize components
    state_manager = EnhancedUserStateManager()
    exam_registry = ExamRegistry()
    processor = EnhancedSmartMessageProcessor(state_manager, exam_registry)
    
    # Test phone number
    test_phone = "1234567890"
    
    # Test greetings that were causing errors
    test_greetings = [
        "hello",
        "hi", 
        "hey",
        "good morning",
        "Hello there",
        "Hi!",
        "sup",
        "wassup"
    ]
    
    print("Testing greetings that previously caused errors...")
    
    for i, greeting in enumerate(test_greetings, 1):
        print(f"\n🧪 Test {i}: '{greeting}'")
        try:
            response = await processor.process_message(test_phone, greeting)
            
            # Check if we get the error message
            if "I'm sorry, I encountered an error" in response:
                print(f"❌ STILL GETTING ERROR: {response}")
            elif "Hello" in response or "Hi" in response or "👋" in response:
                print(f"✅ FIXED: {response[:100]}...")
            else:
                print(f"⚠️ UNEXPECTED: {response[:100]}...")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
    
    # Test one normal flow to make sure we didn't break anything
    print(f"\n🧪 Testing normal flow with 'start':")
    try:
        response = await processor.process_message(test_phone, "start")
        if "Welcome" in response and "exam" in response:
            print(f"✅ NORMAL FLOW WORKS: {response[:100]}...")
        else:
            print(f"⚠️ NORMAL FLOW ISSUE: {response[:100]}...")
    except Exception as e:
        print(f"❌ NORMAL FLOW EXCEPTION: {str(e)}")
    
    print(f"\n🎯 GREETING TEST COMPLETE")

async def main():
    await test_greetings()

if __name__ == "__main__":
    asyncio.run(main()) 