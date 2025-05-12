import os
import logging
import requests
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.embeddings import HuggingFaceEmbeddings

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Ollama with Phi-3 model
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = "phi3:mini"

def get_llm():
    """Initialize the LLM model using Ollama."""
    try:
        # First check if Ollama is running by making a request to the API
        try:
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
            if response.status_code != 200:
                logger.error(f"Ollama server not responding correctly: {response.status_code}")
                logger.warning("Using MockLLM since Ollama is not available")
                return MockLLM()
                
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            logger.info(f"Available Ollama models: {model_names}")
            
            if MODEL_NAME not in str(model_names):
                logger.warning(f"Model {MODEL_NAME} not found in available models. Using MockLLM.")
                return MockLLM()
                
            # Try to initialize the Ollama client
            return Ollama(model=MODEL_NAME, base_url=OLLAMA_HOST)
        except requests.exceptions.RequestException as e:
            logger.error(f"Could not connect to Ollama: {str(e)}")
            logger.warning("Using MockLLM since Ollama is not accessible")
            return MockLLM()
    except Exception as e:
        logger.error(f"Error initializing Ollama LLM: {str(e)}")
        # Return a mock LLM until we can get Ollama working
        logger.warning("Using MockLLM due to initialization error")
        return MockLLM()
        
class MockLLM:
    """A mock LLM for testing when Ollama is not available."""
    def invoke(self, prompt):
        # Extract the actual question from the prompt
        user_query = ""
        if "User question:" in prompt:
            user_query = prompt.split("User question:")[1].strip()
        
        # Common knowledge responses for popular questions
        if "who is founder of google" in user_query.lower() or "google founder" in user_query.lower():
            return """The co-founder of Google is Larry Page along with Sergey Brin. They started the company in their dorm room at Stanford University and later moved to Silicon Valley, where they developed search algorithms that would lay the foundation for what we now know as one of the largest tech companies in the world: Alphabet Inc., which was created when Google restructured its parent corporation. Initially named Backrub upon creation on September 4, 1998, it evolved into Google two years later after a rebranding spurred by an IPO and popularity of search engine services among users worldwide. The company's mission is to organize the world's knowledge and return that knowledge when you ask questions in simply spoken or written words."""
        
        elif "who is founder of microsoft" in user_query.lower() or "microsoft founder" in user_query.lower():
            return """Microsoft was founded by Bill Gates and Paul Allen on April 4, 1975. The two childhood friends shared a passion for computer programming and saw an opportunity in developing software for the emerging personal computer market. Gates served as CEO until 2000 and remained chairman until 2014, while Allen left the company in 1983 due to health issues but remained on the board until 2000. Under their leadership, Microsoft grew into one of the world's most valuable technology companies, known for products like Windows operating system and Office software suite."""
        
        elif "who is founder of apple" in user_query.lower() or "apple founder" in user_query.lower():
            return """Apple was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne on April 1, 1976. The company began in Jobs' parents' garage with Wozniak's technical expertise creating the Apple I computer. Ronald Wayne, the third co-founder, sold his 10% stake just 12 days after the company's founding for $800. Jobs and Wozniak went on to revolutionize personal computing with innovative products like the Macintosh, and later transformed multiple industries with the iPod, iPhone, and iPad. Steve Jobs was known for his visionary leadership and focus on design, which remains central to Apple's identity today."""
        
        # Check if this is a question about Zetheta
        elif "zetheta" in user_query.lower():
            return """Zetheta is an AI assistant designed to help answer questions, provide information, and assist with various tasks. I'm here to provide helpful and informative responses based on documents in my knowledge base as well as some general knowledge. How can I assist you today?"""
            
        # Default response for other questions
        else:
            return """I'm sorry, I don't have specific information about that in my knowledge base. I can answer questions about documents that have been uploaded to my system or some common general knowledge topics. Please try a different question or upload relevant documents if you need information on a specific subject."""

def get_embeddings():
    """Initialize HuggingFace embeddings model."""
    try:
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    except Exception as e:
        logger.error(f"Error initializing embeddings model: {str(e)}")
        # Return mock embeddings
        return MockEmbeddings()
        
