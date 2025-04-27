import os
import json
import logging
import base64
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode
import uuid

# Set this environment variable to allow OAuth over insecure transport (for development only)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'nexus-ai-service.json')

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.db import models

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build 
from googleapiclient.errors import HttpError
from google.cloud import pubsub_v1

from chat.models import Channel, EmailChannel, Chatbot, ProcessedEmail, Conversation, Message
from chat.channels_response_views import ChannelResponseHandler

logger = logging.getLogger(__name__)

# Gmail API scopes needed for reading and sending emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/pubsub'
]

# Configuration - these should be moved to settings.py in production
CLIENT_ID = '789110401170-l63q4kll8rfsnvbmfmjmnutl2pa11ogp.apps.googleusercontent.com'  # Replace with your OAuth client ID
CLIENT_SECRET = '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'  # Replace with your OAuth client secret

# For local development, use http://localhost:<port>/chat/google/oauth2callback/
# For production, use your actual domain with https
REDIRECT_URI = 'http://localhost:8000/chat/google/oauth2callback/'  # Update with your domain

# Pub/Sub configuration
PUBSUB_TOPIC = 'gmail-notifications'
PUBSUB_SUBSCRIPTION = 'gmail-chatbot-subscription'
PUBSUB_SERVICE_ACCOUNT_FILE = SERVICE_ACCOUNT_FILE  # Path to your service account key file



def get_authorization_url(request, channel_id):
    """Generate the authorization URL for Gmail OAuth2 consent."""
    try:
        # Create a custom state that includes the channel_id
        # This is more reliable than using the session which might be lost during redirects
        custom_state = f"{channel_id}:{uuid.uuid4().hex}"
        
        # Create the OAuth2 flow
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            },
            scopes=SCOPES
        )
        
        flow.redirect_uri = REDIRECT_URI
        
        # Generate the authorization URL with our custom state
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',  # Force to show the consent screen to get refresh token
            state=custom_state  # Pass our custom state with channel_id
        )
        
        return authorization_url
        
    except Exception as e:
        logger.error(f"Error generating Gmail authorization URL: {str(e)}")
        return None


def oauth2callback(request):
    """Handle the OAuth2 callback from Google."""
    try:
        # Get the state parameter from the callback URL
        state = request.GET.get('state')
        
        if not state or ':' not in state:
            return HttpResponse("Error: Invalid state parameter", status=400)
        
        # Extract the channel_id from the state parameter
        channel_id, _ = state.split(':', 1)
        
        if not channel_id:
            return HttpResponse("Error: No channel ID found in state parameter", status=400)
        
        # Create the OAuth2 flow
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            },
            scopes=SCOPES,
            state=state
        )
        flow.redirect_uri = REDIRECT_URI
        
        # Get the full URL from the request
        authorization_response = request.build_absolute_uri()
        
        # If we're developing locally with http but the redirect_uri is https,
        # we need to modify the authorization_response to match
        if REDIRECT_URI.startswith('http://') and authorization_response.startswith('http://'):
            # This is fine for development with OAUTHLIB_INSECURE_TRANSPORT=1
            pass
        elif REDIRECT_URI.startswith('https://') and authorization_response.startswith('http://'):
            # Convert http to https in the authorization response to match the redirect URI
            authorization_response = 'https://' + authorization_response[7:]
        
        # Exchange the authorization code for credentials
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        
        # Get the channel
        channel = Channel.objects.get(channel_id=channel_id)
        
        # Get or create the email channel configuration
        email_channel, created = EmailChannel.objects.get_or_create(
            channel=channel,
            defaults={
                'provider': 'gmail',
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'email_address': get_gmail_address(credentials)
            }
        )
        
        if not created:
            # Update the existing email channel
            email_channel.access_token = credentials.token
            email_channel.refresh_token = credentials.refresh_token
            if not email_channel.email_address:
                email_channel.email_address = get_gmail_address(credentials)
            email_channel.save()
        
        # Set up Gmail push notifications
        setup_gmail_push_notifications(credentials, email_channel)
        
        # Redirect to the chatbot configuration page
        return redirect('chat:edit_chatbot_page', chatbot_id=channel.chatbot.chatbot_id)
        
    except Exception as e:
        logger.error(f"Error in Gmail OAuth2 callback: {str(e)}")
        return HttpResponse(f"Error: {str(e)}", status=500)



