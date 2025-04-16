from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import DataSource
from chat.pinecone import chunk_text, PineconeClient
from django.db import transaction
import uuid
from .utils import extract_pdf_text, extract_docx_text, extract_txt_text, extract_text_from_url
import logging
import json
import os
from django.utils.text import slugify
import tempfile

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

                    for page in page_data_list:
                        data_source = DataSource(
                            user=request.user,
                            url=page['url'],
                            text_title=page['title'],
                            text_content=page['text'],
                        )
                        data_source.save()

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
            logger.error(f"Error processing data source: {str(e)}")
            return JsonResponse({'error': f'Error processing data source: {str(e)}'}, status=500)

        # Save to database
        try:
            data_source = DataSource(
                user=request.user,
                url=url if url else None,
                file=file if file else None,
                text_title=text_title if text_title else source_name,
                text_content=extracted_text,
            )
            data_source.save()
        except Exception as e:
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
                    
                    # Use batch upserting for better efficiency
                    pc.batch_upsert_chunks(
                        chunks=page_chunks,
                        data_source_id=data_source.id,
                        user_id=request.user.id,
                        source_type=source_type,
                        source_name=source_name,
                        namespace=f"{request.user.username}"
                    )
                
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
                
                # Use the new batch upserting method
                pc.batch_upsert_chunks(
                    chunks=chunks,
                    data_source_id=data_source.id,
                    user_id=request.user.id,
                    source_type=source_type,
                    source_name=source_name,
                    namespace=f"{request.user.username}"
                )
                
                logger.info(f"Successfully processed {len(chunks)} chunks for data source ID: {data_source.id}")
                return JsonResponse({
                    'message': 'Data source added successfully',
                    'data_source_id': str(data_source.id),
                    'chunk_count': len(chunks)
                }, status=200)
                
        except Exception as e:
            logger.error(f"Error upserting to Pinecone: {str(e)}")
            return JsonResponse({'error': f'Error upserting to Pinecone: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def view_data_source_detail(request, data_source_id):
    """
    View details of a specific data source
    """
    # Get the data source or return 404 if not found
    data_source = get_object_or_404(DataSource, id=data_source_id, user=request.user)
    
    # Calculate content statistics
    word_count = len(data_source.text_content.split()) if data_source.text_content else 0
    character_count = len(data_source.text_content) if data_source.text_content else 0
    line_count = data_source.text_content.count('\n') + 1 if data_source.text_content else 0
    
    # Determine source type
    is_url = bool(data_source.url)
    is_file = bool(data_source.file)
    
    context = {
        'data_source': data_source,
        'word_count': word_count,
        'character_count': character_count,
        'line_count': line_count,
        'is_url': is_url,
        'is_file': is_file,
        'created_at': data_source.created_at,
    }
    
    return render(request, 'kb/view_data_source.html', context)


@login_required
def download_data_source(request, data_source_id):
    """
    Download the text content of a data source as a file
    """
    # Get the data source or return 404 if not found
    data_source = get_object_or_404(DataSource, id=data_source_id, user=request.user)
    
    # If the data source is a file and it still exists, return the file
    if data_source.file and os.path.exists(data_source.file.path):
        return FileResponse(data_source.file, as_attachment=True, filename=os.path.basename(data_source.file.path))
    
    # Otherwise, create a text file from the content
    if data_source.text_content:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            temp_file.write(data_source.text_content.encode('utf-8'))
            temp_path = temp_file.name
        
        # Create a filename based on the data source title
        filename = f"{slugify(data_source.text_title)}.txt"
        
        # Return the file and then delete it
        response = FileResponse(open(temp_path, 'rb'), as_attachment=True, filename=filename)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Schedule the file for deletion after the response has been sent
        # This doesn't immediately delete the file, allowing it to be sent first
        import atexit
        atexit.register(lambda: os.remove(temp_path) if os.path.exists(temp_path) else None)
        
        return response
    
    # If there's no content, return a 404
    return HttpResponse("No content available for download", status=404)


@login_required
def delete_data_source(request, data_source_id):
    """
    Delete a data source
    """
    if request.method == 'POST':
        # Get the data source or return 404 if not found
        data_source = get_object_or_404(DataSource, id=data_source_id, user=request.user)
        
        try:
            data_source.delete()
            
            messages.success(request, "Data source deleted successfully.")
            return redirect('core:dashboard')
        except Exception as e:
            logger.error(f"Error deleting data source: {str(e)}")
            messages.error(request, f"Error deleting data source: {str(e)}")
            return redirect('core:dashboard')
    
    # If not a POST request, redirect to the detail view
    return redirect('kb:view_data_source', data_source_id=data_source_id)
