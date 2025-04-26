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
            
            # Create or get conversation
            conversation, created = Conversation.objects.get_or_create(
                chatbot=self.chatbot,
                channel=self.channel,
                from_number=self.from_number
            )
            
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


# Email Handler
class EmailHandler(ChannelResponseHandler):
    def __init__(self, request, chatbot_id):
        super().__init__(request, 'email', chatbot_id)
        self.email_channel = None
        self.imap_connection = None
        self.smtp_connection = None
        self.subject = None
        self.sender_email = None
        self.message_id = None
        self.email_body = None
    
    def extract_data(self):
        """Extract data from the request for email processing."""
        try:
            # For email, we'll be receiving a JSON payload with email details
            data = json.loads(self.request.body)
            self.from_number = data.get('sender_email')  # Using from_number to store email
            self.to_number = data.get('recipient_email')  # Using to_number to store recipient email
            self.body = data.get('body')
            self.subject = data.get('subject')
            self.message_id = data.get('message_id')
            
            if not all([self.from_number, self.to_number, self.body]):
                logger.error("Missing required email parameters")
                return False
                
            logger.info(f"Received email from {self.from_number} to {self.to_number}: {self.body[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error extracting email data: {str(e)}")
            return False
    
    def get_chatbot_and_channel(self):
        """Get the chatbot and email channel configuration."""
        try:
            # First, get the chatbot using the chatbot_id from the URL
            self.chatbot = Chatbot.objects.get(chatbot_id=self.chatbot_id)
            
            # Then, find the channel for this chatbot with the matching channel type
            self.channel = Channel.objects.get(
                chatbot=self.chatbot,
                channel_type=self.channel_type
            )
            
            # Get the email channel configuration
            try:
                self.email_channel = EmailChannel.objects.get(channel=self.channel)
                
                # Verify the email address matches
                if self.email_channel.email_address != self.to_number:
                    logger.error(f"Email address mismatch: {self.email_channel.email_address} != {self.to_number}")
                    return False
                    
                return True
            except EmailChannel.DoesNotExist:
                logger.error(f"No EmailChannel configuration found for this channel")
                return False
        except Chatbot.DoesNotExist:
            logger.error(f"Chatbot not found with ID: {self.chatbot_id}")
            return False
        except Channel.DoesNotExist:
            logger.error(f"No {self.channel_type} channel found for chatbot ID: {self.chatbot_id}")
            return False
        except Exception as e:
            logger.error(f"Error getting chatbot and channel: {str(e)}")
            return False
    
    def send_response(self, response_text):
        """Send an email response back to the user via SMTP."""
        try:
            # Create a multipart message
            msg = MIMEMultipart()
            msg['From'] = self.email_channel.email_address
            msg['To'] = self.from_number
            
            # Create subject as a reply
            if self.subject and not self.subject.lower().startswith('re:'):
                msg['Subject'] = f"Re: {self.subject}"
            else:
                msg['Subject'] = self.subject or "Response from Chatbot"
                
            # Add in-reply-to header if we have the original message ID
            if self.message_id:
                msg['In-Reply-To'] = self.message_id
                msg['References'] = self.message_id
            
            # Add the response text to the email body
            msg.attach(MIMEText(response_text, 'plain'))
            
            # Connect to SMTP server based on provider
            if self.email_channel.provider == 'gmail':
                smtp_server = 'smtp.gmail.com'
                smtp_port = 587
            elif self.email_channel.provider == 'outlook':
                smtp_server = 'smtp.office365.com'
                smtp_port = 587
            else:
                # Use custom SMTP settings
                smtp_server = self.email_channel.smtp_server
                smtp_port = int(self.email_channel.smtp_port)
            
            # Connect to SMTP server
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Secure the connection
            
            # Login with credentials
            # Note: For OAuth2 providers like Gmail, this would need to be adapted
            # to use access tokens instead of passwords
            server.login(self.email_channel.email_address, self.email_channel.access_token)
            
            # Send the email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Sent email response to {self.from_number}")
            return True
        except Exception as e:
            logger.error(f"Error sending email response: {str(e)}")
            return False
    
    def get_immediate_response(self):
        """For email, we don't need an immediate response like with Twilio."""
        return JsonResponse({"status": "processing"})
    
    @staticmethod
    def listen_for_emails(chatbot_id):
        """Listen for new emails using a simple polling approach."""
        try:
            # Get the chatbot and email channel configuration
            chatbot = Chatbot.objects.get(chatbot_id=chatbot_id)
            channel = Channel.objects.get(
                chatbot=chatbot,
                channel_type='email'
            )
            
            email_channel = EmailChannel.objects.get(channel=channel)
            
            # Determine IMAP server settings based on provider
            if email_channel.provider == 'gmail':
                imap_server = 'imap.gmail.com'
                imap_port = 993
            elif email_channel.provider == 'outlook':
                imap_server = 'outlook.office365.com'
                imap_port = 993
            else:
                imap_server = email_channel.imap_server
                imap_port = int(email_channel.imap_port) if email_channel.imap_port else 993
                
            if not imap_server:
                logger.error(f"No IMAP server configured for {email_channel.email_address}")
                return
            
            # Import needed models and utilities
            from django.core.cache import cache
            import time
            import uuid
            
            logger.info(f"Starting email polling for {email_channel.email_address}")
            
            # Main polling loop
            listener_key = f"email_listener_{chatbot_id}"
            poll_interval = 60  # Check every 60 seconds by default
            
            while cache.get(listener_key):
                try:
                    # Create a new connection for each check to avoid timeout issues
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                    mail.login(email_channel.email_address, email_channel.access_token)
                    mail.select('INBOX')
                    
                    # Process any new emails
                    EmailHandler.process_new_emails(mail, chatbot_id, email_channel, channel)
                    
                    # Clean up connection
                    try:
                        mail.close()
                        mail.logout()
                    except Exception as e:
                        logger.warning(f"Error closing IMAP connection: {str(e)}")
                    
                    # Wait before checking again
                    time.sleep(poll_interval)
                    
                except Exception as e:
                    logger.error(f"Error in email polling loop: {str(e)}")
                    # Wait before trying again
                    time.sleep(30)  # Shorter interval on error
            
            logger.info(f"Email polling stopped for {email_channel.email_address}")
            
        except Exception as e:
            logger.error(f"Error in email listener: {str(e)}")
            # Clear the running flag
            from django.core.cache import cache
            cache.delete(f"email_listener_{chatbot_id}")
    
    @staticmethod
    def process_new_emails(mail, chatbot_id, email_channel, channel):
        """Process new emails from an active IMAP connection."""
        try:
            # Import necessary modules
            from chat.models import ProcessedEmail
            from email.utils import parsedate_to_datetime
            from email.header import decode_header
            import email
            import re
            import uuid
            
            # Search for unseen emails - handle different return formats safely
            try:
                result = mail.search(None, 'UNSEEN')
                logger.debug(f"SEARCH result type: {type(result)}, value: {result}")
                
                # Handle different return formats from different IMAP libraries
                if isinstance(result, tuple):
                    # Standard imaplib returns (status, [data])
                    if len(result) >= 1:
                        status = result[0]
                        messages = result[1] if len(result) > 1 else None
                    else:
                        logger.warning(f"Empty tuple in search result")
                        return
                else:
                    # Direct response (some IMAP implementations)
                    status = 'OK'  # Assume OK
                    messages = result
            except ValueError as e:
                logger.error(f"ValueError in search result parsing: {str(e)}")
                # Try a different approach - some IMAP servers return multiple values
                try:
                    # Retry with a more specific search
                    result = mail.search(None, '(UNSEEN)')
                    if isinstance(result, tuple) and len(result) >= 2:
                        status = result[0]
                        messages = result[1]
                    else:
                        logger.error("Unable to parse search results after retry")
                        return
                except Exception as retry_e:
                    logger.error(f"Failed retry search: {str(retry_e)}")
                    return
            
            if status != 'OK':
                logger.error(f"Error searching for emails: {status}")
                return
            
            # Handle different message formats
            if isinstance(messages, list) and len(messages) > 0:
                message_data = messages[0]
            else:
                message_data = messages
                
            # Get the list of email IDs
            if isinstance(message_data, bytes):
                email_ids = message_data.split()
            else:
                logger.warning(f"Unexpected message data format: {type(message_data)}")
                return
            
            if not email_ids:
                return
                
            logger.info(f"Found {len(email_ids)} new emails to process")
            
            from chat.models import ProcessedEmail
            from email.utils import parsedate_to_datetime
            import email
            import re
            
            # Process each email
            for email_id in email_ids:
                # Fetch the email - handle different return formats
                try:
                    result = mail.fetch(email_id, '(RFC822)')
                    
                    # Handle different return formats
                    if isinstance(result, tuple) and len(result) == 2:
                        status, msg_data = result
                    else:
                        logger.warning(f"Unexpected fetch result format: {result}")
                        continue
                    
                    if status != 'OK':
                        logger.error(f"Error fetching email {email_id}: {status}")
                        continue
                    
                    if not msg_data or len(msg_data) == 0:
                        logger.warning(f"No data returned for email {email_id}")
                        continue
                        
                    # Get the first part of the message data
                    first_part = msg_data[0]
                    
                    # Handle different message data formats
                    if isinstance(first_part, tuple) and len(first_part) > 1:
                        raw_email = first_part[1]
                    elif isinstance(first_part, bytes):
                        raw_email = first_part
                    else:
                        logger.warning(f"Unexpected message data format: {first_part}")
                        continue
                except Exception as e:
                    logger.error(f"Error fetching email {email_id}: {str(e)}")
                    continue
                email_message = email.message_from_bytes(raw_email)
                
                # Get message ID for tracking
                message_id = email_message.get('Message-ID')
                if not message_id:
                    logger.warning(f"Email without Message-ID, generating a unique ID")
                    message_id = f"generated-{uuid.uuid4()}"
                
                # Skip already processed emails
                if ProcessedEmail.objects.filter(message_id=message_id).exists():
                    logger.info(f"Skipping already processed email with ID: {message_id}")
                    continue
                
                # Get sender email
                sender_header = email_message.get('From')
                sender_email = re.search(r'<(.+?)>', sender_header)
                if sender_email:
                    sender_email = sender_email.group(1)
                else:
                    sender_email = sender_header
                
                # Skip emails from the chatbot itself to avoid loops
                if sender_email == email_channel.email_address:
                    continue
                
                # Get and decode subject
                subject = email_message.get('Subject')
                if subject:
                    decoded_subject = decode_header(subject)
                    subject = ''
                    for part, encoding in decoded_subject:
                        if isinstance(part, bytes):
                            if encoding:
                                part = part.decode(encoding)
                            else:
                                part = part.decode('utf-8', errors='ignore')
                        subject += part
                
                # Get email body
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get('Content-Disposition'))
                        
                        # Skip attachments
                        if 'attachment' in content_disposition:
                            continue
                        
                        # Get text content
                        if content_type == 'text/plain':
                            charset = part.get_content_charset() or 'utf-8'
                            try:
                                body = part.get_payload(decode=True).decode(charset, errors='ignore')
                            except:
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    # Not multipart - get payload directly
                    charset = email_message.get_content_charset() or 'utf-8'
                    try:
                        body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
                    except:
                        body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                # Clean up the body - remove quoted replies and signatures
                lines = body.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Skip quoted lines (common in email replies)
                    if line.startswith('>'): 
                        continue
                    # Stop at common signature markers
                    if line.strip() == '-- ' or re.match(r'^-{3,}$', line.strip()):
                        break
                    cleaned_lines.append(line)
                
                cleaned_body = '\n'.join(cleaned_lines).strip()
                
                # Skip emails with empty bodies
                if not cleaned_body.strip():
                    logger.info(f"Skipping email with empty body from {sender_email}")
                    continue
                
                logger.info(f"Processing new email from {sender_email}: {subject}")
                
                # Create a request-like object to pass to the handler
                class DummyRequest:
                    def __init__(self, body_data):
                        self.body = json.dumps(body_data).encode('utf-8')
                
                # Prepare the request data
                request_data = {
                    'sender_email': sender_email,
                    'recipient_email': email_channel.email_address,
                    'subject': subject,
                    'body': cleaned_body,
                    'message_id': message_id
                }
                
                # Create a dummy request
                dummy_request = DummyRequest(request_data)
                
                # Process the email
                handler = EmailHandler(dummy_request, chatbot_id)
                handler.handle()
                
                # Mark the email as read
                mail.store(email_id, '+FLAGS', '\\Seen')
                
                # Record that we've processed this email
                ProcessedEmail.objects.create(
                    message_id=message_id,
                    channel=channel
                )
                
                logger.info(f"Successfully processed email from {sender_email}")
                
        except Exception as e:
            logger.error(f"Error processing new emails: {str(e)}")
    
    @staticmethod
    def check_emails(chatbot_id):
        """Check for new emails from the last hour and process them."""
        try:
            # Get the chatbot and email channel configuration
            chatbot = Chatbot.objects.get(chatbot_id=chatbot_id)
            channel = Channel.objects.get(
                chatbot=chatbot,
                channel_type='email'
            )
            
            email_channel = EmailChannel.objects.get(channel=channel)
            
            # Determine IMAP server settings based on provider
            if email_channel.provider == 'gmail':
                imap_server = 'imap.gmail.com'
                imap_port = 993
            elif email_channel.provider == 'outlook':
                imap_server = 'outlook.office365.com'
                imap_port = 993
            else:
                imap_server = email_channel.imap_server
                imap_port = int(email_channel.imap_port)
            
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(email_channel.email_address, email_channel.access_token)
            mail.select('INBOX')
            
            # Import needed models and utilities
            from chat.models import ProcessedEmail
            from django.utils import timezone
            import pytz
            from email.utils import parsedate_to_datetime
            
            # Get emails from the last hour
            one_hour_ago = timezone.now() - datetime.timedelta(hours=1)
            date_str = one_hour_ago.strftime("%d-%b-%Y")
            
            # IMAP search criteria for emails received since the date
            search_criteria = f'(SINCE {date_str})'
            
            # Search for emails
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                logger.error(f"Error searching for emails: {status}")
                mail.logout()
                return
            
            # Get the list of email IDs
            email_ids = messages[0].split()
            
            if not email_ids:
                logger.info(f"No new emails found for {email_channel.email_address}")
                mail.logout()
                return
                
            logger.info(f"Found {len(email_ids)} emails to check from {date_str}")
            
            # Process each email
            for email_id in email_ids:
                # Fetch the email - handle different return formats
                try:
                    result = mail.fetch(email_id, '(RFC822)')
                    
                    # Handle different return formats
                    if isinstance(result, tuple) and len(result) == 2:
                        status, msg_data = result
                    else:
                        logger.warning(f"Unexpected fetch result format: {result}")
                        continue
                    
                    if status != 'OK':
                        logger.error(f"Error fetching email {email_id}: {status}")
                        continue
                    
                    if not msg_data or len(msg_data) == 0:
                        logger.warning(f"No data returned for email {email_id}")
                        continue
                        
                    # Get the first part of the message data
                    first_part = msg_data[0]
                    
                    # Handle different message data formats
                    if isinstance(first_part, tuple) and len(first_part) > 1:
                        raw_email = first_part[1]
                    elif isinstance(first_part, bytes):
                        raw_email = first_part
                    else:
                        logger.warning(f"Unexpected message data format: {first_part}")
                        continue
                except Exception as e:
                    logger.error(f"Error fetching email {email_id}: {str(e)}")
                    continue
                email_message = email.message_from_bytes(raw_email)
                
                # Check the date of the email
                date_header = email_message.get('Date')
                email_date = None
                if date_header:
                    try:
                        # Parse the date from the email header (this will be timezone-aware)
                        email_date = parsedate_to_datetime(date_header)
                        
                        # Skip emails older than one hour
                        if email_date < one_hour_ago:
                            logger.info(f"Skipping email older than 1 hour: {date_header}")
                            continue
                    except Exception as e:
                        # Continue processing even if we can't parse the date
                        logger.warning(f"Could not parse email date: {date_header}, {str(e)}")
                
                # Get message ID for tracking
                message_id = email_message.get('Message-ID')
                if not message_id:
                    logger.warning(f"Email without Message-ID, generating a unique ID")
                    message_id = f"generated-{uuid.uuid4()}"
                
                # Skip already processed emails
                if ProcessedEmail.objects.filter(message_id=message_id).exists():
                    logger.info(f"Skipping already processed email with ID: {message_id}")
                    continue
                
                # Get sender email
                sender_header = email_message.get('From')
                sender_email = re.search(r'<(.+?)>', sender_header)
                if sender_email:
                    sender_email = sender_email.group(1)
                else:
                    sender_email = sender_header
                
                # Skip emails from the chatbot itself to avoid loops
                if sender_email == email_channel.email_address:
                    continue
                
                # Get and decode subject
                subject = email_message.get('Subject')
                if subject:
                    decoded_subject = decode_header(subject)
                    subject = ''
                    for part, encoding in decoded_subject:
                        if isinstance(part, bytes):
                            if encoding:
                                part = part.decode(encoding)
                            else:
                                part = part.decode('utf-8', errors='ignore')
                        subject += part
                
                # Get email body
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get('Content-Disposition'))
                        
                        # Skip attachments
                        if 'attachment' in content_disposition:
                            continue
                        
                        # Get text content
                        if content_type == 'text/plain':
                            charset = part.get_content_charset() or 'utf-8'
                            try:
                                body = part.get_payload(decode=True).decode(charset, errors='ignore')
                            except:
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    # Not multipart - get payload directly
                    charset = email_message.get_content_charset() or 'utf-8'
                    try:
                        body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
                    except:
                        body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                # Clean up the body - remove quoted replies and signatures
                lines = body.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Skip quoted lines (common in email replies)
                    if line.startswith('>'): 
                        continue
                    # Stop at common signature markers
                    if line.strip() == '-- ' or re.match(r'^-{3,}$', line.strip()):
                        break
                    cleaned_lines.append(line)
                
                cleaned_body = '\n'.join(cleaned_lines).strip()
                
                # Skip emails with empty bodies
                if not cleaned_body.strip():
                    logger.info(f"Skipping email with empty body from {sender_email}")
                    continue
                
                logger.info(f"Processing new email from {sender_email}: {subject}")
                
                # Create a request-like object to pass to the handler
                class DummyRequest:
                    def __init__(self, body_data):
                        self.body = json.dumps(body_data).encode('utf-8')
                
                # Prepare the request data
                request_data = {
                    'sender_email': sender_email,
                    'recipient_email': email_channel.email_address,
                    'subject': subject,
                    'body': cleaned_body,
                    'message_id': message_id
                }
                
                # Create a dummy request
                dummy_request = DummyRequest(request_data)
                
                # Process the email
                handler = EmailHandler(dummy_request, chatbot_id)
                handler.handle()
                
                # Mark the email as read
                mail.store(email_id, '+FLAGS', '\\Seen')
                
                # Record that we've processed this email
                ProcessedEmail.objects.create(
                    message_id=message_id,
                    channel=channel
                )
                
                logger.info(f"Successfully processed email from {sender_email}")
            
            # Update the last synced timestamp with timezone-aware datetime
            email_channel.last_synced = timezone.now()
            email_channel.save()
            
            # Logout from the server
            mail.logout()
            
            logger.info(f"Email check completed for {email_channel.email_address}")
            
        except Exception as e:
            logger.error(f"Error checking emails: {str(e)}")

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

