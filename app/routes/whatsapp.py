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
        
        # Handle different states
        if user_state['stage'] == 'initial' or message_body == 'start':
            # User is starting fresh or explicitly restarting
            response_text = exam_flow.start_conversation(user_phone)
            
        elif message_body == 'restart':
            # User wants to restart
            state_manager.reset_user_state(user_phone)
            response_text = exam_flow.start_conversation(user_phone)
            
        elif message_body == 'exit':
            # User wants to exit
            state_manager.reset_user_state(user_phone)
            response_text = "Thanks for using the Exam Practice Bot! Send 'start' to begin a new session."
            
        elif user_state['stage'] == 'selecting_exam':
            # User is selecting an exam
            response_text = exam_flow.handle_exam_selection(user_phone, message_body)
            
        elif user_state['stage'] == 'selecting_subject':
            # User is selecting a subject
            response_text = exam_flow.handle_subject_selection(user_phone, message_body)
            
        elif user_state['stage'] == 'selecting_year':
            # User is selecting a year
            response_text = exam_flow.handle_year_selection(user_phone, message_body)
            
        elif user_state['stage'] == 'taking_exam':
            # User is answering questions
            response_text = exam_flow.handle_answer(user_phone, message_body)
            
        else:
            # Unknown state or command
            response_text = ("I didn't understand that. Send 'start' to begin, "
                           "'restart' to start over, or 'exit' to quit.")
        
        msg.body(response_text)
        
    except Exception as e:
        logger.error(f"Error processing message from {user_phone}: {str(e)}")
        msg.body("Sorry, something went wrong. Please try again or send 'restart' to start over.")
    
    return Response(content=str(response), media_type="application/xml")

@router.get("/whatsapp")
async def whatsapp_webhook_verify():
    """
    Webhook verification endpoint for Twilio
    """
    return {"message": "WhatsApp webhook endpoint is ready"}