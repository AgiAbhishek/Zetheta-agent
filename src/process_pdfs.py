import os
import logging
import json
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
RAW_FILES_DIR = Path('data/raw_files')
PROCESSED_FILES_DIR = Path('data/processed_files')

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path (Path): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    logger.info(f"Extracting text from {pdf_path}")
    
    try:
        reader = PdfReader(pdf_path)
        text = ""
        
        # Extract text from each page
        for i, page in enumerate(reader.pages):
            logger.debug(f"Processing page {i+1}/{len(reader.pages)}")
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        
        logger.info(f"Successfully extracted {len(text)} characters from {pdf_path}")
        return text
    
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
        return ""

def split_text_into_chunks(text, filename, chunk_size=1000, chunk_overlap=200):
    """
    Split text into smaller chunks for better processing.
    
    Args:
        text (str): Text to split
        filename (str): Original filename (for metadata)
        chunk_size (int): Size of each chunk
        chunk_overlap (int): Overlap between chunks
        
    Returns:
        list: List of dictionaries with text chunks and metadata
    """
    logger.info(f"Splitting text into chunks (size={chunk_size}, overlap={chunk_overlap})")
    
    try:
        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Split text into chunks
        chunks = text_splitter.split_text(text)
        
        # Create list of dictionaries with text and metadata
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "text": chunk,
                "metadata": {
                    "source": filename,
                    "chunk": i + 1,
                    "total_chunks": len(chunks)
                }
            })
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return result
    
    except Exception as e:
        logger.error(f"Error splitting text: {str(e)}")
        return []

def process_pdf_file(pdf_path):
    """
    Process a single PDF file and save the chunks.
    
    Args:
        pdf_path (Path): Path to the PDF file
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    filename = pdf_path.name
    output_path = PROCESSED_FILES_DIR / f"{filename}.json"
    
    logger.info(f"Processing PDF: {filename}")
    
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        
        if not text:
            logger.warning(f"No text extracted from {filename}")
            return False
        
        # Split text into chunks
        chunks = split_text_into_chunks(text, filename)
        
        if not chunks:
            logger.warning(f"No chunks created for {filename}")
            return False
        
        # Save chunks to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved processed data to {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing {filename}: {str(e)}")
        return False

def load_processed_documents():
    """
    Load all processed documents from the processed_files directory.
    
    Returns:
        list: List of Document objects ready for indexing
    """
    from langchain.schema.document import Document
    
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

def process_all_pdfs(chunk_size=1000, chunk_overlap=200):
    """
    Process all PDF files in the raw_files directory.
    
    Args:
        chunk_size (int): Size of each text chunk
        chunk_overlap (int): Overlap between chunks
        
    Returns:
        tuple: (total, successful) counts
    """
    # Ensure directories exist
    PROCESSED_FILES_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Processing all PDFs in {RAW_FILES_DIR}")
    
    total_count = 0
    success_count = 0
    
    # Get all PDF files
    pdf_files = [f for f in RAW_FILES_DIR.glob("*.pdf")]
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {RAW_FILES_DIR}")
        return 0, 0
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF file
    for pdf_path in pdf_files:
        total_count += 1
        if process_pdf_file(pdf_path):
            success_count += 1
    
    logger.info(f"Processed {success_count}/{total_count} PDF files successfully")
    return total_count, success_count

if __name__ == "__main__":
    logger.info("Starting PDF processing")
    total, successful = process_all_pdfs()
    logger.info(f"PDF processing complete. Processed {successful}/{total} files successfully")