// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendMessage = document.getElementById('sendMessage');
const fileInput = document.getElementById('fileInput');
const userName = document.getElementById('userName');

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
    initializeNavigation();
    loadUserName();
    addWelcomeMessage();
    initializeFlashcards();
    initializeSkillChart();
});

// Initialize dashboard components
function initializeDashboard() {
    initializeCalendar();
    initializeQuiz();
}

// Navigation
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.getAttribute('data-section');
            
            // Update active states
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Hide all sections and show selected one
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(section).classList.add('active');
        });
    });
}

// Calendar Initialization
function initializeCalendar() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: [
            {
                title: 'Python Basics',
                start: '2025-01-31T14:00:00',
                end: '2025-01-31T15:30:00',
                color: '#10b981'
            },
            {
                title: 'Data Structures',
                start: '2025-02-01T10:00:00',
                end: '2025-02-01T11:30:00',
                color: '#3b82f6'
            }
        ]
    });
    
    calendar.render();
}

// Quiz Initialization
function initializeQuiz() {
    const quizOptions = document.querySelectorAll('.quiz-option');
    quizOptions.forEach(option => {
        option.addEventListener('click', handleQuizAnswer);
    });
}

function handleQuizAnswer(e) {
    const option = e.currentTarget;
    const isCorrect = option.textContent === "<class 'list'>";
    
    // Remove previous states
    document.querySelectorAll('.quiz-option').forEach(opt => {
        opt.classList.remove('correct', 'incorrect');
    });
    
    // Add new state
    option.classList.add(isCorrect ? 'correct' : 'incorrect');
    
    // Get AI explanation
    if (!isCorrect) {
        getAIExplanation();
    }
}

async function getAIExplanation() {
    try {
        const response = await fetch('/api/explain-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: "What is the output of print(type([]))?",
                userAnswer: "<class 'array'>",
                correctAnswer: "<class 'list'>"
            })
        });
        
        if (!response.ok) throw new Error('Failed to get explanation');
        
        const data = await response.json();
        // Show explanation in a toast or modal
    } catch (error) {
        console.error('Failed to get explanation:', error);
    }
}

// Flashcards
function initializeFlashcards() {
    const flashcards = document.querySelectorAll('.flashcard');
    flashcards.forEach(card => {
        card.addEventListener('click', () => {
            card.classList.toggle('flipped');
        });
    });
}

// Skill Chart
function initializeSkillChart() {
    const ctx = document.getElementById('skillChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: [
                'Python Basics',
                'Data Structures',
                'Algorithms',
                'Web Development',
                'Database',
                'Problem Solving'
            ],
            datasets: [{
                label: 'Current Skills',
                data: [90, 75, 60, 85, 70, 80],
                fill: true,
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: 'rgb(59, 130, 246)',
                pointBackgroundColor: 'rgb(59, 130, 246)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(59, 130, 246)'
            }]
        },
        options: {
            elements: {
                line: { borderWidth: 3 }
            },
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            }
        }
    });
}

// Chat functionality
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage.click();
    }
});

// Add thinking animation to chat
function showThinkingAnimation() {
    const thinkingHtml = `
        <div class="message bot-message thinking-message">
            <div class="message-content">
                <div class="thinking-animation">
                    <span>EduBot is thinking</span>
                    <span class="dots">
                        <span class="dot">.</span>
                        <span class="dot">.</span>
                        <span class="dot">.</span>
                    </span>
                </div>
            </div>
        </div>
    `;
    chatMessages.insertAdjacentHTML('beforeend', thinkingHtml);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeThinkingAnimation() {
    const thinkingMessage = document.querySelector('.thinking-message');
    if (thinkingMessage) {
        thinkingMessage.remove();
    }
}

sendMessage.addEventListener('click', async () => {
    const userInput = messageInput.value.trim();
    if (!userInput) return;

    // Add user message
    addMessageToChat('user', userInput);
    messageInput.value = '';

    // Show thinking animation
    showThinkingAnimation();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userInput })
        });

        const data = await response.json();
        
        // Remove thinking animation before showing bot response
        removeThinkingAnimation();
        
        if (data.error) {
            addMessageToChat('ai', 'Sorry, I encountered an error. Please try again.');
        } else {
            addMessageToChat('ai', data.response);
        }
    } catch (error) {
        removeThinkingAnimation();
        addMessageToChat('ai', 'Sorry, I encountered an error. Please try again.');
    }
});

function addMessageToChat(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    
    if (type === 'ai') {
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
    } else if (type === 'user') {
        avatar.innerHTML = '<i class="fas fa-user"></i>';
    }
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;
    
    if (type === 'user') {
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(avatar);
    } else {
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// File handling
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
        addMessageToChat('error', 'Please upload a PDF or image file (JPG, PNG)');
        fileInput.value = '';
        return;
    }
    
    try {
        addMessageToChat('user', `Analyzing file: ${file.name}`);
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/analyze-file', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Failed to analyze file');
        
        const data = await response.json();
        addMessageToChat('ai', data.summary);
    } catch (error) {
        console.error('Failed to analyze file:', error);
        addMessageToChat('error', 'Sorry, I had trouble analyzing that file. Please try again.');
    } finally {
        fileInput.value = '';
    }
});

// Load user name
function loadUserName() {
    const name = localStorage.getItem('userName');
    if (!name) {
        window.location.href = '/';
        return;
    }
    userName.textContent = `Welcome, ${name}!`;
}

// Add welcome message
function addWelcomeMessage() {
    const welcomeMessage = "Hi! I'm your AI learning assistant. I can help you with your studies, answer questions, and analyze documents. How can I help you today?";
    addMessageToChat('ai', welcomeMessage);
}
