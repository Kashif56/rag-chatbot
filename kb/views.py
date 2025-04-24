from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import DataSource
from chat.pinecone import initialize_pinecone

from django.db import transaction
import uuid
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from django.utils.text import slugify

from chat.models import Chatbot
from .models import KnowledgeBase, DataSource




def knowledge_bases(request):
    chatbots = Chatbot.objects.filter(user=request.user)
    knowledge_bases = KnowledgeBase.objects.filter(chatbot__user=request.user)
    data_sources = DataSource.objects.filter(kb__chatbot__user=request.user)

    url_sources_count = data_sources.filter(source_type='url').count()
    file_sources_count = data_sources.filter(source_type='file').count()

    context = {
        'chatbots': chatbots,
        'knowledge_bases': knowledge_bases,
        'data_sources': data_sources,
        'url_sources_count': url_sources_count,
        'file_sources_count': file_sources_count
    }
    return render(request, 'dashboard/knowledge_base.html', context)


def knowledge_base_detail(request, kb_id):
    knowledge_base = get_object_or_404(KnowledgeBase, knowledge_base_id=kb_id)
    data_sources = DataSource.objects.filter(kb=knowledge_base)

    context = {
        'data_sources': data_sources,
        'knowledge_base': knowledge_base
    }
    return render(request, 'dashboard/kb_datasources.html', context)



