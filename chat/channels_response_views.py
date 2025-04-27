from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from chat.models import Chatbot, Channel, Conversation, Message, WhatsAppChannel, EmailChannel
import json
import threading
import logging
import time
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import re
import datetime
from chat.pinecone import create_rag_chain

logger = logging.getLogger(__name__)

# Base class for handling channel responses
class ChannelResponseHandler:
    def __init__(self, request, channel_type, chatbot_id):
        self.request = request
        self.channel_type = channel_type
        self.chatbot_id = chatbot_id
        self.from_number = None
        self.body = None
        self.to_number = None
        self.chatbot = None
        self.channel = None
        
    def extract_data(self):
        """Extract data from the request. To be implemented by subclasses."""
        raise NotImplementedError
        
    def get_chatbot_and_channel(self):
        """Get the chatbot and channel based on the chatbot_id."""
        try:
            # First, get the chatbot using the chatbot_id from the URL
            self.chatbot = Chatbot.objects.get(chatbot_id=self.chatbot_id)
            
            # Then, find the channel for this chatbot with the matching channel type
            self.channel = Channel.objects.get(
                chatbot=self.chatbot,
                channel_type=self.channel_type
            )
            
            # For WhatsApp and SMS, we also need to verify the Twilio phone number matches
            if self.channel_type in ['whatsapp', 'sms']:
                try:
                    self.whatsapp_channel = WhatsAppChannel.objects.get(channel=self.channel)
                    # Store Twilio credentials for later use
                    self.twilio_account_sid = self.whatsapp_channel.twilio_account_sid
                    self.twilio_auth_token = self.whatsapp_channel.twilio_auth_token
                    
                    # Verify the phone number matches
                    if self.whatsapp_channel.twilio_phone_number != self.to_number:
                        logger.error(f"Phone number mismatch: {self.whatsapp_channel.twilio_phone_number} != {self.to_number}")
                        return False
                except WhatsAppChannel.DoesNotExist:
                    logger.error(f"No WhatsAppChannel configuration found for this channel")
                    return False
            
            return True
        except Chatbot.DoesNotExist:
            logger.error(f"Chatbot not found with ID: {self.chatbot_id}")
            return False
        except Channel.DoesNotExist:
            logger.error(f"No {self.channel_type} channel found for chatbot ID: {self.chatbot_id}")
            return False
        except Exception as e:
            logger.error(f"Error getting chatbot and channel: {str(e)}")
            return False
    
    def get_conversation_history(self, conversation):
        """Get the conversation history for context."""
        try:
            # Get conversation history for context
            conversation_history = Message.objects.filter(
                conversation=conversation
            ).order_by('created_at')[:10]  # Limit to last 10 messages for context
            
            # Format conversation history for the LLM
            formatted_history = []
            for msg in conversation_history:
                role = "user" if msg.role == 'user' else "assistant"
                formatted_history.append({"role": role, "content": msg.content})
            
            return formatted_history
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    def get_twilio_client(self):
        """Get a Twilio client instance using the credentials from the channel configuration."""
        try:
            if hasattr(self, 'twilio_account_sid') and hasattr(self, 'twilio_auth_token'):
                return Client(self.twilio_account_sid, self.twilio_auth_token)
            else:
                logger.error("Twilio credentials not available")
                return None
        except Exception as e:
            logger.error(f"Error creating Twilio client: {str(e)}")
            return None
    
    def process_message_in_background(self, conversation):
        """Process the message in the background and send the response."""
        try:
            # Add a small delay to ensure the immediate response is sent first
            time.sleep(1)
            
            # Save user message
            user_message = Message.objects.create(
                conversation=conversation,
                content=self.body,
                role='user'
            )
            
            # Get conversation history
            formatted_history = self.get_conversation_history(conversation)
            
            # Create the RAG chain with the chatbot's namespace
            rag_chain = create_rag_chain(self.chatbot, namespace=self.chatbot.name)
            
            # Pass the message and the full formatted history to the chain
            logger.info(f"Generating response for {self.channel_type} message from {self.from_number}")
            bot_response = rag_chain(self.body, formatted_history)
            
            # Save bot response
            bot_message = Message.objects.create(
                conversation=conversation,
                content=bot_response,
                role='assistant'
            )
            
            logger.info(f"Generated response for {self.channel_type} message: {bot_response[:50]}...")
            
            # Send the response via Twilio
            self.send_response(bot_response)
            
        except Exception as e:
            logger.error(f"Error processing {self.channel_type} message: {str(e)}")
    
    def send_response(self, response_text):
        """Send the response via Twilio. To be implemented by subclasses."""
        raise NotImplementedError
    
    def handle(self):
        """Handle the incoming message."""
        try:
            # Extract data from the request
            if not self.extract_data():
                return HttpResponse("Failed to extract data from request", status=400)
            
            # Get the chatbot and channel
            if not self.get_chatbot_and_channel():
                return HttpResponse("No matching chatbot found", status=404)
            
            # Create or get conversation based on channel type
            try:
                if self.channel_type == 'email' and hasattr(self, 'from_email'):
                    # For email channel, try to find by from_email first
                    try:
                        # Try to get a single conversation by from_email
                        conversation = Conversation.objects.get(
                            chatbot=self.chatbot,
                            channel=self.channel,
                            from_email=self.from_email
                        )
                        created = False
                    except Conversation.DoesNotExist:
                        # If no conversation exists with from_email, check if there's one with from_number
                        # that matches the email (for backward compatibility)
                        try:
                            # Look for conversations with the email in from_number field
                            email_conversations = Conversation.objects.filter(
                                chatbot=self.chatbot,
                                channel=self.channel,
                                from_number=self.from_email  # Old format without 'email:' prefix
                            )
                            
                            if email_conversations.exists():
                                # Use the most recent conversation
                                conversation = email_conversations.order_by('-updated_at').first()
                                # Update it to use the new from_email field
                                conversation.from_email = self.from_email
                                conversation.save()
                                created = False
                            else:
                                # Create a new conversation
                                conversation = Conversation.objects.create(
                                    chatbot=self.chatbot,
                                    channel=self.channel,
                                    from_email=self.from_email,
                                    from_number=self.from_number or ''
                                )
                                created = True
                        except Exception as e:
                            logger.error(f"Error finding email conversation: {str(e)}")
                            # Create a new conversation as fallback
                            conversation = Conversation.objects.create(
                                chatbot=self.chatbot,
                                channel=self.channel,
                                from_email=self.from_email,
                                from_number=self.from_number or ''
                            )
                            created = True
                else:
                    # For other channels (SMS, WhatsApp), use from_number as before
                    conversation, created = Conversation.objects.get_or_create(
                        chatbot=self.chatbot,
                        channel=self.channel,
                        from_number=self.from_number,
                        defaults={'from_email': ''}
                    )
            except Conversation.MultipleObjectsReturned:
                # Handle the case where multiple conversations are found
                logger.warning(f"Multiple conversations found for {self.channel_type} from {self.from_email or self.from_number}")
                
                if self.channel_type == 'email' and hasattr(self, 'from_email'):
                    # Get the most recent conversation for this email
                    conversations = Conversation.objects.filter(
                        chatbot=self.chatbot,
                        channel=self.channel,
                        from_email=self.from_email
                    ).order_by('-updated_at')
                else:
                    # Get the most recent conversation for this number
                    conversations = Conversation.objects.filter(
                        chatbot=self.chatbot,
                        channel=self.channel,
                        from_number=self.from_number
                    ).order_by('-updated_at')
                
                # Use the most recent conversation
                conversation = conversations.first()
                created = False
            
            # Process the message in a background thread
            threading.Thread(
                target=self.process_message_in_background,
                args=(conversation,)
            ).start()
            
            # Return an empty TwiML response immediately
            return self.get_immediate_response()
            
        except Exception as e:
            logger.error(f"Error handling {self.channel_type} message: {str(e)}")
            return HttpResponse(f"Error: {str(e)}", status=500)
    

    def get_immediate_response(self):
        """Get the immediate response to send back to Twilio."""
        # Create a TwiML response
        resp = MessagingResponse()
        return HttpResponse(str(resp), content_type='text/xml')


