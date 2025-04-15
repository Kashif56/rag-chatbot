from pinecone import Pinecone, ServerlessSpec
from django.conf import settings
import logging
import random

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
INDEX_NAME = "rag-chatbot"
EMBEDDING_DIMENSION = 1536
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
            logger.error(f"Failed to initialize Pinecone client: {str(e)}")
            raise

    def _ensure_index_exists(self):
        """Check if index exists and create it if it doesn't."""
        try:
            # List existing indexes
            indexes = self.pc.list_indexes()
            
            # Create index if it doesn't exist
            if INDEX_NAME not in [index['name'] for index in indexes.get('indexes', [])]:
                logger.info(f"Creating Pinecone index: {INDEX_NAME}")
                self.pc.create_index(
                    name=INDEX_NAME,
                    dimension=EMBEDDING_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Successfully created index: {INDEX_NAME}")
        except Exception as e:
            logger.error(f"Error checking/creating index: {str(e)}")
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
            logger.error(f"Error generating embeddings: {str(e)}")
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
            logger.error(f"Error querying Pinecone: {str(e)}")
            return {"matches": []}

    def upsert(self, data, embeddings, namespace=""):
        """
        Upsert vectors to the index.
        
        Args:
            data (dict): Document data with at least id and metadata
            embeddings: Vector embeddings to store
            namespace (str): Namespace to store in
        """
        try:
            # Create vector data with all metadata provided
            vector_data = {
                "id": str(random.uuid4()),
                "values": embeddings,
                "metadata": data.get("metadata", {})
            }
            
            # If no metadata provided but fields exist in data, create metadata
            if "metadata" not in data and any(k in data for k in ["title", "description", "source", "chunk"]):
                vector_data["metadata"] = {}
                for field in ["title", "description", "source", "chunk"]:
                    if field in data:
                        vector_data["metadata"][field] = data[field]
            
            self.index.upsert(vectors=[vector_data], namespace=namespace)
            logger.debug(f"Upserted document with ID: {data['id']}")
            return True
        except Exception as e:
            logger.error(f"Error upserting to Pinecone: {str(e)}")
            return False

    def delete(self, ids=None, namespace="", delete_all=False, filter=None):
        """
        Delete vectors from the index.
        
        Args:
            ids (list, optional): IDs to delete
            namespace (str): Namespace to delete from
            delete_all (bool): Whether to delete all vectors in the namespace
            filter (dict, optional): Metadata filter for deletion
        """
        try:
            if delete_all:
                self.index.delete(delete_all=True, namespace=namespace)
                logger.info(f"Deleted all vectors in namespace: {namespace}")
            elif ids:
                self.index.delete(ids=ids, namespace=namespace)
                logger.info(f"Deleted {len(ids)} vectors")
            elif filter:
                self.index.delete(filter=filter, namespace=namespace)
                logger.info(f"Deleted vectors matching filter: {filter}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from Pinecone: {str(e)}")
            return False

    def fetch(self, ids, namespace=""):
        """
        Fetch vectors by ID.
        
        Args:
            ids (list): IDs to fetch
            namespace (str): Namespace to fetch from
            
        Returns:
            dict: Fetched vectors
        """
        try:
            results = self.index.fetch(ids=ids, namespace=namespace)
            return results
        except Exception as e:
            logger.error(f"Error fetching from Pinecone: {str(e)}")
            return {"vectors": {}}