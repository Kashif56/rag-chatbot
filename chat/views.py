from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
import logging
from .pinecone import PineconeClient, generate_response
from kb.models import DataSource  # Import DataSource model to get original text

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def chat_view(request):
    return render(request, 'chat/chat.html')

@login_required
@require_http_methods(["POST"])
def send_message(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)
        
        pc = PineconeClient()
        
        # Generate embedding for the user query
        query_embedding = pc.embeddings([user_message])
        
        # Search for relevant content
        results = pc.query(
            embedding=query_embedding,
            namespace=f"{request.user.username}",
            top_k=5
        )
        
        # Extract contexts from the search results
        contexts = []
        
        for match in results.get('matches', []):
            if match.get('score', 0) > 0.5:  # Only use high-relevance matches
                metadata = match.get('metadata', {})
                
                # First check for the text_content field which should be there now
                if 'text_content' in metadata:
                    context = metadata['text_content']
                    
                    # Add source information if available
                    if 'source_name' in metadata:
                        context += f"\nSource: {metadata['source_name']}"
                    
                    # Add page title information if available
                    if 'page_title' in metadata:
                        context += f"\nPage Title: {metadata['page_title']}"
                    
                    contexts.append(context)
                    continue
                
                # Fallback to older fields or database retrieval if needed
                if 'chunk' in metadata:
                    contexts.append(metadata['chunk'])
                    continue
                    
       
        if contexts:
            bot_response = generate_response(contexts, user_message)
        else:
            bot_response = "I don't have enough information to answer that question. Please try asking something related to the documents you've uploaded."
        
        return JsonResponse({'response': bot_response})
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'An error occurred while processing your message'}, status=500)
