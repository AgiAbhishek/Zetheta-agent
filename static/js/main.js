document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    feather.replace();
    
    // DOM Elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatContainer = document.getElementById('chat-container');
    const newChatBtn = document.getElementById('new-chat-btn');
    const chatSessions = document.getElementById('chat-sessions');
    const sourceDocuments = document.getElementById('source-documents');
    const documentList = document.getElementById('document-list');
    const currentChatTitle = document.getElementById('current-chat-title');
    
    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        // Reset to default height if empty
        if (this.value === '') {
            this.style.height = 'auto';
        }
    });
    
    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        
        if (message === '') return;
        
        // Add user message to chat
        addMessage('user', message);
        
        // Clear input and reset
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Add loading indicator
        const loadingMessage = addLoadingMessage();
        
        // Send message to API
        sendMessage(message)
            .then(response => {
                // Remove loading indicator
                if (loadingMessage && loadingMessage.parentNode) {
                    chatContainer.removeChild(loadingMessage);
                }
                
                // Add assistant response
                addMessage('assistant', response.response);
                
                // Always hide source documents as requested
                sourceDocuments.classList.add('d-none');
                
                // Refresh chat sessions list
                loadChatSessions();
                
                // Make sure textarea is still available and focusable
                setTimeout(() => {
                    userInput.focus();
                }, 100);
            })
            .catch(error => {
                // Remove loading indicator
                if (loadingMessage && loadingMessage.parentNode) {
                    chatContainer.removeChild(loadingMessage);
                }
                
                // Add error message
                addMessage('assistant', 'I apologize, but I encountered an error processing your request. Please try again.');
                console.error('Error:', error);
                
                // Make sure textarea is still available
                setTimeout(() => {
                    userInput.focus();
                }, 100);
            });
    });
    
    // New chat button
    newChatBtn.addEventListener('click', function() {
        createNewChat();
    });
    
    // Function to send message to API
    async function sendMessage(message) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message }),
                credentials: 'same-origin' // Ensure cookies are sent for session management
            });
            
            if (!response.ok) {
                console.error(`HTTP error! status: ${response.status}`);
                const errorText = await response.text();
                console.error(`Error details: ${errorText}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error in sendMessage:', error);
            throw error;
        }
    }
    
    // Function to add message to chat
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = role === 'user' ? 'user-message' : 'assistant-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Process message content (handle markdown-like syntax)
        let formattedContent = content;
        
        // Convert code blocks
        formattedContent = formattedContent.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Convert line breaks to <br>
        formattedContent = formattedContent.replace(/\n/g, '<br>');
        
        messageContent.innerHTML = formattedContent;
        
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(timestamp);
        
        chatContainer.appendChild(messageDiv);
        
        // Clear float and scroll to bottom
        const clearFloat = document.createElement('div');
        clearFloat.style.clear = 'both';
        chatContainer.appendChild(clearFloat);
        
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Function to add loading message
    function addLoadingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'assistant-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const loadingDots = document.createElement('div');
        loadingDots.className = 'loading-dots';
        loadingDots.innerHTML = '<span></span><span></span><span></span>';
        
        messageContent.appendChild(loadingDots);
        messageDiv.appendChild(messageContent);
        
        chatContainer.appendChild(messageDiv);
        
        // Clear float and scroll to bottom
        const clearFloat = document.createElement('div');
        clearFloat.style.clear = 'both';
        chatContainer.appendChild(clearFloat);
        
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return messageDiv;
    }
    
    // Function to display source documents
    function displaySourceDocuments(documents) {
        // Always hide source documents as requested
        sourceDocuments.classList.add('d-none');
    }
    
    // Function to create delete button for chat session
    function createDeleteButton(sessionId) {
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-link text-danger chat-delete-btn';
        deleteBtn.innerHTML = '<i data-feather="trash-2"></i>';
        deleteBtn.title = 'Delete this chat';
        
        deleteBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Don't trigger session click
            deleteSession(sessionId);
        });
        
        return deleteBtn;
    }
    
    // Function to delete a chat session
    async function deleteSession(sessionId) {
        if (!confirm('Are you sure you want to delete this chat? This cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/delete_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // If we're deleting the current session, create a new one
            if (document.querySelector(`.chat-session[data-id="${sessionId}"]`).classList.contains('active')) {
                createNewChat();
            } else {
                // Otherwise just refresh the session list
                loadChatSessions();
            }
            
        } catch (error) {
            console.error('Error deleting chat session:', error);
            alert('Failed to delete chat session. Please try again.');
        }
    }
    
    // Load chat sessions with delete buttons
    async function loadChatSessions() {
        try {
            const response = await fetch('/api/sessions');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Clear previous sessions
            chatSessions.innerHTML = '';
            
            // Get current session ID
            const currentSessionId = document.querySelector('.chat-session.active')?.dataset.id;
            
            // Add each session
            data.sessions.forEach(session => {
                const sessionWrapper = document.createElement('div');
                sessionWrapper.className = 'chat-session-wrapper d-flex align-items-center justify-content-between';
                
                const sessionElement = document.createElement('div');
                sessionElement.className = 'chat-session flex-grow-1';
                if (currentSessionId === session.id) {
                    sessionElement.classList.add('active');
                }
                sessionElement.dataset.id = session.id;
                sessionElement.textContent = session.title;
                
                sessionElement.addEventListener('click', function() {
                    switchSession(session.id);
                });
                
                const deleteBtn = createDeleteButton(session.id);
                
                sessionWrapper.appendChild(sessionElement);
                sessionWrapper.appendChild(deleteBtn);
                chatSessions.appendChild(sessionWrapper);
            });
            
            // Re-initialize feather icons for the delete buttons
            feather.replace();
            
        } catch (error) {
            console.error('Error loading chat sessions:', error);
        }
    }
    
    // Switch to a different chat session
    async function switchSession(sessionId) {
        try {
            const response = await fetch('/api/switch_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Clear current chat
            chatContainer.innerHTML = '';
            
            // Hide source documents
            sourceDocuments.classList.add('d-none');
            
            // Load chat history
            loadChatHistory();
            
            // Update active session styling
            document.querySelectorAll('.chat-session').forEach(el => {
                el.classList.remove('active');
                if (el.dataset.id === sessionId) {
                    el.classList.add('active');
                    currentChatTitle.textContent = el.textContent;
                }
            });
        } catch (error) {
            console.error('Error switching session:', error);
        }
    }
    
    // Create a new chat session
    async function createNewChat() {
        try {
            const response = await fetch('/api/new_session', {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Clear current chat
            chatContainer.innerHTML = '';
            
            // Add welcome message
            addMessage('assistant', 'Hello! I\'m Zetheta AI, your document-aware assistant. How can I help you today?');
            
            // Hide source documents
            sourceDocuments.classList.add('d-none');
            
            // Set title
            currentChatTitle.textContent = 'New Conversation';
            
            // Refresh chat sessions list
            loadChatSessions();
        } catch (error) {
            console.error('Error creating new chat session:', error);
        }
    }
    
    // Load chat history for current session
    async function loadChatHistory() {
        try {
            const response = await fetch('/api/chat_history');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add each message to chat
            data.messages.forEach(message => {
                addMessage(message.role, message.content);
            });
            
            // If no messages, add welcome message
            if (data.messages.length === 0) {
                addMessage('assistant', 'Hello! I\'m Zetheta AI, your document-aware assistant. How can I help you today?');
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            
            // Add welcome message as fallback
            addMessage('assistant', 'Hello! I\'m Zetheta AI, your document-aware assistant. How can I help you today?');
        }
    }
    
    // Initial loading of chat sessions and history
    loadChatSessions();
    loadChatHistory();
});