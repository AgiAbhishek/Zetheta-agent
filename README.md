# Zetheta AI Assistant

![Zetheta Logo](generated-icon.png)

A powerful document-aware AI assistant built with Flask, Ollama (Phi-3), and FAISS vector database for intelligent question answering based on your PDF documents.

## 🌟 Features

- **Document-Aware Responses**: Ask questions about your documents and get intelligent answers
- **Vector Search**: Find relevant information across all your PDFs using semantic search
- **Chat History**: Save and manage conversation sessions
- **Beautiful UI**: Clean, responsive interface with professional styling
- **PDF Processing**: Easy workflow for adding new documents to the knowledge base

## 📋 Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) with Phi-3 model installed (optional, falls back to built-in knowledge)
- 4GB+ RAM recommended for processing large PDFs

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/zetheta-ai-assistant.git
cd zetheta-ai-assistant
```

### 2. Create a Python Virtual Environment

```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Ollama (Optional but Recommended)

For enhanced responses, install [Ollama](https://ollama.ai/) and pull the Phi-3 model:

```bash
# Install Ollama following instructions at https://ollama.ai/

# After installation, pull the Phi-3 model
ollama pull phi3:mini
```

### 5. Create Required Directories

```bash
mkdir -p data/raw_files data/processed_files data/faiss_index
```

## 🔧 Usage

### Starting the Application

```bash
# Start the Flask application
python app.py

# Or use gunicorn for production (recommended)
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

Then open your browser to http://localhost:5000

### Adding Documents to the Knowledge Base

1. **Upload PDFs**: Copy your PDF files to the `data/raw_files` directory

2. **Process PDFs**: Run the processing script to extract text from PDFs
   ```bash
   python process_pdfs.py
   ```

3. **Update Vector Index**: Build or update the vector database
   ```bash
   python update_index.py
   ```

Alternatively, use the helper script to upload PDFs directly:
```bash
python upload_pdf.py path/to/your/document.pdf
```

### Ask Questions About Your Documents

Once your documents are processed and indexed:

1. Open the web interface in your browser
2. Type your question in the chat box
3. Receive responses based on the content of your documents

## 📊 How It Works

1. **Document Processing Pipeline**:
   - PDFs are uploaded to `data/raw_files/`
   - `process_pdfs.py` extracts text and splits into chunks
   - Text chunks are saved to `data/processed_files/`
   - `update_index.py` creates vector embeddings and builds the FAISS index

2. **Query Processing**:
   - User questions are converted to vector embeddings
   - FAISS finds the most relevant document chunks
   - The response is generated using the relevant documents
   - When Ollama is available, responses are enhanced with the Phi-3 model

## 🔍 Troubleshooting

### Common Issues

- **PDFs Not Processing**: Ensure PDFs are readable and not password-protected
- **No Relevant Responses**: Try processing more documents or reformulating your question
- **Ollama Connection Issues**: Check if Ollama is running with `http://localhost:11434/api/tags`
- **Memory Errors**: Process larger PDFs on a machine with more RAM

## 🛠️ Development

### Project Structure

```
.
├── app.py                 # Main Flask application
├── main.py                # Entry point
├── process_pdfs.py        # PDF processing utility
├── update_index.py        # Vector index updater
├── upload_pdf.py          # PDF upload utility
├── run_directly.py        # Helper for running scripts
├── data/                  # Data directory
│   ├── raw_files/         # Original PDFs
│   ├── processed_files/   # Processed text chunks
│   └── faiss_index/       # Vector database
├── src/                   # Source code
│   ├── chatbot.py         # AI response generation
│   ├── data_processing.py # Document processing logic
│   ├── integrate_pdfs.py  # PDF integration
│   ├── process_pdfs.py    # PDF chunking
│   └── vector_db.py       # Vector database operations
├── static/                # Static files
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript
│   └── images/            # Images
└── templates/             # HTML templates
```


## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [LangChain](https://langchain.com/) - Document processing
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- [Ollama](https://ollama.ai/) - Local LLM hosting
- [Phi-3](https://huggingface.co/microsoft/phi-3) - LLM model by Microsoft
