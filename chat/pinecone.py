from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
from django.conf import settings
import logging
import random
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
llm = genai.GenerativeModel('gemini-1.5-pro-latest')



# Configuration
INDEX_NAME = "rag-chatbot"
EMBEDDING_DIMENSION = 1024
EMBEDDING_MODEL = "multilingual-e5-large"

def chunk_text(text, chunk_size=500, overlap=100):
    """
    Split text into overlapping chunks for processing.
    
    Args:
        text (str): Text to be chunked
        chunk_size (int): Size of each chunk in words
        overlap (int): Number of words to overlap between chunks
        
    Returns:
        list: List of text chunks
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks


class PineconeClient:
    def __init__(self):
        """Initialize Pinecone client and ensure index exists."""
        try:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self._ensure_index_exists()
            self.index = self.pc.Index(INDEX_NAME)
        except Exception as e:
            raise

    def _ensure_index_exists(self):
        """Check if index exists and create it if it doesn't."""
        try:
            # List existing indexes
            indexes = self.pc.list_indexes()
            
            # Create index if it doesn't exist
            if INDEX_NAME not in [index['name'] for index in indexes.get('indexes', [])]:
                self.pc.create_index(
                    name=INDEX_NAME,
                    dimension=EMBEDDING_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
        except Exception as e:
            
            raise

    def embeddings(self, data):
        """
        Generate embeddings for input data.
        
        Args:
            data (str or list): Text to embed
            
        Returns:
            list: Embedding vectors
        """
        try:
            embeddings = self.pc.inference.embed(
                model=EMBEDDING_MODEL,
                inputs=data,
                parameters={"input_type": "passage", "truncate": "END"}
            )
            return embeddings
        except Exception as e:
            raise

    def query(self, embedding, namespace="", top_k=3):
        """
        Query the index with an embedding.
        
        Args:
            embedding: Vector embedding to query with
            namespace (str): Namespace to query in
            top_k (int): Number of results to return
            
        Returns:
            dict: Query results
        """
        try:
            # Query the index with the embedding
            results = self.index.query(
                namespace=namespace,
                vector=embedding[0].values,
                top_k=top_k,
                include_values=False,
                include_metadata=True
            )
            return results
        except Exception as e:
            return {"matches": []}

    def upsert(self, data, embedding_obj, namespace="", chunk_text=None):
        """
        Upsert vectors to the index.
        
        Args:
            data (dict): Document data with at least id and metadata
            embedding_obj: Vector embeddings to store
            namespace (str): Namespace to store in
            chunk_text (str, optional): The actual text of the chunk to be stored
        """
        try:
            vector_id = data.get('id', str(uuid.uuid4()))
            metadata = data.get("metadata", {})
            if chunk_text:
                metadata["text_content"] = chunk_text
            
            if "chunk" in data and data["chunk"]:
                metadata["text_content"] = data["chunk"]
            
            for field in ["title", "description", "source", "source_name", "page_title", "page_url"]:
                if field in data and field not in metadata:
                    metadata[field] = data[field]
            
            embedding_values = None
            
            if hasattr(embedding_obj, '__class__') and embedding_obj.__class__.__name__ == 'EmbeddingsList':
                if len(embedding_obj) > 0:
                    embedding_values = embedding_obj[0].values
            # Handle dictionary with 'values' key
            elif hasattr(embedding_obj, 'get') and embedding_obj.get('values'):
                embedding_values = embedding_obj.get('values')
            # Handle object with values attribute
            elif hasattr(embedding_obj, 'values'):
                embedding_values = embedding_obj.values
            # Handle list of embeddings objects
            elif isinstance(embedding_obj, list) and len(embedding_obj) > 0:
                if hasattr(embedding_obj[0], 'values'):
                    embedding_values = embedding_obj[0].values
            
            vector_data = {
                "id": vector_id,
                "values": embedding_values,  
                "metadata": metadata
            }
            
          
            self.index.upsert(vectors=[vector_data], namespace=namespace)
            return True
        except Exception as e:
            
            return False

    def batch_upsert_chunks(self, chunks, data_source_id, user_id, source_type, source_name, namespace=""):
        """
        Upsert a batch of text chunks with proper metadata.
        
        Args:
            chunks (list): List of text chunks to embed and store
            data_source_id (str): ID of the data source
            user_id (str): ID of the user
            source_type (str): Type of source (url, pdf, etc.)
            source_name (str): Name of the source
            namespace (str): Namespace to store in
            
        Returns:
            bool: Success or failure
        """
        try:
            successful_upserts = 0
            
            # First, generate all embeddings at once for efficiency
            all_embeddings = self.embeddings(chunks)
            
            # Check if we got valid embeddings
            if not all_embeddings or len(all_embeddings) != len(chunks):
                
                return False
            
            # Process chunks with their corresponding embeddings
            for chunk_idx, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
                # Generate a unique ID for this chunk
                chunk_id = f"{data_source_id}_{chunk_idx}_{uuid.uuid4().hex[:8]}"
                
                # Prepare metadata
                chunk_data = {
                    "id": chunk_id,
                    "metadata": {
                        "data_source_id": str(data_source_id),
                        "user_id": str(user_id),
                        "source_type": source_type,
                        "source_name": source_name,
                        "chunk_index": chunk_idx,
                        "total_chunks": len(chunks),
                        "chunk_id": chunk_id,
                        "text_content": chunk  # Store the actual text content
                    }
                }
                
                # Upsert the chunk
                if self.upsert(chunk_data, embedding, namespace=namespace):
                    successful_upserts += 1
                
            return successful_upserts > 0
        except Exception as e:
            
            return False

def generate_response(contexts, query):
    """
    Generate a response to a user query based on retrieved contexts.
    
    Args:
        contexts (list): List of text chunks retrieved from the knowledge base
        query (str): User's question
        
    Returns:
        str: Generated response
    """
    # Format contexts for better readability
    formatted_contexts = ""
    for i, context in enumerate(contexts, 1):
        # Extract text content from context object or dictionary
        text = ""
        if isinstance(context, dict) and 'metadata' in context:
            if 'text_content' in context['metadata']:
                text = context['metadata']['text_content']
            elif 'text' in context['metadata']:
                text = context['metadata']['text']
        elif hasattr(context, 'metadata') and hasattr(context.metadata, 'get'):
            text = context.metadata.get('text_content', context.metadata.get('text', ''))
        elif isinstance(context, str):
            text = context
            
        # Include source information if available
        source_info = ""
        if isinstance(context, dict) and 'metadata' in context:
            if 'source' in context['metadata']:
                source_info = f" (Source: {context['metadata']['source']})"
            elif 'source_name' in context['metadata']:
                source_info = f" (Source: {context['metadata']['source_name']})"
            
        formatted_contexts += f"CONTEXT {i}{source_info}:\n{text}\n\n"

    prompt = f"""
    You are an expert conversationalist and knowledge specialist. Answer the user's question in a completely natural, human way.
    
    I've provided some information below that you should use to answer the question, but your response should sound like a knowledgeable person speaking naturally - not like you're referencing any provided information.
    
    INFORMATION:
    {formatted_contexts}
    
    CRITICAL INSTRUCTIONS:
    1. NEVER mention "context", "provided information", "text", "document", or use phrases like "based on the information" or "according to the text".
    2. Answer directly and conversationally as if you inherently know this information.
    3. Don't start with "The answer is..." or "To answer your question..."
    4. Speak naturally like a human expert would in conversation.
    5. If you don't have enough information, respond naturally about what you do know and acknowledge any limitations without referring to "provided contexts".
    6. Maintain a warm, helpful tone while being accurate and precise with facts, dates, and numbers.
    7. If there are different perspectives, present them as a thoughtful human would, weighing options rather than just listing what different "sources" say.
    8. For complex answers, use natural paragraph breaks as a human would.
    9. NEVER EVER say "I don't have information beyond what was provided" or similar phrases.
    10. If you're uncertain, say something like "I'm not entirely sure about that specific detail" instead of referring to limitations in the provided information.
    
    USER QUESTION: {query}
    
    YOUR NATURAL HUMAN RESPONSE:
    """
    
    # Generate response using the LLM
    try:
        response = llm.generate_content(prompt)
        
        # Post-process to remove any remaining references to "contexts" or "provided information"
        text_response = response.text.strip()
        text_response = text_response.replace("Based on the information provided, ", "")
        text_response = text_response.replace("According to the provided context, ", "")
        text_response = text_response.replace("Based on the context, ", "")
        text_response = text_response.replace("From the information provided, ", "")
        text_response = text_response.replace("The context indicates that ", "")
        text_response = text_response.replace("The provided information shows that ", "")
        text_response = text_response.replace("According to the context, ", "")
        
        return text_response
    except Exception as e:
        return "I'm not entirely sure about that. Could you try asking in a different way?"


