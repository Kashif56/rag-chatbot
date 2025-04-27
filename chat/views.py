from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
from chat.models import Chatbot, Channel, EmailChannel, WhatsAppChannel, MessengerChannel, Message, Conversation
from kb.models import KnowledgeBase, DataSource
from django.db.utils import OperationalError
from chat.google import get_authorization_url



@login_required
def dashboard(request):
    chatbots = Chatbot.objects.filter(user=request.user)
    channels = Channel.objects.filter(chatbot__in=chatbots)
    
    conversations = Conversation.objects.filter(chatbot__in=chatbots)

    context = {
        'chatbots': chatbots,
        'channels': channels,
        'conversations': conversations
    }
    return render(request, 'dashboard/dashboard.html', context)



@login_required
def create_chatbot_page(request):
    return render(request, 'dashboard/create_chatbot.html')


@login_required
@require_POST
@csrf_exempt
@transaction.atomic
def add_chatbot(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        description = data.get('description', '')
        prompt = data.get('prompt', '')
        llm_provider = data.get('llm_provider')
        llm_model = data.get('llm_model')
        
        # Basic validation
        if not llm_provider or not llm_model:
            return JsonResponse({
                'success': False,
                'error': 'LLM provider and model are required'
            }, status=400)

        if not name:
            name = "New Chatbot"

        # Create the chatbot
        chatbot = Chatbot.objects.create(
            user=request.user,
            name=name,
            description=description,
            prompt=prompt,
            llm_provider=llm_provider,
            llm_model=llm_model
        )

        # Process channels
        channels = data.get('channels', [])
        
        for channel_data in channels:
            # Validate channel data
            if 'type' not in channel_data:
                continue
                
            channel = Channel.objects.create(
                chatbot=chatbot,
                channel_type=channel_data['type']
            )
            
            if channel_data['type'] == 'email':
                EmailChannel.objects.create(
                    channel=channel,
                    email_address=channel_data.get('email_address', None),
                    provider=channel_data.get('provider', None),
                    access_token=channel_data.get('access_token', None),
                    refresh_token=channel_data.get('refresh_token', None),
                    smtp_server=channel_data.get('smtp_server', None),
                    smtp_port=channel_data.get('smtp_port', None),
                    imap_server=channel_data.get('imap_server', None)
                )
            elif channel_data['type'] == 'whatsapp' or channel_data['type'] == 'sms':
                WhatsAppChannel.objects.create(
                    channel=channel,
                    twilio_account_sid=channel_data.get('twilio_account_sid', ''),
                    twilio_auth_token=channel_data.get('twilio_auth_token', ''),
                    twilio_phone_number=channel_data.get('twilio_phone_number', '')
                )
            elif channel_data['type'] == 'messenger':
                MessengerChannel.objects.create(
                    channel=channel,
                    page_id=channel_data.get('page_id', ''),
                    page_name=channel_data.get('page_name', ''),
                    access_token=channel_data.get('access_token', '')
                )

        return JsonResponse({
            'success': True,
            'chatbot': chatbot.chatbot_id
        })
        
    except json.JSONDecodeError:
        print("Invalid JSON data")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        print(f"Error creating chatbot: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)




@login_required
def edit_chatbot_page(request, chatbot_id):
    chatbot = Chatbot.objects.get(chatbot_id=chatbot_id)
    channels = Channel.objects.filter(chatbot=chatbot)
    channels_data = []
    for channel in channels:
        if channel.channel_type == 'email':
            email_config = EmailChannel.objects.get(channel=channel)
            if email_config.provider == 'gmail' or email_config.provider == 'outlook':
                channels_data.append({
                    'channel_type': channel.get_channel_type_display(),
                    'channel_id': channel.channel_id,
                    'email_address': email_config.email_address,
                    'provider': email_config.provider,
                    'access_token': email_config.access_token,
                    'refresh_token': email_config.refresh_token,
                })
 
            elif email_config.provider == 'smtp' or email_config.provider == 'imap':
                channels_data.append({
                    'channel_type': channel.get_channel_type_display(),
                    'channel_id': channel.channel_id,
                    'email_address': email_config.email_address,
                    'provider': email_config.provider,
                    'smtp_server': email_config.smtp_server,
                    'smtp_port': email_config.smtp_port,
                    'imap_server': email_config.imap_server,
                    'imap_port': email_config.imap_port,
                })
            
        elif channel.channel_type == 'whatsapp' or channel.channel_type == 'sms':
            whatsapp_config = WhatsAppChannel.objects.get(channel=channel)
            channels_data.append({
                'channel_type': channel.get_channel_type_display(),
                'channel_id': channel.channel_id,
                'twilio_account_sid': whatsapp_config.twilio_account_sid,
                'twilio_auth_token': whatsapp_config.twilio_auth_token,
                'twilio_phone_number': whatsapp_config.twilio_phone_number,
            })
        elif channel.channel_type == 'messenger':
            messenger_config = MessengerChannel.objects.get(channel=channel)
            channels_data.append({
                'channel_type': channel.get_channel_type_display(),
                'channel_id': channel.channel_id,
                'page_id': messenger_config.page_id,
                'page_name': messenger_config.page_name,
                'access_token': messenger_config.access_token,
            })
    
    # Get knowledge base and data sources for this chatbot
    knowledge_base = None
    data_sources = []
    try:
        knowledge_base = KnowledgeBase.objects.get(chatbot=chatbot)
        data_sources = DataSource.objects.filter(kb=knowledge_base)
    except KnowledgeBase.DoesNotExist:
        # No knowledge base exists for this chatbot
        pass
    
    context = {
        'chatbot': chatbot,
        'channels': channels_data,
        'knowledge_base': knowledge_base,
        'data_sources': data_sources,
    }
    
    return render(request, 'dashboard/chatbot_detail.html', context)


@login_required
@require_POST
@csrf_exempt
@transaction.atomic
def update_chatbot(request, chatbot_id):
    try:
        data = json.loads(request.body)
        chatbot_id = data.get('chatbot_id')
        name = data.get('name')
        description = data.get('description', '')
        prompt = data.get('prompt', '')
        llm_provider = data.get('llm_provider')
        llm_model = data.get('llm_model')

        chatbot = Chatbot.objects.get(chatbot_id=chatbot_id)
        chatbot.name = name
        chatbot.description = description
        chatbot.prompt = prompt
        chatbot.llm_provider = llm_provider
        chatbot.llm_model = llm_model
        chatbot.save()

        # Process channels
        channels = data.get('channels', [])
        
        for channel_data in channels:
            # Validate channel data
            if 'type' not in channel_data:
                continue
                
            channel = Channel.objects.get(chatbot=chatbot, channel_type=channel_data['type'])
            
            if channel_data['type'] == 'email':
                EmailChannel.objects.create(
                    channel=channel,
                    email_address=channel_data.get('email_address', None),
                    provider=channel_data.get('provider', None),
                    access_token=channel_data.get('access_token', None),
                    refresh_token=channel_data.get('refresh_token', None),
                    smtp_server=channel_data.get('smtp_server', None),
                    smtp_port=channel_data.get('smtp_port', None),
                    imap_server=channel_data.get('imap_server', None)
                )
            elif channel_data['type'] == 'whatsapp' or channel_data['type'] == 'sms':
                WhatsAppChannel.objects.create(
                    channel=channel,
                    twilio_account_sid=channel_data.get('twilio_account_sid', ''),
                    twilio_auth_token=channel_data.get('twilio_auth_token', ''),
                    twilio_phone_number=channel_data.get('twilio_phone_number', '')
                )
            elif channel_data['type'] == 'messenger':
                MessengerChannel.objects.create(
                    channel=channel,
                    page_id=channel_data.get('page_id', ''),
                    page_name=channel_data.get('page_name', ''),
                    access_token=channel_data.get('access_token', '')
                )

        return JsonResponse({
            'success': True,
            'chatbot': chatbot.chatbot_id
        })

    except Exception as e:
        print(f"Error updating chatbot: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)



@login_required
@require_POST
@csrf_exempt
@transaction.atomic
def update_channel(request, channel_id):
    try:
        data = json.loads(request.body)
        channel_type = data.get('channel_type')
        channel = Channel.objects.get(channel_id=channel_id)
        if channel_type.lower() == 'email':
            email_address = data.get('email_address')
            provider = data.get('provider')
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token')
            smtp_server = data.get('smtp_server')
            smtp_port = data.get('smtp_port')
            imap_server = data.get('imap_server')
            imap_port = data.get('imap_port')
        elif channel_type.lower() == 'whatsapp' or channel_type.lower() == 'sms':
            twilio_account_sid = data.get('twilio_account_sid')
            twilio_auth_token = data.get('twilio_auth_token')
            twilio_phone_number = data.get('twilio_phone_number')
        elif channel_type.lower() == 'messenger':
            page_id = data.get('page_id')
            page_name = data.get('page_name')
            access_token = data.get('access_token')
        
        channel.channel_type = channel_type.lower()
        channel.save()
        
        if channel_type.lower() == 'email':
            email_config = channel.email_config
            email_config.email_address = email_address
            email_config.provider = provider
            email_config.access_token = access_token
            email_config.refresh_token = refresh_token
            email_config.smtp_server = smtp_server
            email_config.smtp_port = smtp_port
            email_config.imap_server = imap_server
            email_config.imap_port = imap_port
            email_config.save()
        elif channel_type.lower() == 'whatsapp' or channel_type.lower() == 'sms':
            whatsapp_config = channel.whatsapp_config
            whatsapp_config.twilio_account_sid = twilio_account_sid
            whatsapp_config.twilio_auth_token = twilio_auth_token
            whatsapp_config.twilio_phone_number = twilio_phone_number
            whatsapp_config.save()
        elif channel_type.lower() == 'messenger':
            messenger_config = channel.messenger_config
            messenger_config.page_id = page_id
            messenger_config.page_name = page_name
            messenger_config.access_token = access_token
            messenger_config.save()

        return JsonResponse({
            'success': True,
            'channel': channel.channel_id
        })
            
    
    except Exception as e:
        print(f"Error updating channel: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)

@login_required
@require_POST
@csrf_exempt
@transaction.atomic
def add_channel(request, chatbot_id):
    try:
        # Get request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        # Debug log
        print(f"Adding channel with data: {data}")
        
        # Get chatbot
        chatbot = Chatbot.objects.get(chatbot_id=chatbot_id)
        channel_type = data.get('channel_type')
        
        # Initialize variables to avoid NameError
        email_address = provider = access_token = refresh_token = smtp_server = smtp_port = imap_server = imap_port = None
        twilio_account_sid = twilio_auth_token = twilio_phone_number = None
        page_id = page_name = None
        
        # Get channel-specific data
        if channel_type and channel_type.lower() == 'email':
            email_address = data.get('email_address')
            provider = data.get('provider')
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token', '')  # Default to empty string if not provided
            smtp_server = data.get('smtp_server', '')
            smtp_port = data.get('smtp_port', '')
            imap_server = data.get('imap_server', '')
            imap_port = data.get('imap_port', '')
        
        elif channel_type and (channel_type.lower() == 'whatsapp' or channel_type.lower() == 'sms'):
            twilio_account_sid = data.get('twilio_account_sid')
            twilio_auth_token = data.get('twilio_auth_token')
            twilio_phone_number = data.get('twilio_phone_number')
        
        elif channel_type and channel_type.lower() == 'messenger':
            page_id = data.get('page_id')
            page_name = data.get('page_name')
            access_token = data.get('access_token')
        
        # Check if channel type is valid
        if not channel_type:
            return JsonResponse({
                'success': False,
                'error': 'Channel type is required'
            }, status=400)
            
        # Check if channel already exists
        if Channel.objects.filter(chatbot=chatbot, channel_type=channel_type).exists():
            return JsonResponse({
                'success': False,
                'error': f'{channel_type} channel already exists for this chatbot'
            }, status=400)
        
        # Create channel
        channel = Channel.objects.create(
            chatbot=chatbot,
            channel_type=channel_type  # Store the original channel_type value
        )
        
        # Normalize channel type for comparison
        channel_type_lower = channel_type.lower()
        
        # Create channel-specific record
        if channel_type_lower == 'email':
            if not email_address or not provider:
                channel.delete()  # Clean up the channel if data is incomplete
                return JsonResponse({
                    'success': False,
                    'error': 'Email address and provider are required for Email channel'
                }, status=400)
                
            EmailChannel.objects.create(
                channel=channel,
                email_address=email_address,
                provider=provider,
                access_token=access_token or '',
                refresh_token=refresh_token or '',
                smtp_server=smtp_server or '',
                smtp_port=smtp_port or '',
                imap_server=imap_server or '',
                imap_port=imap_port or ''
            )
            
        elif channel_type_lower == 'whatsapp' or channel_type_lower == 'sms':
            if not twilio_account_sid or not twilio_phone_number:
                channel.delete()  # Clean up the channel if data is incomplete
                return JsonResponse({
                    'success': False,
                    'error': 'Twilio Account SID and Phone Number are required'
                }, status=400)
                
            WhatsAppChannel.objects.create(
                channel=channel,
                twilio_account_sid=twilio_account_sid,
                twilio_auth_token=twilio_auth_token or '',
                twilio_phone_number=twilio_phone_number
            )
            
        elif channel_type_lower == 'messenger':
            if not page_id or not access_token:
                channel.delete()  # Clean up the channel if data is incomplete
                return JsonResponse({
                    'success': False,
                    'error': 'Page ID and Access Token are required for Messenger channel'
                }, status=400)
                
            MessengerChannel.objects.create(
                channel=channel,
                page_id=page_id,
                page_name=page_name or '',
                access_token=access_token
            )
        
        messages.success(request, f'{channel_type} channel added successfully')

        print(f'{channel_type} channel added successfully')
        
        return JsonResponse({
            'success': True,
            'channel_id': str(channel.channel_id),
            'message': f'{channel_type} channel added successfully'
        })
            
    except Chatbot.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Chatbot not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except OperationalError as e:
        # Handle database lock errors specifically
        print(f"Database operational error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'Database is currently busy. Please try again in a moment.'
        }, status=503)  # Service Unavailable
    except Exception as e:
        print(f"Error adding channel: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }, status=500)



@login_required
@transaction.atomic
def delete_channel(request, channel_id):
    try:
        # Get channel with appropriate locking
        channel = Channel.objects.select_for_update().get(channel_id=channel_id)
        
        # Store info for response before deletion
        channel_id_str = str(channel.channel_id)
        channel_type = channel.channel_type
        
        # Delete the channel
        channel.delete()
        
        # Add success message
        messages.success(request, f'{channel_type} channel deleted successfully')
        
        # Return success response
        return JsonResponse({
            'success': True,
            'channel_id': channel_id_str,
            'message': f'{channel_type} channel deleted successfully'
        })
    except Channel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Channel not found'
        }, status=404)
    except OperationalError as e:
        # Handle database lock errors
        print(f"Database operational error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'Database is currently busy. Please try again in a moment.'
        }, status=503)  # Service Unavailable
    except Exception as e:
        print(f"Error deleting channel: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }, status=500)

def public_conversation(request, chatbot_id):
    try:
        chatbot = Chatbot.objects.get(chatbot_id=chatbot_id)
        channels = Channel.objects.filter(chatbot=chatbot)
        
        # Get recent messages for this chatbot
        recent_messages = Message.objects.filter(
            conversation__chatbot=chatbot
        ).order_by('-created_at')[:10]
        
        context = {
            'chatbot': chatbot,
            'channels': channels,
            'recent_messages': recent_messages
        }
        return render(request, 'core/conversation.html', context)
    except Chatbot.DoesNotExist:
        return render(request, 'core/404.html', status=404)

@csrf_exempt
def chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        message = data.get('message')
        chatbot_id = data.get('chatbot_id')
        
        if not message or not chatbot_id:
            return JsonResponse({'error': 'Message and chatbot_id are required'}, status=400)
        
        # Get the chatbot
        chatbot = Chatbot.objects.get(chatbot_id=chatbot_id)
        channel = Channel.objects.get(chatbot=chatbot, channel_type='web')
        # Create or get conversation
        conversation, created = Conversation.objects.get_or_create(
            chatbot=chatbot,
            from_number=12345,
            channel=channel
        )
        
        # Save user message
        user_message = Message.objects.create(  
            conversation=conversation,
            content=message,
            role='user'
        )
        
        # Get conversation history for context
        conversation_history = Message.objects.filter(
            conversation=conversation
        ).order_by('created_at')[:10]  # Limit to last 10 messages for context
        
        # Format conversation history for the LLM
        formatted_history = []
        for msg in conversation_history:
            role = "user" if msg.role == 'user' else "assistant"
            formatted_history.append({"role": role, "content": msg.content})
        
     
        from chat.pinecone import create_rag_chain
        
        # Create the RAG chain with the chatbot's namespace
        rag_chain = create_rag_chain(chatbot, namespace=chatbot.name)
        
        # Pass the message and the full formatted history to the chain
        bot_response = rag_chain(message, formatted_history)
        
      
        # Save bot response
        bot_message = Message.objects.create(
            conversation=conversation,
            content=bot_response,
            role='assistant'
        )
        
        return JsonResponse({
            'response': bot_response,
            'message_id': str(bot_message.message_id)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Chatbot.DoesNotExist:
        return JsonResponse({'error': 'Chatbot not found'}, status=404)
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def gmail_auth(request, channel_id):
    """Initiate the Gmail OAuth2 authentication flow."""
    try:
        # Get the channel
        channel = Channel.objects.get(channel_id=channel_id)
        
        # Verify the channel belongs to the user
        if channel.chatbot.user != request.user:
            messages.error(request, "You don't have permission to access this channel.")
            return redirect('dashboard:dashboard')
        
        # Generate the authorization URL
        auth_url = get_authorization_url(request, channel_id)
        
        if not auth_url:
            messages.error(request, "Failed to generate Gmail authorization URL.")
            return redirect('dashboard:chatbot_detail', chatbot_id=channel.chatbot.chatbot_id)
        
        # Redirect to the Google authorization page
        return redirect(auth_url)
        
    except Channel.DoesNotExist:
        messages.error(request, "Channel not found.")
        return redirect('dashboard:dashboard')
    except Exception as e:
        messages.error(request, f"Error initiating Gmail authentication: {str(e)}")
        return redirect('dashboard:dashboard')