def get_gmail_address(credentials):
    """Get the Gmail address for the authenticated user."""
    try:
        # Build the Gmail API service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get the user profile
        profile = service.users().getProfile(userId='me').execute()
        
        return profile.get('emailAddress')
        
    except Exception as e:
        logger.error(f"Error getting Gmail address: {str(e)}")
        return None




def setup_gmail_push_notifications(credentials, email_channel):
    """Set up Gmail push notifications using Pub/Sub."""
    try:
        service = build('gmail', 'v1', credentials=credentials)
        
        try:
            # Stop any existing watch
            service.users().stop(userId='me').execute()
            print("Stopped existing Gmail watch")
        except Exception as e:
            print(f"Note: No existing watch to stop or error stopping watch: {str(e)}")

        request = {
            'labelIds': ['INBOX'],
            'topicName': f'projects/nexus-ai-458019/topics/Nexus_AI',
            'labelFilterAction': 'include'
        }
        
        watch_response = service.users().watch(userId='me', body=request).execute()
        
        email_channel.watch_expiration = datetime.fromtimestamp(int(watch_response['expiration'])/1000)
        email_channel.watch_history_id = watch_response['historyId']
        email_channel.save()
        
        print(f"Gmail push notifications set up for {email_channel.email_address}")
        
    except Exception as e:
        print(f"Error setting up Gmail push notifications: {str(e)}")


def stop_gmail_push_notifications(email_channel):
    """Stop Gmail push notifications for a specific email channel."""
    try:
        # Check if the channel already has no watch expiration
        if email_channel.watch_expiration is None:
            print(f"No active watch found for {email_channel.email_address}")
            # Still return True since there's no watch to stop
            return True
            
        # Refresh credentials
        try:
            credentials = refresh_gmail_credentials(email_channel)
            if not credentials:
                print(f"Failed to refresh credentials for {email_channel.email_address}")
                # Still clear the watch expiration since we can't use this channel anymore
                email_channel.watch_expiration = None
                email_channel.save()
                print(f"Cleared watch expiration for {email_channel.email_address} despite credential failure")
                return False
        except Exception as cred_error:
            print(f"Error refreshing credentials for {email_channel.email_address}: {str(cred_error)}")
            # Still clear the watch expiration
            email_channel.watch_expiration = None
            email_channel.save()
            print(f"Cleared watch expiration for {email_channel.email_address} despite error")
            return False
            
        # Build the Gmail API service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Stop the watch
        try:
            service.users().stop(userId='me').execute()
            print(f"Successfully called stop() API for {email_channel.email_address}")
        except Exception as stop_error:
            print(f"Error calling stop() API for {email_channel.email_address}: {str(stop_error)}")
            # Continue anyway to update the database
        
        # Update the email channel
        email_channel.watch_expiration = None
        email_channel.save()
        
        print(f"Successfully stopped Gmail push notifications for {email_channel.email_address}")
        return True
        
    except Exception as e:
        print(f"Error stopping Gmail push notifications for {email_channel.email_address}: {str(e)}")
        # Try to clear the watch expiration anyway
        try:
            email_channel.watch_expiration = None
            email_channel.save()
            print(f"Cleared watch expiration for {email_channel.email_address} despite error")
        except Exception as save_error:
            print(f"Could not clear watch expiration: {str(save_error)}")
        return False


def stop_all_gmail_push_notifications():
    """Stop Gmail push notifications for all email channels."""
    success_count = 0
    failure_count = 0
    
    # Get all email channels
    email_channels = EmailChannel.objects.all()
    
    for email_channel in email_channels:
        if stop_gmail_push_notifications(email_channel):
            success_count += 1
        else:
            failure_count += 1
    
    return {
        'success_count': success_count,
        'failure_count': failure_count,
        'total': success_count + failure_count
    }


@csrf_exempt
def stop_gmail_watch(request):
    """View function to stop Gmail push notifications."""
    try:
        # Check if channel_id is provided
        channel_id = request.GET.get('channel_id')
        
        if channel_id:
            # Stop notifications for a specific channel
            try:
                channel = Channel.objects.get(channel_id=channel_id)
                email_channel = EmailChannel.objects.get(channel=channel)
                
                if stop_gmail_push_notifications(email_channel):
                    return JsonResponse({
                        'success': True,
                        'message': f'Successfully stopped Gmail push notifications for {email_channel.email_address}'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'Failed to stop Gmail push notifications for {email_channel.email_address}'
                    }, status=500)
                    
            except (Channel.DoesNotExist, EmailChannel.DoesNotExist) as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Channel not found: {str(e)}'
                }, status=404)
        else:
            # Stop notifications for all channels
            result = stop_all_gmail_push_notifications()
            
            if result['failure_count'] == 0:
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully stopped Gmail push notifications for all {result["success_count"]} channels',
                    'details': result
                })
            else:
                return JsonResponse({
                    'success': result['success_count'] > 0,
                    'message': f'Stopped {result["success_count"]} channels, failed to stop {result["failure_count"]} channels',
                    'details': result
                }, status=207)  # 207 Multi-Status
                
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)




