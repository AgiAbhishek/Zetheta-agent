import os
import logging
from flask import Flask, render_template, request, jsonify, session
import sqlite3
from datetime import datetime
import json

from src.chatbot import get_ai_response
from src.vector_db import get_relevant_documents
from src.data_processing import preprocess_query

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-dev")

# Database initialization
def get_db_connection():
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create chat sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Routes
@app.route('/')
def index():
    # Generate a new session ID if one doesn't exist
    if 'session_id' not in session:
        session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        session['session_id'] = session_id
        
        # Save new session to database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_sessions (session_id, title) VALUES (?, ?)",
            (session_id, "New Conversation")
        )
        conn.commit()
        conn.close()
        logger.info(f"Created new session: {session_id}")
        
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        # Get or create session ID
        if 'session_id' not in session:
            # Generate a new session ID
            session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            session['session_id'] = session_id
            
            # Save new session to database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_sessions (session_id, title) VALUES (?, ?)",
                (session_id, "New Conversation")
            )
            conn.commit()
            conn.close()
            logger.info(f"Created new session: {session_id}")
        else:
            session_id = session.get('session_id')
        
        if not user_message:
            return jsonify({"error": "Invalid request"}), 400
        
        # Store user message
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, "user", user_message)
        )
        
        # Check if this is the first message in this session
        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = ?",
            (session_id,)
        )
        message_count = cursor.fetchone()[0]
        
        # If this is the first message, update the session title
        if message_count <= 1:  # We just inserted one, so count should be 1
            # Truncate the message if it's too long (limit to ~25 chars)
            title = user_message[:25] + "..." if len(user_message) > 25 else user_message
            cursor.execute(
                "UPDATE chat_sessions SET title = ? WHERE session_id = ?",
                (title, session_id)
            )
        
        conn.commit()
        
        # Preprocess query and get relevant documents
        processed_query = preprocess_query(user_message)
        logger.info(f"Processed query: {processed_query}")
        
        relevant_docs = get_relevant_documents(processed_query)
        logger.info(f"Retrieved {len(relevant_docs)} relevant documents for query")
        
        # Get AI response
        logger.info(f"Generating AI response with {'context' if relevant_docs else 'NO context'}")
        ai_response = get_ai_response(user_message, relevant_docs)
        
        # Store AI response
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, "assistant", ai_response)
        )
        conn.commit()
        conn.close()
        
        # Get unique source documents to avoid repetition
        unique_sources = set()
        source_list = []
        
        if relevant_docs:
            try:
                for doc in relevant_docs:
                    if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                        source = doc.metadata.get('source', 'Unknown')
                        if source not in unique_sources:
                            unique_sources.add(source)
                            source_list.append(source)
            except Exception as e:
                logger.error(f"Error processing document metadata: {str(e)}")
                source_list = []
        
        logger.info(f"Final source list: {source_list}")
                
        return jsonify({
            "response": ai_response,
            "documents": source_list
        })
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": "An error occurred processing your request"}), 500

@app.route('/api/chat_history', methods=['GET'])
def get_chat_history():
    try:
        session_id = session.get('session_id')
        logger.debug(f"Getting chat history for session_id: {session_id}")
        
        if not session_id:
            logger.warning("No active session found, creating a new one")
            # Generate a new session ID
            session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Save new session to database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_sessions (session_id, title) VALUES (?, ?)",
                (session_id, "New Conversation")
            )
            conn.commit()
            conn.close()
            
            # Update session in Flask session
            session['session_id'] = session_id
            logger.info(f"Created new session: {session_id}")
            
            # Return empty messages for new session
            return jsonify({"messages": []})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get messages for current session
        cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        messages = [{"role": row['role'], "content": row['content'], 
                     "timestamp": row['timestamp']} for row in cursor.fetchall()]
        conn.close()
        
        logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")
        return jsonify({"messages": messages})
    
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        logger.exception("Full exception details:")
        return jsonify({"messages": []}), 200

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all chat sessions
        cursor.execute(
            "SELECT session_id, title, created_at FROM chat_sessions ORDER BY created_at DESC"
        )
        sessions = [{"id": row['session_id'], "title": row['title'], 
                     "created_at": row['created_at']} for row in cursor.fetchall()]
        conn.close()
        
        logger.debug(f"Retrieved {len(sessions)} chat sessions")
        return jsonify({"sessions": sessions})
    
    except Exception as e:
        logger.error(f"Error retrieving sessions: {str(e)}")
        logger.exception("Full exception details:")
        return jsonify({"sessions": []}), 200

@app.route('/api/switch_session', methods=['POST'])
def switch_session():
    try:
        data = request.get_json()
        new_session_id = data.get('session_id')
        
        if not new_session_id:
            return jsonify({"error": "Invalid session ID"}), 400
        
        # Check if session exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT session_id FROM chat_sessions WHERE session_id = ?",
            (new_session_id,)
        )
        
        if cursor.fetchone() is None:
            conn.close()
            return jsonify({"error": "Session not found"}), 404
        
        conn.close()
        
        # Update session in Flask session
        session['session_id'] = new_session_id
        
        return jsonify({"success": True, "session_id": new_session_id})
    
    except Exception as e:
        logger.error(f"Error switching session: {str(e)}")
        return jsonify({"error": "An error occurred switching sessions"}), 500

@app.route('/api/new_session', methods=['POST'])
def new_session():
    try:
        # Generate a new session ID
        new_session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Default title - will be updated with first message
        default_title = "New Conversation"
        
        # Save new session to database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_sessions (session_id, title) VALUES (?, ?)",
            (new_session_id, default_title)
        )
        conn.commit()
        conn.close()
        
        # Update session in Flask session
        session['session_id'] = new_session_id
        
        return jsonify({"success": True, "session_id": new_session_id})
    
    except Exception as e:
        logger.error(f"Error creating new session: {str(e)}")
        return jsonify({"error": "An error occurred creating a new session"}), 500

@app.route('/api/delete_session', methods=['POST'])
def delete_session():
    try:
        data = request.get_json()
        session_id_to_delete = data.get('session_id')
        
        if not session_id_to_delete:
            return jsonify({"error": "Invalid session ID"}), 400
        
        # Delete the session and its messages
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First delete messages associated with the session
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id_to_delete,))
        
        # Then delete the session itself
        cursor.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id_to_delete,))
        
        conn.commit()
        conn.close()
        
        # If the deleted session was the active one, create a new session
        if session.get('session_id') == session_id_to_delete:
            new_session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            session['session_id'] = new_session_id
            
            # Save new session to database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_sessions (session_id, title) VALUES (?, ?)",
                (new_session_id, "New Conversation")
            )
            conn.commit()
            conn.close()
        
        return jsonify({"success": True})
    
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        return jsonify({"error": "An error occurred deleting the session"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
