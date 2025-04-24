from pinecone import Pinecone, ServerlessSpec
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader, Docx2txtLoader, UnstructuredURLLoader
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import PlaywrightURLLoader
from langchain_community.document_loaders import SeleniumURLLoader
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
import google.generativeai as genai
from django.conf import settings

import os
import uuid
from dotenv import load_dotenv
import urllib.request
import urllib.error

from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
INDEX_NAME = "rag-chatbot"
EMBEDDING_DIMENSION = 1536  # OpenAI embeddings are 1536 dimensions
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI embedding model
HUGGINGFACE_MODEL = "multilingual-e5-large"  # HuggingFace model as fallback
EMBEDDING_SOURCE = os.getenv('EMBEDDING_SOURCE', 'openai')  # 'openai', 'huggingface', or 'pinecone'
GOOGLE_EMBEDDING_MODEL = "textembedding-gecko@latest"  # Google's embedding model

# Set User Agent for web requests
os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

def initialize_pinecone():
    """
    Initialize the Pinecone index if it doesn't exist.
    """
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(INDEX_NAME)




def get_embeddings_model():
    if EMBEDDING_SOURCE.lower() == 'openai':
        return OpenAIEmbeddings(model=EMBEDDING_MODEL)
    elif EMBEDDING_SOURCE.lower() == 'google':
        return VertexAIEmbeddings(model_name=GOOGLE_EMBEDDING_MODEL)
    else:  
        return HuggingFaceEmbeddings(model_name=HUGGINGFACE_MODEL)



def create_text_splitter():
    embeddings = get_embeddings_model() 

    chunker = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold='percentile'
    )

    return chunker




def load_documents(source, content=None, follow_links=False, max_depth=1, max_internal_links=5):
    LOADER_MAPPING = {
        '.txt': TextLoader,
        '.pdf': PyPDFLoader,
        '.docx': Docx2txtLoader,
        '.doc': Docx2txtLoader, 
        '.md': TextLoader,
        '.json': TextLoader,
    }
    
    # Handle URL
    if source.startswith(('http://', 'https://')):
        return scrape_url(
            source, 
            follow_links=follow_links, 
            max_depth=max_depth, 
            max_internal_links=max_internal_links
        )
    
    # Handle raw text input
    elif source.lower() == 'text' and content:
        timestamp = uuid.uuid4()
        return [Document(
            page_content=content, 
            metadata={"source": "user_input", "timestamp": str(timestamp)}
        )]
    
    # Handle directory
    elif os.path.isdir(source):
        # Create a mapping of file extensions to glob patterns
        glob_patterns = {
            'pdf': '**/*.pdf',
            'txt': '**/*.txt',
            'md': '**/*.md',
            'docx': '**/*.docx',
            'doc': '**/*.doc',
            'json': '**/*.json',
        }
        
        all_documents = []
        
        # Load each document type separately
        for doc_type, glob_pattern in glob_patterns.items():
            try:
                # Skip if no matching loader
                if f'.{doc_type}' not in LOADER_MAPPING:
                    continue
                    
                # Create loader for this document type
                loader = DirectoryLoader(
                    path=source,
                    glob=glob_pattern,
                    loader_cls=LOADER_MAPPING[f'.{doc_type}'],
                    show_progress=True,
                    use_multithreading=True
                )
                
                # Load documents and add to collection
                documents = loader.load()
                all_documents.extend(documents)
                print(f"Loaded {len(documents)} {doc_type} documents from {source}")
            except Exception as e:
                print(f"Error loading {doc_type} documents: {str(e)}")
        
        return all_documents
    
    # Handle single file
    elif os.path.isfile(source):
        ext = os.path.splitext(source)[1].lower()
        
        if ext not in LOADER_MAPPING or LOADER_MAPPING[ext] is None:
            raise ValueError(f"Unsupported file type: {ext}")
        
        loader_class = LOADER_MAPPING[ext]
        loader = loader_class(source)
        documents = loader.load()
        
        return documents
    
    # Handle unsupported source
    else:
        raise ValueError(f"Unsupported source: {source}. Must be a file path, directory, URL, or 'text'.")



