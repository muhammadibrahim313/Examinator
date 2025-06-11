from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from app.services.state import UserStateManager
from app.services.exam_flow import ExamFlowManager
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()
state_manager = UserStateManager()
exam_flow = ExamFlowManager()

@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    To: str = Form(...)
):
    """
    Handle incoming WhatsApp messages via Twilio webhook
    """
    logger.info(f"Received message from {From}: {Body}")
    
    # Create Twilio response object
    response = MessagingResponse()
    msg = response.message()
    
    # Extract user phone number (remove 'whatsapp:' prefix)
    user_phone = From.replace('whatsapp:', '')
    message_body = Body.strip().lower()
    
    try:
        # Get user's current state BEFORE processing
        user_state = state_manager.get_user_state(user_phone)
        current_stage = user_state.get('stage', 'initial')
        
        logger.info(f"Processing message from {user_phone}")
        logger.info(f"Current stage: {current_stage}")
        logger.info(f"Message: '{message_body}'")
        logger.info(f"Full state: {user_state}")
        
        # Handle global commands first (these can interrupt any flow)
        if message_body in ['start', 'restart']:
            logger.info(f"User {user_phone} requesting restart/start")
            response_text = exam_flow.start_conversation(user_phone)
            
        elif message_body == 'exit':
            logger.info(f"User {user_phone} exiting")
            state_manager.reset_user_state(user_phone)
            response_text = "Thanks for using the Exam Practice Bot! Send 'start' to begin a new session."
            
        elif message_body == 'help':
            response_text = ("Available commands:\n"
                           "• 'start' - Begin a new exam session\n"
                           "• 'restart' - Restart current session\n"
                           "• 'exit' - End current session\n"
                           "• 'help' - Show this help message")
        
        # Handle stage-specific responses based on CURRENT state
        elif current_stage == 'initial':
            # User hasn't started yet, guide them to start
            logger.info(f"User {user_phone} in initial stage, starting conversation")
            response_text = exam_flow.start_conversation(user_phone)
            
        elif current_stage == 'selecting_exam':
            logger.info(f"User {user_phone} selecting exam: {message_body}")
            response_text = exam_flow.handle_exam_selection(user_phone, message_body)
            
        else:
            # Handle all other stages using the pluggable system
            logger.info(f"User {user_phone} in stage {current_stage}, processing: {message_body}")
            response_text = exam_flow.handle_stage_flow(user_phone, message_body)
        
        # Log the response being sent
        logger.info(f"Sending response to {user_phone}: {response_text[:100]}...")
        
        # Verify final state after processing
        final_state = state_manager.get_user_state(user_phone)
        final_stage = final_state.get('stage', 'unknown')
        logger.info(f"Final state for {user_phone}: {final_stage}")
        
        msg.body(response_text)
        
    except Exception as e:
        logger.error(f"Error processing message from {user_phone}: {str(e)}", exc_info=True)
        msg.body("Sorry, something went wrong. Please try again or send 'restart' to start over.")
    
    return Response(content=str(response), media_type="application/xml")

@router.get("/whatsapp")
async def whatsapp_webhook_verify():
    """
    Webhook verification endpoint for Twilio
    """
    return {"message": "WhatsApp webhook endpoint is ready"}