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
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const mainContent = document.getElementById('main-content');
    const searchInput = document.getElementById('search-conversations');
    const searchBtn = document.getElementById('search-btn');
    const followUpSuggestions = document.getElementById('follow-up-suggestions');
    
    // Initialize enhanced features
    initializeSidebarToggle();
    initializeSearch();
    initializeFollowUpSuggestions();
    
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
    
    // Enhanced message function with hover actions and expandable responses
    function addMessageEnhanced(role, content, isLongResponse = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = role === 'user' ? 'user-message' : 'assistant-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Add hover actions
        const messageActions = document.createElement('div');
        messageActions.className = 'message-actions';
        
        // Copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-action-btn';
        copyBtn.innerHTML = '<i data-feather="copy"></i>';
        copyBtn.title = 'Copy message';
        copyBtn.addEventListener('click', () => copyToClipboard(content));
        
        // Edit button (only for user messages)
        if (role === 'user') {
            const editBtn = document.createElement('button');
            editBtn.className = 'message-action-btn';
            editBtn.innerHTML = '<i data-feather="edit-2"></i>';
            editBtn.title = 'Edit message';
            editBtn.addEventListener('click', () => editMessage(messageDiv, content));
            messageActions.appendChild(editBtn);
        }
        
        messageActions.appendChild(copyBtn);
        messageDiv.appendChild(messageActions);
        
        // Handle expandable responses for long content
        if (isLongResponse && content.length > 500) {
            const responseContainer = document.createElement('div');
            responseContainer.className = 'response-expandable';
            
            const responseContent = document.createElement('div');
            responseContent.className = 'response-content';
            responseContent.innerHTML = formatMessageContent(content);
            
            const expandToggle = document.createElement('button');
            expandToggle.className = 'expand-toggle';
            expandToggle.textContent = 'Show more';
            expandToggle.addEventListener('click', () => toggleExpand(responseContent, expandToggle));
            
            responseContainer.appendChild(responseContent);
            responseContainer.appendChild(expandToggle);
            messageContent.appendChild(responseContainer);
        } else {
            messageContent.innerHTML = formatMessageContent(content);
        }
        
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
        
        // Re-initialize feather icons for new buttons
        feather.replace();
        
        return messageDiv;
    }
    
    // Helper function to format message content
    function formatMessageContent(content) {
        let formattedContent = content;
        formattedContent = formattedContent.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        formattedContent = formattedContent.replace(/\n/g, '<br>');
        return formattedContent;
    }
    
    // Helper function to toggle expandable responses
    function toggleExpand(contentDiv, toggleBtn) {
        if (contentDiv.classList.contains('expanded')) {
            contentDiv.classList.remove('expanded');
            toggleBtn.textContent = 'Show more';
        } else {
            contentDiv.classList.add('expanded');
            toggleBtn.textContent = 'Show less';
        }
    }
    
    // Helper function to copy text to clipboard
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Message copied to clipboard');
        });
    }
    
    // Helper function to edit message
    function editMessage(messageDiv, originalContent) {
        userInput.value = originalContent;
        userInput.focus();
        userInput.style.height = 'auto';
        userInput.style.height = (userInput.scrollHeight) + 'px';
    }
    
    // Initialize sidebar toggle functionality
    function initializeSidebarToggle() {
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('show');
            });
        }
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && 
                sidebar.classList.contains('show') && 
                !sidebar.contains(e.target) && 
                !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }
    
    // Initialize search functionality
    function initializeSearch() {
        let searchTimeout;
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    filterChatSessions(e.target.value);
                }, 300);
            });
        }
        
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                filterChatSessions(searchInput.value);
            });
        }
    }
    
    // Filter chat sessions based on search query
    function filterChatSessions(query) {
        const sessions = document.querySelectorAll('.chat-session-wrapper');
        const lowercaseQuery = query.toLowerCase();
        let visibleCount = 0;
        
        sessions.forEach(session => {
            const sessionText = session.textContent.toLowerCase();
            if (sessionText.includes(lowercaseQuery)) {
                session.style.display = 'block';
                visibleCount++;
            } else {
                session.style.display = 'none';
            }
        });
        
        // Show "no results" message if needed
        const existingNoResults = document.querySelector('.no-results');
        if (existingNoResults) {
            existingNoResults.remove();
        }
        
        if (visibleCount === 0 && query.length > 0) {
            const noResults = document.createElement('div');
            noResults.className = 'no-results';
            noResults.textContent = 'No conversations found';
            chatSessions.appendChild(noResults);
        }
    }
    
    // Initialize follow-up suggestions
    function initializeFollowUpSuggestions() {
        // Hide suggestions initially
        followUpSuggestions.classList.add('d-none');
    }
    
    // Show follow-up suggestions after assistant response
    function showFollowUpSuggestions(suggestions = null) {
        if (!suggestions) {
            suggestions = generateContextualSuggestions();
        }
        
        const suggestionsContainer = followUpSuggestions.querySelector('div');
        suggestionsContainer.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const chip = document.createElement('span');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            chip.addEventListener('click', () => {
                userInput.value = suggestion;
                userInput.focus();
                hideFollowUpSuggestions();
            });
            suggestionsContainer.appendChild(chip);
        });
        
        followUpSuggestions.classList.remove('d-none');
    }
    
    // Hide follow-up suggestions
    function hideFollowUpSuggestions() {
        followUpSuggestions.classList.add('d-none');
    }
    
    // Generate contextual suggestions
    function generateContextualSuggestions() {
        const suggestions = [
            "Can you elaborate on that?",
            "What are the key points?",
            "How can I apply this?",
            "What should I know next?",
            "Can you give me an example?"
        ];
        
        // Shuffle and return 3 random suggestions
        return suggestions.sort(() => 0.5 - Math.random()).slice(0, 3);
    }
    
    // Enhanced addMessage function to replace the original
    function addMessage(role, content) {
        const isLongResponse = role === 'assistant' && content.length > 500;
        const messageDiv = addMessageEnhanced(role, content, isLongResponse);
        
        // Show follow-up suggestions after assistant responses
        if (role === 'assistant') {
            setTimeout(() => {
                showFollowUpSuggestions();
            }, 1000);
        } else {
            hideFollowUpSuggestions();
        }
        
        return messageDiv;
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
    
    // Enhanced chat session creation with hover actions
    function createChatSessionElement(session) {
        const sessionWrapper = document.createElement('div');
        sessionWrapper.className = 'chat-session-wrapper';
        
        const sessionDiv = document.createElement('div');
        sessionDiv.className = 'chat-session nav-link';
        sessionDiv.dataset.id = session.id;
        
        const sessionTitle = document.createElement('span');
        sessionTitle.className = 'chat-session-title';
        sessionTitle.textContent = session.title;
        
        const sessionActions = document.createElement('div');
        sessionActions.className = 'chat-session-actions';
        
        // Copy session ID button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'chat-action-btn';
        copyBtn.innerHTML = '<i data-feather="copy"></i>';
        copyBtn.title = 'Copy session ID';
        copyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            copyToClipboard(session.id);
        });
        
        // Delete button
        const deleteBtn = createDeleteButton(session.id);
        
        sessionActions.appendChild(copyBtn);
        sessionActions.appendChild(deleteBtn);
        
        sessionDiv.appendChild(sessionTitle);
        sessionDiv.appendChild(sessionActions);
        sessionWrapper.appendChild(sessionDiv);
        
        // Add click handler for session switching
        sessionDiv.addEventListener('click', () => {
            switchSession(session.id);
        });
        
        return sessionWrapper;
    }
    
    // Load chat sessions with enhanced features
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
            
            // Add each session using enhanced creation
            data.sessions.forEach(session => {
                const sessionWrapper = createChatSessionElement(session);
                
                // Set active state if this is the current session
                if (currentSessionId === session.id) {
                    sessionWrapper.querySelector('.chat-session').classList.add('active');
                }
                
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
    
    // Toast notification system
    function showToast(message, duration = 3000) {
        // Remove existing toast
        const existingToast = document.querySelector('.toast-notification');
        if (existingToast) {
            existingToast.remove();
        }
        
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--bs-success);
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            z-index: 10000;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // Fade in
        setTimeout(() => {
            toast.style.opacity = '1';
        }, 100);
        
        // Fade out and remove
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }
    
    // Initial loading of chat sessions and history
    loadChatSessions();
    loadChatHistory();
});