def get_documents_text(documents):
    if not documents:
        return ""
    
    # Extract text from each document
    texts = []
    for doc in documents:
        if hasattr(doc, 'page_content') and doc.page_content:
            texts.append(doc.page_content)
            
    # Combine with double newlines as separators
    return "\n\n".join(texts)


def process_documents(documents):
    try:
        text_splitter = create_text_splitter()
        
        chunks = []
        for doc in documents:
            doc_chunks = text_splitter.split_documents([doc])
            chunks.extend(doc_chunks)
        
        return chunks
    except Exception as e:
        fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        return fallback_splitter.split_documents(documents)



def upsert_documents(documents, namespace=None):
    embeddings = get_embeddings_model()
    
    # Generate UUIDs for documents first
    uuids = [str(uuid.uuid4()) for _ in range(len(documents))]
    
    # Create vector store with the generated UUIDs
    vector_store = PineconeVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        index_name=INDEX_NAME,
        namespace=namespace,
        ids=uuids  # Pass the IDs to the from_documents method
    )
    
    # Remove the duplicate add_documents call
    return vector_store, uuids

def create_retriever(namespace=None):
    embeddings = get_embeddings_model()
    

    vector_store = PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=embeddings,
        namespace=namespace
    )
    
    return vector_store.as_retriever(search_kwargs={"k": 5})

