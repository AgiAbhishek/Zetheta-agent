import os
import logging
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader, CSVLoader

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Document processing settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def get_loader_for_file(file_path):
    """
    Get the appropriate document loader based on file extension.
    
    Args:
        file_path (str): Path to the document file
        
    Returns:
        loader: A LangChain document loader instance
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.pdf':
            return PyPDFLoader(file_path)
        elif file_extension == '.docx' or file_extension == '.doc':
            return Docx2txtLoader(file_path)
        elif file_extension == '.csv':
            return CSVLoader(file_path)
        else:  # Default to text loader for .txt and other text files
            return TextLoader(file_path, encoding='utf-8')
    except Exception as e:
        logger.error(f"Error creating loader for {file_path}: {str(e)}")
        raise

def load_and_split_documents(file_paths):
    """
    Load documents from various file formats and split them into chunks.
    
    Args:
        file_paths (list): List of paths to document files
        
    Returns:
        list: List of document chunks
    """
    try:
        documents = []
        
        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len
        )
        
        # Process each file
        for file_path in file_paths:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
                
            # Get appropriate loader
            loader = get_loader_for_file(file_path)
            
            # Load documents
            file_docs = loader.load()
            
            # Add file path as metadata
            for doc in file_docs:
                doc.metadata['source'] = os.path.basename(file_path)
            
            # Split documents
            split_docs = text_splitter.split_documents(file_docs)
            documents.extend(split_docs)
            
        return documents
    
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        raise

def preprocess_query(query):
    """
    Preprocess the user query for better retrieval results.
    
    Args:
        query (str): The user's question or message
        
    Returns:
        str: Preprocessed query
    """
    try:
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Remove special characters that might interfere with embedding
        query = re.sub(r'[^\w\s?.,]', '', query)
        
        # Ensure the query isn't too long for embedding model
        if len(query) > 512:
            query = query[:512]
            
        return query
    
    except Exception as e:
        logger.error(f"Error preprocessing query: {str(e)}")
        return query  # Return original query if preprocessing fails
