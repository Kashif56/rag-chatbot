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
    prompt = f"""
    You are a helpful assistant. Answer the question based on the context provided. If you don't know the answer, say "I don't know".
    Contexts: {contexts}
    Query: {query}
    Answer:
    """
    response = llm.generate_content(prompt)
    return response.text