@login_required
@require_POST
@csrf_exempt
@transaction.atomic
def add_data_source(request, kb_id=None):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        initialize_pinecone()
        knowledge_base = KnowledgeBase.objects.get(knowledge_base_id=kb_id)

        source_type = request.POST.get('source_type')
        
        data_source = DataSource(
            kb=knowledge_base,
            source_type=source_type,
            text_title=request.POST.get(f'{source_type}_title', '')
        )
        
        documents = []
        url_contents = {}  # Will store URL to content mapping
        
        if source_type == 'file':
            file_obj = request.FILES.get('file')
            if not file_obj:
                return JsonResponse({'error': 'No file uploaded'}, status=400)
            
            data_source.file = file_obj
            
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, file_obj.name)
            
            with open(temp_file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
            
            from chat.pinecone import load_documents, process_documents, upsert_documents, get_documents_text
            try:
                documents = load_documents(temp_file_path)
                
                data_source.text_content = get_documents_text(documents)[:100000]  # Limit text size if needed
                if not data_source.text_content:
                    data_source.text_content = f"File: {file_obj.name} (No content extracted)"
                
                    # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                # Remove temp directory
                os.rmdir(temp_dir)
            except Exception as e:
                # Make sure to clean up even if there's an error
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                return JsonResponse({'error': f'Error processing file: {str(e)}'}, status=400)
            
        elif source_type == 'url':
            url = request.POST.get('url')
            if not url:
                return JsonResponse({'error': 'URL is required'}, status=400)
            
            if not (url.startswith('http://') or url.startswith('https://')):
                url = 'https://' + url
            
            # Scrape URL with Langchain
            from chat.pinecone import load_documents, process_documents, upsert_documents, get_documents_text
            try:
                follow_links = request.POST.get('follow_links') == 'true'
                max_depth = int(request.POST.get('max_depth', 1))
                result = load_documents(url, follow_links=follow_links, max_depth=max_depth)
                
                # Handle the new return format (documents, url_contents)
                if isinstance(result, tuple) and len(result) == 2:
                    documents, url_contents = result
                else:
                    documents = result
                    url_contents = {}
                
                # Create main data source for the primary URL
                data_source.url = url
                if url in url_contents:
                    data_source.text_content = url_contents[url][:100000]  # Limit text size if needed
                else:
                    # Try to extract content from documents with matching URL
                    matching_docs = [doc for doc in documents if doc.metadata.get('source') == url]
                    if matching_docs:
                        data_source.text_content = matching_docs[0].page_content[:100000]
                    else:
                        data_source.text_content = f"URL content from: {url} (No content extracted)"
                
                # Save the primary data source
                data_source.save()
                
                # Create namespace for the knowledge base
                namespace = knowledge_base.chatbot.name
                
                # Process and embed documents for the primary URL
                primary_docs = [doc for doc in documents if doc.metadata.get('source') == url]
                if primary_docs:
                    primary_chunks = process_documents(primary_docs)
                    if primary_chunks:
                        vector_store, uuids = upsert_documents(primary_chunks, namespace=namespace)
                        data_source.chunk_ids = uuids
                        data_source.save()
                
                # Create additional data sources for each followed URL
                child_url_sources = []
                for scraped_url, content in url_contents.items():
                    if scraped_url != url:  # Skip the main URL which is already saved
                        url_title = f"From {scraped_url}"
                        try:
                            # Extract domain for title
                            parsed_url = urlparse(scraped_url)
                            if parsed_url.netloc:
                                url_title = f"From {parsed_url.netloc}"
                        except:
                            pass
                            
                        child_source = DataSource(
                            kb=knowledge_base,
                            source_type='url',
                            url=scraped_url,
                            text_title=url_title,
                            text_content=content[:100000]  # Limit text size if needed
                        )
                        child_source.save()
                        
                        # Process and embed documents for this child URL
                        child_docs = [doc for doc in documents if doc.metadata.get('source') == scraped_url]
                        if child_docs:
                            child_chunks = process_documents(child_docs)
                            if child_chunks:
                                vector_store, child_uuids = upsert_documents(child_chunks, namespace=namespace)
                                child_source.chunk_ids = child_uuids
                                child_source.save()
                        
                        child_url_sources.append(child_source)
                        
                # Return success with count of child sources
                return JsonResponse({
                    'status': 'success',
                    'message': 'Data source added successfully',
                    'data_source_id': data_source.id,
                    'chunks_processed': len([doc for doc in documents if doc.metadata.get('source') == url]),
                    'child_sources': len(child_url_sources)
                })
                
            except Exception as e:
                return JsonResponse({'error': f'Error processing URL: {str(e)}'}, status=400)
            
        elif source_type == 'text':
            text_content = request.POST.get('text_content')
            if not text_content:
                return JsonResponse({'error': 'Text content is required'}, status=400)
            
            data_source.text_content = text_content
            
            # Process text with Langchain
            from chat.pinecone import load_documents, process_documents, upsert_documents, get_documents_text
            try:
                documents = load_documents('text', content=text_content)
            except Exception as e:
                return JsonResponse({'error': f'Error processing text: {str(e)}'}, status=400)
        
        else:
            return JsonResponse({'error': 'Invalid source type'}, status=400)
        
        # Save data source to database if not already saved
        if source_type != 'url' or not data_source.id:
            data_source.save()
        
        # Process documents and create vector embeddings
        if documents:
            try:
                chunks = process_documents(documents)
                
                if not chunks or len(chunks) == 0:
                    print(f"Warning: No chunks created from documents for source: {data_source.id}")
                    return JsonResponse({
                        'status': 'warning',
                        'message': 'Data source added but no content chunks could be extracted',
                        'data_source_id': data_source.id
                    })
                
                # Create a namespace using the data source ID consistently
                namespace = knowledge_base.chatbot.name
                
                # Upsert to vector store and handle any errors
                try:
                    vector_store, uuids = upsert_documents(chunks, namespace=namespace)
                    
                    # Store the chunk UUIDs in the DataSource model
                    data_source.chunk_ids = uuids
                    data_source.save()
                  
                    return JsonResponse({
                        'success': True,
                        'status': 'success',
                        'message': 'Data source added successfully',
                        'data_source_id': data_source.id,
                        'chunks_processed': len(chunks),
                        'child_sources': len(url_contents) - 1 if source_type == 'url' and url_contents else 0,
                        'redirect_url': reverse('kb:knowledge_base_detail', args=[knowledge_base.knowledge_base_id])
                    })
                except Exception as e:
                    # Log the vectorization error but don't delete the data source
                    print(f"Error creating vector embeddings: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    # Return partial success - data is saved but not vectorized
                    return JsonResponse({
                        'status': 'warning',
                        'message': f'Data source added but vectorization failed: {str(e)}',
                        'data_source_id': data_source.id
                    })
            except Exception as e:
                print(f"Error processing documents: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Return partial success - data is saved but not processed
                return JsonResponse({
                    'status': 'warning',
                    'message': f'Data source added but document processing failed: {str(e)}',
                    'data_source_id': data_source.id
                })
        else:
            print(f"No documents extracted for source: {data_source.id}")
            return JsonResponse({
                'status': 'warning',
                'message': 'Data source added but no documents were processed',
                'data_source_id': data_source.id
            })
            
    except KnowledgeBase.DoesNotExist:
        return JsonResponse({'error': 'Knowledge base not found'}, status=404)
    except Exception as e:
        print(e)
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@transaction.atomic
def delete_data_source(request, source_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data_source = DataSource.objects.get(id=source_id)
        
        kb_id = data_source.kb.knowledge_base_id
        chatbot = data_source.kb.chatbot
        
        try:
            from chat.pinecone import pc, INDEX_NAME
            namespace = f"{chatbot.name}"
            index = pc.Index(INDEX_NAME)
            
            if data_source.chunk_ids:
                deleted_vectors = index.delete(ids=data_source.chunk_ids, namespace=namespace)
              
        except Exception as e:
            print(f"Error deleting vectors for source {source_id}: {str(e)}")
        
        data_source.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Data source deleted successfully',
            'redirect_url': reverse('kb:knowledge_base_detail', args=[kb_id])
        })
        
    except DataSource.DoesNotExist:
        return JsonResponse({'error': 'Data source not found', 'success': False}, status=404)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e),
            'redirect_url': reverse('kb:knowledge_base_detail', args=[kb_id])
        })


def source_detail(request, source_id):
    try:
        data_source = DataSource.objects.get(id=source_id)
        return render(request, 'dashboard/source_detail.html', {
            'source': data_source,
            'knowledge_base': data_source.kb
        })
        
    except DataSource.DoesNotExist:
       
        messages.error(request, 'Data source not found')
        return redirect('kb:knowledge_base')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('kb:knowledge_base')
        
        
        

