def scrape_url(url, follow_links=False, max_depth=1, max_internal_links=20, dynamic_rendering=False):


    all_documents = []
    visited_urls = set()
    url_contents = {}  # Store URL to content mapping
    
    def is_internal_link(base_url, link):
        base_domain = urlparse(base_url).netloc
        link_domain = urlparse(link).netloc
        return base_domain == link_domain or not link_domain  # Empty netloc means relative link
    
    def extract_internal_links(base_url, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        internal_links = []
        
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            # Convert relative URLs to absolute
            absolute_link = urljoin(base_url, link)
            # Only include internal links and not the base URL itself
            if is_internal_link(base_url, absolute_link) and absolute_link != base_url:
                internal_links.append(absolute_link)
                
        links = list(set(internal_links))[:max_internal_links]  # Deduplicate and limit
        print(f"Found {len(links)} internal links on {base_url}")
        return links
    
    def scrape_single_url(url, depth=0):
        if url in visited_urls or depth > max_depth:
            return []
        
        print(f"Scraping URL: {url}")
        visited_urls.add(url)
        documents = []
        content = ""
        
        try:
            # Use basic requests with BeautifulSoup - simplest and most reliable method
            headers = {
                'User-Agent': os.environ.get("USER_AGENT", 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            }
            
            print(f"Fetching {url} with requests and BeautifulSoup")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            
            # Get text content
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up text: remove extra whitespace and empty lines
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            
            if text.strip():
                print(f"Successfully fetched and parsed {url}")
                documents = [Document(page_content=text, metadata={"source": url})]
                content = text
                url_contents[url] = text  # Store the URL content mapping
            else:
                print(f"No text content found in {url}")
        
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
            
        # Follow internal links if requested
        if follow_links and depth < max_depth and content:
            try:
                internal_links = extract_internal_links(url, html_content)
                
                for link in internal_links:
                    if len(visited_urls) >= max_internal_links + 1:  # +1 for the original URL
                        print(f"Reached max internal links limit ({max_internal_links})")
                        break
                    print(f"Following internal link: {link}")
                    link_documents = scrape_single_url(link, depth + 1)
                    documents.extend(link_documents)
            except Exception as e:
                print(f"Error following links from {url}: {str(e)}")
                
        if documents:
            print(f"Successfully scraped {url}, extracted {len(documents)} documents")
        else:
            print(f"Failed to extract any documents from {url}")
            
        return documents
        
    # Start scraping from the initial URL
    result = scrape_single_url(url)
    print(f"Completed scraping of {url}: found {len(result)} total documents")
    return result, url_contents

def generate_llm_response(chatbot, message, context="", conversation_history=None):
    if conversation_history is None:
        conversation_history = []
    
    bot_response = ""
    try:
        # Generate response based on the LLM provider
        if chatbot.llm_provider.lower() == 'openai':

            from openai import OpenAI

            client = OpenAI(api_key=OPENAI_API_KEY)

            system_message = f"""You are {chatbot.name}, an AI assistant that helps users with their questions using the provided context. Don't mention the context in your response. Do not respond with phrases like 'As per provided context' or similar.
            {chatbot.prompt}
            
            Use the following context to answer the user's question:
            {context}
            
            Remember previous conversation while answering if relevant.
            """
            
            messages = [{"role": "system", "content": system_message}]
            
          
            messages.extend(conversation_history)
            
            # Add the current message if not already in conversation history
            if not any(msg.get("content") == message and msg.get("role") == "user" for msg in conversation_history):
                messages.append({"role": "user", "content": message})
            
          
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model=chatbot.llm_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            bot_response = response.choices[0].message.content
            
        elif chatbot.llm_provider.lower() == 'google':
            from django.conf import settings
            
            # Configure Google Generative AI
            api_key = settings.GOOGLE_API_KEY or GOOGLE_API_KEY
            genai.configure(api_key=api_key)
            
            # Create model and generate response
            model = genai.GenerativeModel(chatbot.llm_model)
            
            # Prepare conversation history for Google's format
            chat_history = []
            for msg in conversation_history:
                if msg['role'] == 'user':
                    chat_history.append({"role": "user", "parts": [msg['content']]})
                else:
                    chat_history.append({"role": "model", "parts": [msg['content']]})
            
            # Create prompt with context
            system_prompt = f"""You are {chatbot.name}, an AI assistant that helps users with their questions.
            {chatbot.prompt}
            
            Use the following context to answer the user's question:
            {context}
            
            Remember previous conversation while answering if relevant.
            """

          
            # Generate response
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(system_prompt + "\n\nUser question: " + message)
            
            bot_response = response.text
            
        else:
            # Default response if no valid LLM provider is configured
            bot_response = "I'm sorry, I couldn't generate a response at this time."
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error generating LLM response: {str(e)}")
        bot_response = "I encountered an error while generating a response. Please try again later."
    
    return bot_response


def create_rag_chain(chatbot, namespace=None):
    if namespace is None:
        namespace = chatbot.name
    
    print(f"Creating RAG chain for namespace: {namespace}")
    
    try:
        # Create retriever using the existing function
        retriever = create_retriever(namespace=namespace)
        
        def generate_response(message, conversation_history=None):
            if conversation_history is None:
                conversation_history = []
                
            print(f"RAG processing message with {len(conversation_history)} history items")
                
            try:
                # Get relevant documents based on the query
                docs = retriever.invoke(message)
                
                print(f"Retrieved {len(docs)} documents from vector store")
                
                # Combine document content into context
                context = "\n\n".join([doc.page_content for doc in docs])
                
                # Generate response with context and conversation history
                return generate_llm_response(
                    chatbot=chatbot,
                    message=message,
                    context=context,
                    conversation_history=conversation_history
                )
            except Exception as e:
                print(f"Error in RAG chain: {str(e)}")
                
                # Fallback to generate response without context
                return generate_llm_response(
                    chatbot=chatbot,
                    message=message,
                    conversation_history=conversation_history
                )
        
        return generate_response
    
    except Exception as e:
        print(f"Error creating RAG chain: {str(e)}")
        
        
        
        def fallback_response(message, conversation_history=None):
            return generate_llm_response(
                chatbot=chatbot,
                message=message,
                conversation_history=conversation_history
            )
        
        return fallback_response