# SMS Handler
class SMSHandler(ChannelResponseHandler):
    def __init__(self, request, chatbot_id):
        super().__init__(request, 'sms', chatbot_id)
    
    def extract_data(self):
        try:
            # Extract data from Twilio SMS request
            self.from_number = self.request.POST.get('From')
            self.to_number = self.request.POST.get('To')
            self.body = self.request.POST.get('Body')
            
            if not all([self.from_number, self.to_number, self.body]):
                logger.error("Missing required SMS parameters")
                return False
                
            logger.info(f"Received SMS from {self.from_number} to {self.to_number}: {self.body[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error extracting SMS data: {str(e)}")
            return False
    
    def send_response(self, response_text):
        """Send an SMS response back to the user via Twilio."""
        try:
            # Get Twilio client
            client = self.get_twilio_client()
            if not client:
                logger.error("Failed to get Twilio client for sending SMS response")
                return
            
            # Send the SMS
            message = client.messages.create(
                body=response_text,
                from_=self.to_number,  # The Twilio phone number
                to=self.from_number    # The user's phone number
            )
            
            logger.info(f"Sent SMS to {self.from_number}, SID: {message.sid}")
        except Exception as e:
            logger.error(f"Error sending SMS response: {str(e)}")


# WhatsApp Handler
class WhatsAppHandler(ChannelResponseHandler):
    def __init__(self, request, chatbot_id):
        super().__init__(request, 'whatsapp', chatbot_id)
    
    def extract_data(self):
        try:
            # Extract data from Twilio WhatsApp request
            # WhatsApp numbers come in the format 'whatsapp:+1234567890'
            from_whatsapp = self.request.POST.get('From', '')
            to_whatsapp = self.request.POST.get('To', '')
            
            # Strip the 'whatsapp:' prefix if present
            self.from_number = from_whatsapp.replace('whatsapp:', '') if from_whatsapp else None
            self.to_number = to_whatsapp.replace('whatsapp:', '') if to_whatsapp else None
            
            self.body = self.request.POST.get('Body')
            
            if not all([self.from_number, self.to_number, self.body]):
                logger.error("Missing required WhatsApp parameters")
                return False
                
            logger.info(f"Received WhatsApp from {self.from_number} to {self.to_number}: {self.body[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error extracting WhatsApp data: {str(e)}")
            return False
    
    def send_response(self, response_text):
        """Send a WhatsApp response back to the user via Twilio."""
        try:
            # Get Twilio client
            client = self.get_twilio_client()
            if not client:
                logger.error("Failed to get Twilio client for sending WhatsApp response")
                return
            
            # For WhatsApp, we need to prefix the phone numbers with 'whatsapp:'
            from_whatsapp = f"whatsapp:{self.to_number}"  # The Twilio WhatsApp number
            to_whatsapp = f"whatsapp:{self.from_number}"  # The user's WhatsApp number
            
            # Send the WhatsApp message
            message = client.messages.create(
                body=response_text,
                from_=from_whatsapp,
                to=to_whatsapp
            )
            
            logger.info(f"Sent WhatsApp to {self.from_number}, SID: {message.sid}")
        except Exception as e:
            logger.error(f"Error sending WhatsApp response: {str(e)}")


# View functions for handling incoming messages

@csrf_exempt
@require_POST
def handle_sms(request, chatbot_id):
    """Handle incoming SMS messages from Twilio."""
    handler = SMSHandler(request, chatbot_id)
    return handler.handle()

@csrf_exempt
@require_POST
def handle_whatsapp(request, chatbot_id):
    """Handle incoming WhatsApp messages from Twilio."""
    handler = WhatsAppHandler(request, chatbot_id)
    return handler.handle()

