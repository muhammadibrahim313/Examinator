from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from app.services.state import UserStateManager
from app.services.exam_flow import ExamFlowManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
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
        # Get user's current state
        user_state = state_manager.get_user_state(user_phone)
        current_stage = user_state.get('stage', 'initial')
        
        logger.info(f"User {user_phone} current stage: {current_stage}")
        logger.info(f"User message: '{message_body}'")
        
        # Handle global commands first
        if message_body in ['start', 'restart']:
            logger.info(f"User {user_phone} starting/restarting")
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
            
        # Handle stage-specific responses
        elif current_stage == 'initial':
            logger.info(f"User {user_phone} in initial stage, starting conversation")
            response_text = exam_flow.start_conversation(user_phone)
            
        elif current_stage == 'selecting_exam':
            logger.info(f"User {user_phone} selecting exam: {message_body}")
            response_text = exam_flow.handle_exam_selection(user_phone, message_body)
            
        elif current_stage == 'selecting_subject':
            logger.info(f"User {user_phone} selecting subject: {message_body}")
            response_text = exam_flow.handle_subject_selection(user_phone, message_body)
            
        elif current_stage == 'selecting_year':
            logger.info(f"User {user_phone} selecting year: {message_body}")
            response_text = exam_flow.handle_year_selection(user_phone, message_body)
            
        elif current_stage == 'taking_exam':
            logger.info(f"User {user_phone} answering question: {message_body}")
            response_text = exam_flow.handle_answer(user_phone, message_body)
            
        else:
            logger.warning(f"Unknown stage for user {user_phone}: {current_stage}")
            response_text = ("I didn't understand that. Send 'start' to begin, "
                           "'restart' to start over, 'help' for commands, or 'exit' to quit.")
        
        # Log the response being sent
        logger.info(f"Sending response to {user_phone}: {response_text[:100]}...")
        
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