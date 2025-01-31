document.addEventListener('DOMContentLoaded', function() {
    const chatInterface = document.getElementById('chat-interface');
    const dashboardContent = document.getElementById('dashboard-content');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    const chatMessages = document.getElementById('chat-messages');
    const newChatBtn = document.getElementById('new-chat-btn');
    const historyItems = document.querySelectorAll('.history-item');

    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Show chat interface when "New Chat" is clicked
    newChatBtn.addEventListener('click', function() {
        dashboardContent.style.display = 'none';
        chatInterface.style.display = 'flex';
        chatMessages.innerHTML = ''; // Clear previous messages
        chatInput.focus();
    });

    // Load chat history when clicking on a history item
    historyItems.forEach(item => {
        item.addEventListener('click', function() {
            const chatId = this.dataset.chatId;
            loadChatHistory(chatId);
        });
    });

    // Send message when button is clicked
    sendButton.addEventListener('click', sendMessage);

    // Send message when Enter is pressed (without Shift)
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessageToChat('user', message);

        // Clear input and reset height
        chatInput.value = '';
        chatInput.style.height = 'auto';

        // Disable input while waiting for response
        chatInput.disabled = true;
        sendButton.disabled = true;

        // Send to backend
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'message': message
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            // Add AI response to chat
            addMessageToChat('ai', data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            addMessageToChat('error', 'Sorry, there was an error processing your message. Please try again.');
        })
        .finally(() => {
            // Re-enable input
            chatInput.disabled = false;
            sendButton.disabled = false;
            chatInput.focus();
        });
    }

    function addMessageToChat(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        // Add message actions for AI messages
        if (type === 'ai') {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';
            actionsDiv.innerHTML = `
                <button class="action-button copy-button" title="Copy response">
                    <i class="fas fa-copy"></i>
                </button>
                <button class="action-button thumbs-up" title="Thumbs up">
                    <i class="fas fa-thumbs-up"></i>
                </button>
                <button class="action-button thumbs-down" title="Thumbs down">
                    <i class="fas fa-thumbs-down"></i>
                </button>
            `;
            contentDiv.appendChild(actionsDiv);

            // Add copy functionality
            const copyButton = actionsDiv.querySelector('.copy-button');
            copyButton.addEventListener('click', () => {
                navigator.clipboard.writeText(content).then(() => {
                    copyButton.innerHTML = '<i class="fas fa-check"></i>';
                    setTimeout(() => {
                        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                    }, 2000);
                });
            });
        }
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function loadChatHistory(chatId) {
        dashboardContent.style.display = 'none';
        chatInterface.style.display = 'flex';
        chatMessages.innerHTML = ''; // Clear previous messages

        // Load chat history from backend
        fetch(`/chat-history?chat_id=${chatId}`)
            .then(response => response.json())
            .then(data => {
                if (data.messages) {
                    data.messages.forEach(msg => {
                        addMessageToChat('user', msg.message);
                        addMessageToChat('ai', msg.response);
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                addMessageToChat('error', 'Failed to load chat history.');
            });
    }
});
