# EduBotAI

An intelligent educational assistant powered by Google's Gemini AI, designed to provide personalized learning experiences.

## Features

### 1. Interactive Chat
- Real-time conversations with Gemini AI
- Context-aware responses
- Educational guidance and explanations
- Support for multiple subjects and topics

### 2. Study Plans
- Personalized study plan generation
- Customizable duration (1 week to 1 month)
- Difficulty level adaptation (beginner, intermediate, advanced)
- Progress tracking and adjustments

### 3. Quiz Generation
- Dynamic quiz creation based on topics
- Customizable number of questions
- Instant feedback and explanations
- Score tracking and performance analytics

### 4. Flashcards
- AI-generated flashcard sets
- Topic-based organization
- Spaced repetition support
- Progress tracking

### 5. Notes Management
- Upload and analyze study notes
- File format support: PDF, DOC, DOCX, TXT
- AI-powered content summarization
- Key concepts extraction

### 6. Progress Tracking
- Detailed performance analytics
- Study time monitoring
- Quiz score tracking
- Visual progress charts

## Tech Stack

### Backend
- **Framework**: Flask (Python)
- **AI/ML**: Google Gemini AI
- **Database**: SQLite
- **Authentication**: Flask-Login
- **Real-time Communication**: Flask-SocketIO
- **Security**: Flask-WTF (CSRF Protection)

### Frontend
- **Framework**: Bootstrap 5
- **Icons**: Bootstrap Icons
- **Fonts**: Inter (Google Fonts)
- **Charts**: Chart.js
- **Real-time Updates**: Socket.IO Client

### Additional Tools & Libraries
- **CORS**: Flask-CORS
- **File Handling**: Werkzeug
- **Environment Variables**: python-dotenv
- **Logging**: Python's built-in logging

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/EduBotAI.git
   cd EduBotAI
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `example.env` to `.env`
   - Add your Gemini API key to `.env`:
     ```
     GEMINI_API_KEY=your_api_key_here
     SECRET_KEY=your_secret_key_here
     ```

5. Initialize the database:
   ```bash
   flask init-db
   ```

6. Run the application:
   ```bash
   python app.py
   ```

7. Access the application:
   - Open your browser and navigate to `http://localhost:5000`
   - Register a new account or log in with existing credentials

## Project Structure

```
EduBotAI/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── schema.sql            # Database schema
├── .env                  # Environment variables
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
├── uploads/              # User uploaded files
└── utils/                # Utility functions
    └── gemini_helper.py  # Gemini AI integration
```

## Security Features

- CSRF Protection
- Secure Password Hashing
- Session Management
- File Upload Validation
- Input Sanitization
- HTTP-Only Cookies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for providing the AI capabilities
- Flask and its extensions for the robust backend framework
- Bootstrap for the responsive frontend design
- The open-source community for various tools and libraries
