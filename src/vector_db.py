import os
import sys
import logging
import pickle
from pathlib import Path

# Add the project root directory to the Python path when run directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FAISS index settings
FAISS_INDEX_PATH = "data/faiss_index"
EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def get_embeddings():
    """Initialize HuggingFace embeddings model."""
    try:
        return HuggingFaceEmbeddings(
            model_name=EMBEDDINGS_MODEL
        )
    except Exception as e:
        logger.error(f"Error initializing embeddings model: {str(e)}")
        raise

def create_faiss_index(documents):
    """
    Create a FAISS index from the provided documents.
    
    Args:
        documents (list): List of document chunks
        
    Returns:
        FAISS: FAISS vector store
    """
    try:
        # Get embeddings
        embeddings = get_embeddings()
        
        # Create FAISS index
        db = FAISS.from_documents(documents, embeddings)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
        
        # Save the index
        db.save_local(FAISS_INDEX_PATH)
        
        logger.info(f"FAISS index created and saved to {FAISS_INDEX_PATH}")
        return db
    
    except Exception as e:
        logger.error(f"Error creating FAISS index: {str(e)}")
        raise

def load_faiss_index():
    """
    Load the FAISS index.
    
    Returns:
        FAISS: FAISS vector store or None if not found
    """
    try:
        # Check if index exists
        if not os.path.exists(FAISS_INDEX_PATH):
            logger.warning(f"FAISS index not found at {FAISS_INDEX_PATH}")
            return None
        
        # Get embeddings
        embeddings = get_embeddings()
        
        # Load index with allow_dangerous_deserialization=True to fix the security error
        db = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        
        logger.info(f"FAISS index loaded from {FAISS_INDEX_PATH}")
        return db
    
    except Exception as e:
        logger.error(f"Error loading FAISS index: {str(e)}")
        return None

def get_relevant_documents(query, top_k=5):
    """
    Retrieve relevant documents based on the query.
    
    Args:
        query (str): The user's question or message
        top_k (int): Number of documents to retrieve
        
    Returns:
        list: List of relevant document chunks
    """
    try:
        # Load FAISS index
        db = load_faiss_index()
        
        if db is None:
            logger.warning("No FAISS index available. Returning empty results.")
            return []
        
        # Query FAISS
        docs = db.similarity_search(query, k=top_k)
        
        logger.info(f"Retrieved {len(docs)} documents for query: {query}")
        return docs
    
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        return []

def add_documents_to_index(documents):
    """
    Add new documents to the existing FAISS index.
    
    Args:
        documents (list): List of document chunks
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load existing index
        db = load_faiss_index()
        
        # Create new index if one doesn't exist
        if db is None:
            logger.info("Creating new FAISS index")
            create_faiss_index(documents)
            return True
        
        # Get embeddings
        embeddings = get_embeddings()
        
        # Add documents to index
        db.add_documents(documents)
        
        # Save updated index
        db.save_local(FAISS_INDEX_PATH)
        
        logger.info(f"Added {len(documents)} documents to FAISS index")
        return True
    
    except Exception as e:
        logger.error(f"Error adding documents to index: {str(e)}")
        return False

if __name__ == "__main__":
    # This script will directly process PDFs and create/update the FAISS index when run
    from src.process_pdfs import load_processed_documents
    
    print("=== FAISS Vector Database Tool ===")
    print("This tool will process documents and create/update the vector index.")
    
    # Create data directories if they don't exist
    Path("data/raw_files").mkdir(parents=True, exist_ok=True)
    Path("data/processed_files").mkdir(parents=True, exist_ok=True)
    
    # Load processed documents
    print("\nLoading processed documents...")
    documents = load_processed_documents()
    
    if not documents:
        print("\n❌ No documents found to process!")
        print("Please add PDF files to the data/raw_files directory")
        print("and run process_pdfs.py first.")
        sys.exit(1)
    
    # Add documents to index
    print(f"\nFound {len(documents)} document chunks. Creating/updating index...")
    
    if add_documents_to_index(documents):
        print("\n✅ Success! Vector database created/updated successfully.")
        print(f"   - Index location: {FAISS_INDEX_PATH}")
        print(f"   - Document chunks: {len(documents)}")
        print("\nYou can now use the AI assistant to ask questions about your documents.")
    else:
        print("\n❌ Error creating/updating vector database.")
        print("Please check the logs for more information.")
        sys.exit(1)
