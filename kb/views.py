from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import DataSource
from chat.pinecone import chunk_text, PineconeClient
from django.db import transaction
import uuid
from .utils import extract_pdf_text, extract_docx_text, extract_txt_text, extract_text_from_url
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

# Saving the Data Source
@login_required
@transaction.atomic
def add_data_source(request):
    if request.method == 'POST':
        # Get the source type to determine how to process the data
        source_type = request.POST.get('source_type')
        
        # Log request data for debugging
        logger.debug(f"Processing data source request of type: {source_type}")
        logger.debug(f"POST data: {dict(request.POST)}")
        logger.debug(f"FILES data: {dict(request.FILES)}")
        
        text_title = request.POST.get('text_title')
        text_content = request.POST.get('text_content')
        url = request.POST.get('url')
        scrap_interal_pages = request.POST.get('scrap_interal_pages') == 'on'
        file = request.FILES.get('file')
        
        source_name = None
        extracted_text = None
        extracted_pages = None

        # Extract text based on source type
        try:
            # URL data source
            if source_type == 'url' and url:
                source_type = "url"
                source_name = url
                
                # extract_text_from_url now returns a list of page data dictionaries
                page_data_list = extract_text_from_url(url, scrap_interal_pages)
                
                # Store the structured data for later processing
                extracted_pages = page_data_list
                
                # For database storage, we'll create a combined text representation
                if scrap_interal_pages and len(page_data_list) > 1:
                    # Join all texts with page information
                    combined_text = "\n\n".join([
                        f"Page: {page['title']}\nURL: {page['url']}\n\n{page['text']}" 
                        for page in page_data_list if page['status'] == 'success'
                    ])
                    extracted_text = combined_text
                    
                    # Create a title with page count
                    text_title = f"Website: {url} (with {len(page_data_list)} pages)"
                else:
                    # Just use the text from the main URL
                    main_page = next((page for page in page_data_list if page.get('is_main_page')), page_data_list[0])
                    extracted_text = main_page['text']
                    text_title = f"Website: {main_page['title'] or url}"
            
            # File data source
            elif source_type == 'file' and file:
                if file.name.lower().endswith('.pdf'):
                    source_type = "pdf"
                    extracted_text = extract_pdf_text(file)
                elif file.name.lower().endswith('.docx'):
                    source_type = "docx"
                    extracted_text = extract_docx_text(file)
                elif file.name.lower().endswith('.txt'):
                    source_type = "txt"
                    extracted_text = extract_txt_text(file)
                else:
                    return JsonResponse({'error': 'Unsupported file type. Only PDF, DOCX, and TXT files are supported.'}, status=400)
                source_name = file.name
            
            # Text input data source
            elif source_type == 'text' and text_title and text_content:
                source_type = "text"
                source_name = text_title
                extracted_text = text_content
            
            # Invalid data
            else:
                return JsonResponse({'error': 'Please provide a valid data source with all required fields.'}, status=400)

        except Exception as e:
            logger.error(f"Error processing data source: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Error processing data source: {str(e)}'}, status=500)

        # Save to database
        try:
            # Create metadata for storage
            metadata = {}
            
            if extracted_pages:
                # Store the structured page data as metadata
                metadata = {
                    'page_count': len(extracted_pages),
                    'success_count': sum(1 for page in extracted_pages if page['status'] == 'success'),
                    'error_count': sum(1 for page in extracted_pages if page['status'] == 'error'),
                    'source_urls': [page['url'] for page in extracted_pages]
                }
            
            data_source = DataSource(
                user=request.user,
                url=url if url else None,
                file=file if file else None,
                text_title=text_title if text_title else source_name,
                text_content=extracted_text,
                metadata=json.dumps(metadata)
            )
            data_source.save()
            logger.info(f"Saved data source with ID: {data_source.id}")
        except Exception as e:
            logger.error(f"Error saving data source to database: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Error saving to database: {str(e)}'}, status=500)

        # Process for Pinecone
        try:
            pc = PineconeClient()
            
            # If we have structured page data, process each page separately
            if extracted_pages and len(extracted_pages) > 0:
                total_chunks = 0
                
                # Process each page individually
                for page_index, page_data in enumerate(extracted_pages):
                    if page_data['status'] != 'success' or not page_data['text']:
                        continue
                        
                    # Chunk the page text
                    page_chunks = chunk_text(page_data['text'])
                    total_chunks += len(page_chunks)
                    
                    if not page_chunks:
                        continue
                    
                    # Get embeddings for chunks
                    embeddings = pc.embeddings(page_chunks)
                    
                    # Upsert each chunk with metadata
                    for chunk_idx, (chunk, embedding) in enumerate(zip(page_chunks, embeddings)):
                        chunk_id = f"{data_source.id}_{page_index}_{chunk_idx}_{uuid.uuid4().hex[:8]}"
                        
                        chunk_data = {
                            "id": chunk_id,
                            "metadata": {
                                "data_source_id": str(data_source.id),
                                "user_id": str(request.user.id),
                                "source_type": source_type,
                                "source_name": source_name,
                                "page_title": page_data['title'],
                                "page_url": page_data['url'],
                                "is_main_page": page_data.get('is_main_page', False),
                                "page_index": page_index,
                                "chunk_index": chunk_idx,
                                "chunk_id": chunk_id
                            }
                        }
                        pc.upsert(chunk_data, embedding, namespace=f"{request.user.username}")
                
                logger.info(f"Successfully processed {total_chunks} chunks from {len(extracted_pages)} pages for data source ID: {data_source.id}")
                return JsonResponse({
                    'message': 'Data source added successfully',
                    'data_source_id': str(data_source.id),
                    'page_count': len(extracted_pages),
                    'chunk_count': total_chunks
                }, status=200)
            
            # Regular text chunking for non-page data
            else:
                # Chunk text and embed for Pinecone
                chunks = chunk_text(extracted_text)
                
                # Process chunks in batches for efficiency
                batch_size = 10
                for i in range(0, len(chunks), batch_size):
                    batch_chunks = chunks[i:i+batch_size]
                    embeddings = pc.embeddings(batch_chunks)
                    
                    # Upsert each chunk with proper metadata
                    for j, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
                        chunk_index = i + j
                        chunk_data = {
                            "id": f"{data_source.id}_{chunk_index}_{uuid.uuid4().hex[:8]}",
                            "metadata": {
                                "title": data_source.text_title,
                                "source_type": source_type,
                                "source_name": source_name,
                                "chunk_index": chunk_index,
                                "total_chunks": len(chunks),
                                "data_source_id": str(data_source.id),
                                "user_id": str(request.user.id)
                            }
                        }
                        pc.upsert(chunk_data, embedding, namespace=f"{request.user.username}")
                
                logger.info(f"Successfully processed {len(chunks)} chunks for data source ID: {data_source.id}")
                return JsonResponse({
                    'message': 'Data source added successfully',
                    'data_source_id': str(data_source.id),
                    'chunk_count': len(chunks)
                }, status=200)
                
        except Exception as e:
            logger.error(f"Error upserting to Pinecone: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Error upserting to Pinecone: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


        

