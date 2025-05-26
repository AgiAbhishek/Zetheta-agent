import os
import logging
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = os.getenv("MODEL_NAME", "llama3-70b-8192")
OPENAI_API_KEY = os.getenv("GROQ_API_KEY")  # from .env file
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.groq.com/openai/v1")


# ----------------------- LLM SETUP -----------------------

def get_llm():
    """Initialize the LLM model using Groq or fallback to MockLLM."""
    try:
        if not OPENAI_API_KEY or not OPENAI_API_BASE:
            logger.warning("Missing Groq API credentials. Using MockLLM.")
            return MockLLM()

        llm = ChatOpenAI(
            model=MODEL_NAME,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE,
            temperature=0.7
        )
        logger.info(f"Using Groq LLM: {MODEL_NAME}")
        return llm

    except Exception as e:
        logger.error(f"Groq LLM connection failed: {e}")
        return MockLLM()


# ----------------------- MOCK LLM -----------------------

class MockLLM:
    """A mock fallback LLM."""
    def invoke(self, prompt):
        print("MockLLM prompt:\n", prompt)
        if "who is founder of google" in prompt.lower():
            return "Google was founded by Larry Page and Sergey Brin."
        elif "who is founder of microsoft" in prompt.lower():
            return "Microsoft was founded by Bill Gates and Paul Allen."
        elif "who is founder of apple" in prompt.lower():
            return "Apple was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne."
        elif "zetheta" in prompt.lower():
            return "Zetheta is an AI assistant built to provide informative answers."
        else:
            return "Sorry, I don't have information on that."


# ----------------------- EMBEDDINGS -----------------------

def get_embeddings():
    """Return embeddings model."""
    try:
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    except Exception as e:
        logger.error(f"Embeddings error: {e}")
        return MockEmbeddings()


class MockEmbeddings:
    """Mock embedding model."""
    def embed_documents(self, texts):
        return [[0.0] * 384 for _ in texts]
    def embed_query(self, text):
        return [0.0] * 384


# ----------------------- AI RESPONSE -----------------------

def get_ai_response(user_query, relevant_documents=None):
    """
    Generate response based on input and optional documents.
    """
    try:
        llm = get_llm()
        using_real_llm = not isinstance(llm, MockLLM)
        logger.info(f"Using real LLM: {using_real_llm}")

        doc_relevant = False
        unique_doc_contents = []
        source_str = ""

        if relevant_documents:
            doc_relevant = True
            logger.info(f"Using {len(relevant_documents)} relevant documents")

            seen_content = set()
            unique_doc_contents = []
            for doc in relevant_documents:
                if doc.page_content not in seen_content:
                    seen_content.add(doc.page_content)
                    unique_doc_contents.append(doc.page_content)

            sources = [doc.metadata.get('source', 'Unknown') for doc in relevant_documents]
            unique_sources = list(set(sources))
            source_str = "\n\nSources:\n" + "\n".join(f"- {s}" for s in unique_sources)

        # Build the prompt
        if using_real_llm:
            if doc_relevant and unique_doc_contents:
                context = "\n\n".join(unique_doc_contents[:3])
                prompt = f"""
You are Zetheta-AI, a helpful professional assistant.

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION:
{user_query}

Please respond accurately using the context. If it's not useful, rely on general knowledge.
"""
            else:
                prompt = f"""
You are Zetheta-AI, a helpful professional assistant.

USER QUESTION:
{user_query}

Please respond accurately based on your general knowledge.
"""

            print("Prompt sent to Groq:\n", prompt)
            response = llm.invoke(prompt).content.strip()

            if source_str:
                response += "\n" + source_str

            return response

        else:
            # Prompt for MockLLM
            prompt = f"""
You are Zetheta-AI, a helpful assistant that provides informative and accurate responses.

User question: {user_query}

Please provide a helpful response based on your knowledge.
"""
            print("Prompt sent to MockLLM:\n", prompt)
            return llm.invoke(prompt).strip()

    except Exception as e:
        logger.error(f"Error during AI response: {str(e)}")
        return "Sorry, something went wrong while generating the response."


# ----------------------- CLI RUNNER -----------------------

if __name__ == "__main__":
    while True:
        query = input("Ask Zetheta: ")
        if query.lower() in ("exit", "quit"):
            break
        answer = get_ai_response(query)
        print("\nZetheta:\n", answer, "\n")
