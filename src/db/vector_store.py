"""
Vector store module - Vector-based memory system for the Scout-Edge platform.
"""
import os
import sys
import logging
from typing import Optional

# Import libraries required for Chroma
import chromadb
from chromadb.config import Settings

# Import configuration settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


def init_vector_store():
    """
    Initialize the vector store or open an existing one.
    
    Returns:
        ChromaClient: Initialized ChromaDB client
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(config.VECTORSTORE_PATH, exist_ok=True)
        
        # Initialize Chroma client
        client = chromadb.PersistentClient(
            path=config.VECTORSTORE_PATH,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        logger.info(
            f"Vector store successfully initialized: {config.VECTORSTORE_PATH}"
        )
        
        # Check and create collections if needed
        _check_and_create_collections(client)
        
        return client
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        raise


def _check_and_create_collections(client):
    """
    Check required collections and create them if they don't exist.
    
    Args:
        client (ChromaClient): ChromaDB client
    """
    # Base collections
    collections = [
        "arxiv_papers",
        "github_repos",
        "huggingface_models",
        "news_articles",
        "trends"
    ]
    
    existing_collections = client.list_collections()
    existing_collection_names = [col.name for col in existing_collections]
    
    for collection_name in collections:
        if collection_name not in existing_collection_names:
            client.create_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' created.")


def get_collection(client, collection_name: str):
    """
    Get a collection with the specified collection name.
    
    Args:
        client (ChromaClient): ChromaDB client
        collection_name (str): Collection name
        
    Returns:
        Collection: ChromaDB collection
    """
    return client.get_collection(name=collection_name)


def add_documents(client, collection_name: str, documents: list, 
                 metadatas: list, ids: list):
    """
    Add documents to the collection. Embedding creation is done by ChromaDB.
    
    Args:
        client (ChromaClient): ChromaDB client
        collection_name (str): Collection name
        documents (list): List of document contents
        metadatas (list): List of document metadata
        ids (list): List of document IDs
    """
    collection = get_collection(client, collection_name)
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    logger.info(f"{len(documents)} documents added to '{collection_name}' collection.")


def query_collection(client, collection_name: str, query_text: str, 
                    n_results: int = 5):
    """
    Query the collection and return the most similar documents.
    
    Args:
        client (ChromaClient): ChromaDB client
        collection_name (str): Collection name
        query_text (str): Query text
        n_results (int): Number of results to return
        
    Returns:
        dict: Query results
    """
    collection = get_collection(client, collection_name)
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results