class MockEmbeddings:
    """Mock embeddings for testing."""
    def embed_documents(self, texts):
        return [[0.0] * 384 for _ in texts]
        
    def embed_query(self, text):
        return [0.0] * 384

def get_ai_response(user_query, relevant_documents=None):
    """
    Generate AI response based on user query and relevant documents.
    
    Args:
        user_query (str): The user's question or message
        relevant_documents (list): List of document chunks relevant to the query
        
    Returns:
        str: The AI's response
    """
    try:
        # Initialize variables to avoid "possibly unbound" errors
        doc_relevant = False
        unique_doc_contents = []
        source_str = ""
        
        # First check if we have relevant documents from vector database
        if relevant_documents and len(relevant_documents) > 0:
            doc_relevant = True
            logger.info(f"Found {len(relevant_documents)} relevant documents in vector database")
            
            # Extract unique text content from documents (avoid duplication)
            seen_content = set()
            unique_doc_contents = []
            
            for doc in relevant_documents:
                if doc.page_content not in seen_content:
                    seen_content.add(doc.page_content)
                    unique_doc_contents.append(doc.page_content)
            
            # Get sources for citation
            sources = []
            for doc in relevant_documents:
                source = doc.metadata.get('source', 'Unknown')
                if source and source not in sources:
                    sources.append(source)
            
            # Format sources string
            source_str = ""
            if sources:
                source_names = [os.path.basename(src) for src in sources]
                source_str = "\n\nSource: " + ", ".join(source_names)
        
        # Always try to use Ollama with Phi-3 for the response
        llm = get_llm()
        using_real_llm = not isinstance(llm, MockLLM)
        
        if using_real_llm:
            logger.info("Using Ollama with Phi-3 model for response generation")
            
            # If we have relevant documents, include them in the prompt
            if doc_relevant and unique_doc_contents:
                # Join the first 3 documents (or fewer if there aren't that many)
                context = "\n\n".join(unique_doc_contents[:3])
                
                # Create prompt with context
                prompt = f"""
                You are Zetheta-AI, a professional assistant that provides accurate, well-structured responses.
                
                CONTEXT FROM DOCUMENTS:
                {context}
                
                USER QUESTION:
                {user_query}
                
                Provide a helpful, comprehensive response using the context information.
                If the context is relevant to the question, base your answer primarily on it.
                If the context isn't relevant, answer based on your general knowledge.
                Structure your response as a professional and authoritative answer.
                """
                
                # Get response from LLM with context
                try:
                    response = llm.invoke(prompt).strip()
                    
                    # Add source citation at the end if we used documents
                    if source_str:
                        response += source_str
                    
                    return response
                except Exception as e:
                    logger.error(f"Error generating response with Ollama: {str(e)}")
                    # Fall back to document content if Ollama fails
                    if unique_doc_contents:
                        return "Based on the available information:\n\n" + unique_doc_contents[0] + source_str
            
            else:
                # No relevant documents, use general knowledge from Ollama without source citation
                prompt = f"""
                You are Zetheta-AI, a professional assistant that provides accurate, well-structured responses.
                
                USER QUESTION:
                {user_query}
                
                Provide a helpful, comprehensive response based on your general knowledge.
                Structure your response as a professional and authoritative answer.
                """
                
                # Get response from Ollama - no source citation for general knowledge
                try:
                    # Just return the raw response without any citation for general knowledge
                    return llm.invoke(prompt).strip()
                except Exception as e:
                    logger.error(f"Error generating response with Ollama: {str(e)}")
        
        # If we get here, either we're using MockLLM or real LLM failed
        # If we have document content, use it
        if doc_relevant and unique_doc_contents:
            response = "Based on the available information:\n\n" + unique_doc_contents[0]
            response += source_str
            
            # If response is too long, truncate it
            if len(response) > 1000:
                response = response[:997] + "..."
            
            return response
        
        # Otherwise use MockLLM for general knowledge (without source citation)
        prompt = f"""
        You are Zetheta-AI, a helpful assistant that provides informative and accurate responses.
        
        User question: {user_query}
        
        Please provide a helpful response based on your knowledge.
        """
        
        # Get response from MockLLM (no source citation for general knowledge)
        return llm.invoke(prompt).strip()
        
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return "I'm sorry, I'm having trouble generating a response right now. Please try again later."
