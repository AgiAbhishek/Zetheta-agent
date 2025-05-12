"""
Integrate processed PDF data into the vector database

This module loads processed PDF files and adds them to the vector database for retrieval.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain.schema.document import Document

# Use absolute import to avoid relative import errors
from src.vector_db import add_documents_to_index, create_faiss_index, load_faiss_index

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
PROCESSED_FILES_DIR = Path('data/processed_files')

def load_processed_documents():
    """
    Load all processed documents from the processed_files directory.
    
    Returns:
        list: List of Document objects ready for indexing
    """
    documents = []
    
    if not PROCESSED_FILES_DIR.exists():
        logger.warning(f"Processed files directory not found: {PROCESSED_FILES_DIR}")
        return documents
    
    # Get all JSON files in the processed files directory
    json_files = list(PROCESSED_FILES_DIR.glob("*.pdf.json"))
    
    if not json_files:
        logger.warning(f"No processed PDF files found in {PROCESSED_FILES_DIR}")
        return documents
    
    logger.info(f"Found {len(json_files)} processed PDF files")
    
    # Load each JSON file and convert to Document objects
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            logger.info(f"Loading {len(chunks)} chunks from {json_file}")
            
            for chunk in chunks:
                text = chunk.get('text', '')
                metadata = chunk.get('metadata', {})
                
                if text:
                    documents.append(Document(page_content=text, metadata=metadata))
        
        except Exception as e:
            logger.error(f"Error loading {json_file}: {str(e)}")
    
    logger.info(f"Loaded {len(documents)} document chunks in total")
    return documents

def integrate_documents():
    """
    Integrate processed documents into the vector database.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load processed documents
        documents = load_processed_documents()
        
        if not documents:
            logger.warning("No documents to integrate")
            return False
        
        # Try to load existing index
        vector_db = load_faiss_index()
        
        if vector_db:
            # Add to existing index
            logger.info("Adding documents to existing vector database")
            success = add_documents_to_index(documents)
            
            if success:
                logger.info(f"Successfully added {len(documents)} documents to existing index")
            else:
                logger.error("Failed to add documents to existing index")
                return False
        else:
            # Create new index
            logger.info("Creating new vector database")
            vector_db = create_faiss_index(documents)
            
            if vector_db:
                logger.info(f"Successfully created new index with {len(documents)} documents")
            else:
                logger.error("Failed to create vector database")
                return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error integrating documents: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting integration of processed PDF files into vector database")
    
    if integrate_documents():
        logger.info("Successfully integrated documents into vector database")
    else:
        logger.error("Failed to integrate documents into vector database")