@csrf_exempt
@require_POST
def handle_email(request, chatbot_id):
    """Handle incoming email messages via webhook."""
    handler = EmailHandler(request, chatbot_id)
    return handler.handle()

@csrf_exempt
def check_emails(request, chatbot_id):
    """Manually trigger checking for new emails."""
    try:
        threading.Thread(
            target=EmailHandler.check_emails,
            args=(chatbot_id,)
        ).start()
        return JsonResponse({"status": "Email check started"})
    except Exception as e:
        logger.error(f"Error starting email check: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def start_email_listener(request, chatbot_id):
    """Start a continuous email listener using IMAP IDLE."""
    try:
        # Check if a listener is already running for this chatbot
        from django.core.cache import cache
        listener_key = f"email_listener_{chatbot_id}"
        
        if cache.get(listener_key):
            return JsonResponse({"status": "Listener already running"})
        
        # Mark as running
        cache.set(listener_key, True)
        
        # Start the listener in a background thread
        threading.Thread(
            target=EmailHandler.listen_for_emails,
            args=(chatbot_id,),
            daemon=True  # Allow the thread to be terminated when the main program exits
        ).start()
        
        return JsonResponse({"status": "Email listener started"})
    except Exception as e:
        logger.error(f"Error starting email listener: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def stop_email_listener(request, chatbot_id):
    """Stop the continuous email listener."""
    try:
        from django.core.cache import cache
        listener_key = f"email_listener_{chatbot_id}"
        
        # Mark as stopped
        cache.delete(listener_key)
        
        return JsonResponse({"status": "Email listener stopping"})
    except Exception as e:
        logger.error(f"Error stopping email listener: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