def refresh_gmail_credentials(email_channel):
    """Refresh the Gmail API credentials if they are expired."""
    try:
        # Create credentials object from stored tokens
        credentials = google.oauth2.credentials.Credentials(
            token=email_channel.access_token,
            refresh_token=email_channel.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        
        # Check if credentials are expired and refresh them
        if credentials.expired:
            credentials.refresh(Request())
            
            # Update the stored tokens
            email_channel.access_token = credentials.token
            email_channel.save()
            
            logger.info(f"Refreshed Gmail credentials for {email_channel.email_address}")
        
        return credentials
        
    except Exception as e:
        logger.error(f"Error refreshing Gmail credentials: {str(e)}")
        return None




def renew_push_notification_watch(email_channel):
    """Renew the Gmail push notification watch if it's about to expire."""
    try:
        # Check if the watch is about to expire (within 1 day)
        if email_channel.watch_expiration and email_channel.watch_expiration - timedelta(days=1) <= datetime.now():
            # Get fresh credentials
            credentials = refresh_gmail_credentials(email_channel)
            
            # Set up push notifications again
            setup_gmail_push_notifications(credentials, email_channel)
            
            logger.info(f"Renewed Gmail push notification watch for {email_channel.email_address}")
        
    except Exception as e:
        logger.error(f"Error renewing Gmail push notification watch: {str(e)}")




@csrf_exempt
def gmail_push_notification(request):
    """Handle Gmail push notifications from Pub/Sub."""
    try:
        # Verify the request is from Google Pub/Sub
        print("Gmail push notification received")
        if request.method != 'POST':
            return HttpResponse('Only POST requests are accepted', status=405)
        
        # Check if the request body is empty
        if not request.body:
            print("Empty request body received")
            return HttpResponse('Empty request body', status=400)
            
        # Log the raw request body for debugging
        print(f"Request body: {request.body.decode('utf-8', errors='replace')}")
        
        try:
            # Parse the message from Pub/Sub
            data = json.loads(request.body.decode('utf-8'))
            print(f"Gmail push notification received\nRequest body: {json.dumps(data)}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            # For testing purposes, return OK to acknowledge the request
            return HttpResponse('Invalid JSON, but acknowledged for testing', status=200)
        
        # Verify the message has the expected structure
        if 'message' not in data:
            print("No 'message' field in data")
            return HttpResponse('Invalid Pub/Sub message format', status=400)
        
        # Get the message data
        message = data['message']
        if 'data' not in message:
            print("No 'data' field in message")
            return HttpResponse('No data in Pub/Sub message', status=400)
            
        # Extract the message ID for deduplication
        message_id = message.get('messageId') or message.get('message_id')
        if message_id:
            # Use a cache to prevent duplicate processing of the same notification
            cache_key = f"gmail_notification_{message_id}"
            if cache.get(cache_key):
                print(f"Skipping duplicate notification with message_id: {message_id}")
                return HttpResponse("Duplicate notification", status=200)
            
            # Set a cache entry to mark this notification as being processed
            # Use a short timeout (30 seconds) to prevent permanent blocking if processing fails
            cache.set(cache_key, True, 30)
        
        try:
            message_data = base64.b64decode(message['data']).decode('utf-8')
            print(f"Decoded message data: {message_data}")
            
            # Try to parse the decoded data as JSON
            try:
                notification_data = json.loads(message_data)
            except json.JSONDecodeError:
                # If it's not valid JSON, it might be a test message
                print("Received a non-JSON test message")
                return HttpResponse('Test message received', status=200)
            
            # Extract the email information
            email_address = notification_data.get('emailAddress')
            history_id = notification_data.get('historyId')
            
            if not email_address or not history_id:
                print(f"Missing email address or history ID: {notification_data}")
                # This might be a test message or verification from Google
                return HttpResponse('Acknowledged', status=200)
                
            # Find the corresponding email channel
            try:
                email_channel = EmailChannel.objects.get(email_address=email_address)
            except EmailChannel.DoesNotExist:
                print(f"No email channel found for {email_address}")
                return HttpResponse(f'No email channel found for {email_address}', status=404)
            
            # Process new emails
            process_new_emails(email_channel, history_id)
            
            # Acknowledge the message
            return HttpResponse('OK', status=200)
            
        except Exception as e:
            print(f"Error processing message data: {str(e)}")
            # This is likely a test message, so return success
            return HttpResponse('Test message acknowledged', status=200)
            
    except Exception as e:
        print(f"Error handling Gmail push notification: {str(e)}")
        return HttpResponse(f"Error: {str(e)}", status=500)
def process_new_emails(email_channel, history_id):
    """Process new emails based on the history ID."""
    try:
        # Get fresh credentials
        credentials = refresh_gmail_credentials(email_channel)
        if not credentials:
            logger.error(f"Failed to refresh credentials for {email_channel.email_address}")
            return
        
        # Build the Gmail API service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get the last processed history ID
        last_history_id = email_channel.watch_history_id or 0
        
        # Get history since the last processed ID
        history_results = service.users().history().list(
            userId='me',
            startHistoryId=last_history_id,
            historyTypes=['messageAdded']
        ).execute()
        
        # Update the history ID
        email_channel.watch_history_id = history_id
        email_channel.save()
        
        # Process each history record
        if 'history' in history_results:
            for history in history_results['history']:
                if 'messagesAdded' in history:
                    for message_added in history['messagesAdded']:
                        message = message_added['message']
                        
                        # Skip already processed emails
                        if ProcessedEmail.objects.filter(message_id=message['id']).exists():
                            continue
                        
                        # Process the email
                        process_gmail_message(service, email_channel, message['id'])
        
    except Exception as e:
        logger.error(f"Error processing new emails: {str(e)}")





def process_gmail_message(service, email_channel, message_id):
    """Process a single Gmail message."""
    try:
        # Check if this message has already been processed
        if ProcessedEmail.objects.filter(message_id=message_id).exists():
            print(f"Skipping already processed message: {message_id}")
            return
            
        # Get the message
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract message details
        headers = {header['name']: header['value'] for header in message['payload']['headers']}
        
        # Get sender email
        from_header = headers.get('From', '')
        sender_email = extract_email_address(from_header)
        
        # Skip emails from the chatbot itself to avoid loops
        if sender_email == email_channel.email_address:
            print(f"Skipping email from the chatbot itself: {sender_email}")
            # Mark as processed to avoid future processing attempts
            ProcessedEmail.objects.create(
                message_id=message_id,
                channel=email_channel.channel
            )
            return
            
        # Skip system-generated messages based on sender
        system_indicators = [
            "mailer-daemon@",
            "postmaster@",
            "noreply@",
            "no-reply@",
            "unknown@example.com"
        ]
        
        # Check if this is likely a system message based on sender
        is_system_message = False
        if not sender_email or sender_email.strip() == '':
            is_system_message = True
            print(f"Skipping message with empty sender: {message_id}")
        elif any(indicator.lower() in (sender_email or '').lower() for indicator in system_indicators):
            is_system_message = True
            print(f"Skipping system sender message: {sender_email}")
            
        if is_system_message:
            # Mark as processed to avoid future processing attempts
            ProcessedEmail.objects.create(
                message_id=message_id,
                channel=email_channel.channel
            )
            return
        
        # Get subject
        subject = headers.get('Subject', '')
        
        # Get message body
        body = extract_message_body(message)
        
        # Skip emails with empty bodies
        if not body.strip():
            print(f"Skipping email with empty body from {sender_email}")
            # Mark as processed to avoid future processing attempts
            ProcessedEmail.objects.create(
                message_id=message_id,
                channel=email_channel.channel
            )
            return
            
        # Check for system-generated content in the body
        system_content = [
            "I'm sorry, I could not find that information",
            "mailer-daemon",
            "delivery status notification",
            "automatic reply",
            "out of office"
        ]
        
        if any(indicator.lower() in body.lower() for indicator in system_content):
            print(f"Skipping message with system content: {message_id}")
            # Mark as processed to avoid future processing attempts
            ProcessedEmail.objects.create(
                message_id=message_id,
                channel=email_channel.channel
            )
            return
        
        # Get recipient email from To header
        to_header = headers.get('To', '')
        recipient_email = extract_email_address(to_header)
        
        # We should never get here with empty sender_email due to earlier checks,
        # but just in case, skip the message
        if not sender_email or sender_email.strip() == '':
            print(f"WARNING: Empty sender email detected after initial checks, skipping")
            ProcessedEmail.objects.create(
                message_id=message_id,
                channel=email_channel.channel
            )
            return
        
        print(f"Processing new email from {sender_email}: {subject}")
        
        # Create a request-like object to pass to the handler
        class DummyRequest:
            def __init__(self, body_data):
                self.body = json.dumps(body_data).encode('utf-8')
        
        # Prepare the request data
        request_data = {
            'sender_email': sender_email,
            'recipient_email': email_channel.email_address,
            'subject': subject,
            'body': body,
            'message_id': message_id
        }
        
        # Create a dummy request
        dummy_request = DummyRequest(request_data)
        
        # Get the chatbot ID
        chatbot_id = email_channel.channel.chatbot.chatbot_id
        
        # Process the email using a custom EmailHandler implementation
        # Since EmailHandler has been removed, we'll create a custom handler based on ChannelResponseHandler
        from chat.channels_response_views import ChannelResponseHandler
        
        class EmailHandler(ChannelResponseHandler):
            def __init__(self, request, chatbot_id):
                super().__init__(request, 'email', chatbot_id)
                self.email_channel = None
                self.subject = None
                self.sender_email = None
                self.from_email = None  # Added to support the new Conversation model field
                self.message_id = None
                
            def extract_data(self):
                try:
                    # Extract data from the request
                    request_data = json.loads(self.request.body.decode('utf-8'))
                    print(f"Email request data: {request_data}")
                    
                    self.sender_email = request_data.get('sender_email')
                    # For email channel, we'll use both from_number and from_email
                    self.from_number = "email:" + self.sender_email  # Legacy field, prefixed to avoid conflicts
                    self.from_email = self.sender_email  # New field specifically for email
                    self.body = request_data.get('body')
                    self.subject = request_data.get('subject')
                    self.message_id = request_data.get('message_id')
                    
                    # Validate required fields
                    if not self.sender_email:
                        print("ERROR: Missing sender_email in request data")
                        return False
                        
                    if not self.body:
                        print("ERROR: Missing body in request data")
                        return False
                    
                    # Handle potential duplicates by checking if there are existing conversations
                    # with this email address in either from_email or from_number fields
                    try:
                        # This is just a check - actual conversation retrieval happens in the handle method
                        existing_conversations = Conversation.objects.filter(
                            chatbot=self.chatbot,
                            channel=self.channel
                        ).filter(
                            # Check both fields for the email address
                            models.Q(from_email=self.from_email) | 
                            models.Q(from_number=self.from_email) | 
                            models.Q(from_number=self.from_number)
                        ).count()
                        
                        if existing_conversations > 1:
                            print(f"NOTE: Found {existing_conversations} existing conversations for {self.from_email}")
                    except Exception as e:
                        print(f"WARNING: Error checking for duplicate conversations: {str(e)}")
                    
                    print(f"Successfully extracted email data from: {self.sender_email}, subject: {self.subject}")
                    return True
                except Exception as e:
                    print(f"ERROR: Error extracting data from email request: {str(e)}")
                    return False
            
            def send_response(self, response_text):
                try:
                    # Get the email channel
                    self.email_channel = EmailChannel.objects.get(channel=self.channel)
                    
                    # Debug logging to trace the issue
                    print(f"Attempting to send email response to: {self.sender_email}")
                    print(f"Subject: {self.subject}")
                    
                    # Ensure we have a valid recipient email
                    if not self.sender_email or self.sender_email.strip() == '':
                        print("ERROR: No recipient email address found")
                        return False
                    
                    # Send the response via Gmail
                    subject = f"Re: {self.subject}" if self.subject and not self.subject.lower().startswith('re:') else self.subject
                    if not subject or subject.strip() == '':
                        subject = "Re: Your email to the chatbot"
                    
                    send_gmail(self.email_channel, self.sender_email, subject, response_text, self.message_id)
                    print(f"Successfully sent email response to {self.sender_email}")
                    
                    return True
                except Exception as e:
                    print(f"ERROR: Error sending email response: {str(e)}")
                    return False
            
            def get_immediate_response(self):
                # For email, we don't need an immediate response like with Twilio
                return HttpResponse("Email processing started", status=200)
        
        # Create and use the handler
        handler = EmailHandler(dummy_request, str(chatbot_id))
        handler.handle()
        
        # Mark the email as processed - use get_or_create to handle race conditions
        # where multiple processes might try to create the same record
        ProcessedEmail.objects.get_or_create(
            message_id=message_id,
            defaults={'channel': email_channel.channel}
        )
        
        # Mark the message as read in Gmail
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        logger.info(f"Successfully processed email from {sender_email}")
        
    except Exception as e:
        logger.error(f"Error processing Gmail message {message_id}: {str(e)}")




def extract_email_address(header_value):
    """Extract the email address from a header value."""
    import re
    match = re.search(r'<(.+?)>', header_value)
    if match:
        return match.group(1)
    return header_value




def extract_message_body(message):
    """Extract the text body from a Gmail message."""
    try:
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body_data = part['body'].get('data', '')
                    if body_data:
                        decoded_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        return clean_email_body(decoded_body)
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body_data = message['payload']['body']['data']
            decoded_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            return clean_email_body(decoded_body)
        
        return ""
        
    except Exception as e:
        logger.error(f"Error extracting message body: {str(e)}")
        return ""




def clean_email_body(body):
    """Clean up the email body by removing quoted replies and signatures."""
    import re
    
    # Split into lines
    lines = body.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip quoted lines (common in email replies)
        if line.strip().startswith('>'): 
            continue
        # Stop at common signature markers
        if line.strip() == '-- ' or re.match(r'^-{3,}$', line.strip()):
            break
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()




def send_gmail(email_channel, to_email, subject, body, in_reply_to=None):
    """Send an email using the Gmail API."""
    try:
        # Validate input parameters
        if not to_email or to_email.strip() == '':
            print("ERROR: Cannot send email: recipient email address is empty")
            return False
            
        if not subject or subject.strip() == '':
            print("WARNING: Email subject is empty, using default subject")
            subject = "Response from Chatbot"
            
        if not body or body.strip() == '':
            print("ERROR: Cannot send email: message body is empty")
            return False
            
        print(f"Preparing to send email to: {to_email}, subject: {subject}")
        
        # Get fresh credentials
        credentials = refresh_gmail_credentials(email_channel)
        if not credentials:
            print(f"ERROR: Failed to refresh credentials for {email_channel.email_address}")
            return False
        
        # Build the Gmail API service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Create the message
        message = create_message(email_channel.email_address, to_email, subject, body, in_reply_to)
        
        # Send the message
        send_message(service, 'me', message)
        
        print(f"Successfully sent email to {to_email}")
        return True
        
    except Exception as e:
        print(f"ERROR: Error sending Gmail: {str(e)}")
        return False




def create_message(sender, to, subject, message_text, in_reply_to=None):
    """Create a message for the Gmail API."""
    from email.mime.text import MIMEText
    import base64
    
    # Create message
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    
    # Handle subject for replies
    if in_reply_to and not subject.lower().startswith('re:'):
        message['subject'] = f"Re: {subject}"
    else:
        message['subject'] = subject
    
    # Add in-reply-to header if applicable
    if in_reply_to:
        message['In-Reply-To'] = in_reply_to
        message['References'] = in_reply_to
    
    # Encode the message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    return {'raw': encoded_message}




def send_message(service, user_id, message):
    """Send a message via the Gmail API."""
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        return message
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise




# Gmail Handler for channels_response_views.py
class GmailHandler(ChannelResponseHandler):
    def __init__(self, request, chatbot_id):
        super().__init__(request, 'email', chatbot_id)
        self.email_channel = None
        self.subject = None
        self.sender_email = None
        self.message_id = None
    
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
        """Send an email response back to the user via Gmail API."""
        try:
            # Create subject as a reply
            if self.subject and not self.subject.lower().startswith('re:'):
                subject = f"Re: {self.subject}"
            else:
                subject = self.subject or "Response from Chatbot"
            
            # Send the email using Gmail API
            return send_gmail(
                self.email_channel,
                self.from_number,
                subject,
                response_text,
                self.message_id
            )
        except Exception as e:
            logger.error(f"Error sending email response: {str(e)}")
            return False
    
    def get_immediate_response(self):
        """For email, we don't need an immediate response like with Twilio."""
        return JsonResponse({"status": "processing"})