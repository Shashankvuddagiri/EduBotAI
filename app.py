from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, session
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import PyPDF2
from PIL import Image
import io
import logging
import shutil
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = 'super secret key'  # Add a secret key for session

# Configure file upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Configure Gemini API
try:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    vision_model = genai.GenerativeModel('gemini-pro-vision')
    logger.info("Successfully configured Gemini API")
except Exception as e:
    logger.error(f"Error configuring Gemini API: {str(e)}")
    raise

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    """Delete files older than 1 hour"""
    current_time = datetime.now().timestamp()
    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            creation_time = os.path.getctime(filepath)
            if (current_time - creation_time) > 3600:  # 1 hour
                try:
                    os.remove(filepath)
                    logger.info(f"Deleted old file: {filename}")
                except Exception as e:
                    logger.error(f"Error deleting file {filename}: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_username', methods=['POST'])
def set_username():
    username = request.form.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    # Save username to session
    session['username'] = username
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    # Check if user has a username
    if 'username' not in session:
        return redirect('/')
    return render_template('dashboard.html')

@app.route('/redirect_dashboard')
def redirect_dashboard():
    return redirect('/dashboard')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        message = data['message']
        logger.info(f"Received chat message: {message[:50]}...")

        # Generate response using Gemini
        response = model.generate_content(message)
        if not response or not response.text:
            raise ValueError("Empty response from Gemini API")

        logger.info("Successfully generated chat response")
        return jsonify({'response': response.text})

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Failed to generate response'}), 500

@app.route('/api/analyze-file', methods=['POST'])
def analyze_file():
    try:
        cleanup_old_files()
        logger.info("Starting file analysis")
        
        if 'file' not in request.files:
            logger.warning("No file provided in request")
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.warning("Empty filename received")
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type'}), 400
            
        if file:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            logger.info(f"File saved: {filename}")
            
            try:
                if file.filename.lower().endswith('.pdf'):
                    text = extract_text_from_pdf(filename)
                    # Generate a more detailed analysis for PDFs
                    prompt = f"""Analyze this text and provide:
                    1. Summary of main points
                    2. Key concepts covered
                    3. Important takeaways
                    4. Suggested questions for understanding
                    
                    Text: {text[:2000]}"""  # Analyze first 2000 chars
                    
                    summary = model.generate_content(prompt).text
                else:
                    summary = analyze_image(filename)
                    
                logger.info("Successfully generated file analysis")
                return jsonify({'summary': summary})
            finally:
                try:
                    os.remove(filename)
                    logger.info(f"Cleaned up file: {filename}")
                except Exception as e:
                    logger.error(f"Error deleting file {filename}: {str(e)}")
                    
    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/generate-study-plan', methods=['POST'])
def generate_study_plan():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        subject = data.get('subject', 'General Studies')
        duration = data.get('duration', 4)
        
        logger.info(f"Generating study plan for {subject} ({duration} weeks)")

        # Generate study plan using Gemini
        prompt = f"Create a {duration}-week study plan for {subject}. Include weekly goals and daily tasks."
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            raise ValueError("Empty response from Gemini API")

        logger.info("Successfully generated study plan")
        return jsonify({'plan': response.text})

    except Exception as e:
        logger.error(f"Error generating study plan: {str(e)}")
        return jsonify({'error': 'Failed to generate study plan'}), 500

@app.route('/api/generate-quiz', methods=['POST'])
def generate_quiz():
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        num_questions = data.get('num_questions', 5)  # Default to 5 questions
        
        # Generate quiz using Gemini with more detailed prompt
        prompt = f"""Create a multiple-choice quiz about {topic} with {num_questions} questions of varying difficulty. 
        For each question, provide:
        1. A clear, concise question
        2. 4 plausible answer options
        3. The index of the correct answer (0-3)
        4. A brief explanation of why the correct answer is right
        
        Format the response as a strict JSON with this structure:
        {{
            "questions": [
                {{
                    "question": "...",
                    "options": ["option1", "option2", "option3", "option4"],
                    "correct": 0,
                    "explanation": "..."
                }}
            ]
        }}
        """
        
        response = model.generate_content(prompt)
        if not response or not response.text:
            raise ValueError("Empty response from Gemini API")

        # Parse the response as JSON
        quiz_data = json.loads(response.text)
        logger.info("Successfully generated quiz")
        return jsonify(quiz_data)

    except json.JSONDecodeError as je:
        logger.error(f"JSON Parsing Error: {str(je)}")
        return jsonify({'error': 'Failed to parse quiz JSON', 'details': str(je)}), 500
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        return jsonify({'error': 'Failed to generate quiz', 'details': str(e)}), 500

# Study Planner Routes
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        # Demo tasks
        tasks = [
            {
                'id': 1,
                'title': 'Python Basics',
                'start': '2025-01-31T14:00:00',
                'end': '2025-01-31T15:30:00',
                'status': 'completed'
            },
            {
                'id': 2,
                'title': 'Data Structures',
                'start': '2025-02-01T10:00:00',
                'end': '2025-02-01T11:30:00',
                'status': 'pending'
            }
        ]
        return jsonify(tasks)
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}")
        return jsonify({'error': 'Failed to get tasks'}), 500

@app.route('/api/tasks', methods=['POST'])
def add_task():
    try:
        task = request.get_json()
        # Here you would normally save to a database
        return jsonify({'message': 'Task added successfully'})
    except Exception as e:
        logger.error(f"Error adding task: {str(e)}")
        return jsonify({'error': 'Failed to add task'}), 500

@app.route('/api/optimize-schedule', methods=['POST'])
def optimize_schedule():
    try:
        data = request.get_json()
        prompt = f"""Given these study tasks: {data['tasks']}, 
        create an optimized study schedule considering:
        1. Task priority and deadlines
        2. Recommended study duration
        3. Breaks between sessions
        4. Best time of day for different subjects
        """
        response = model.generate_content(prompt)
        return jsonify({'schedule': response.text})
    except Exception as e:
        logger.error(f"Error optimizing schedule: {str(e)}")
        return jsonify({'error': 'Failed to optimize schedule'}), 500

# Quiz Routes
@app.route('/api/explain-answer', methods=['POST'])
def explain_answer():
    try:
        data = request.get_json()
        prompt = f"""Question: {data['question']}
        User's answer: {data['userAnswer']}
        Correct answer: {data['correctAnswer']}
        
        Explain why the correct answer is right and why the user's answer is wrong.
        Also provide a helpful memory tip or mnemonic.
        """
        response = model.generate_content(prompt)
        return jsonify({'explanation': response.text})
    except Exception as e:
        logger.error(f"Error explaining answer: {str(e)}")
        return jsonify({'error': 'Failed to get explanation'}), 500

# Flashcard Routes
@app.route('/api/generate-flashcards', methods=['POST'])
def generate_flashcards():
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        content = data.get('content', '')
        
        prompt = f"""Create study flashcards for: {topic}
        Content: {content}
        
        Generate:
        1. Key concepts and definitions
        2. Important examples
        3. Mnemonics and memory aids
        4. Practice questions
        
        Format as JSON with structure:
        {{
            "flashcards": [
                {{
                    "front": "...",
                    "back": "...",
                    "mnemonic": "..."
                }}
            ]
        }}
        """
        response = model.generate_content(prompt)
        return jsonify({'flashcards': json.loads(response.text)})
    except Exception as e:
        logger.error(f"Error generating flashcards: {str(e)}")
        return jsonify({'error': 'Failed to generate flashcards'}), 500

# Notes Routes
@app.route('/api/analyze-notes', methods=['POST'])
def analyze_notes():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extract text based on file type
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
        else:
            text = analyze_image(filepath)

        # Ensure text is not empty
        if not text:
            os.remove(filepath)
            return jsonify({'error': 'Could not extract text from file'}), 400

        # Use Gemini for comprehensive analysis
        analysis_prompts = [
            # Key Concepts
            f"""Analyze the following text and extract the most important key concepts:
            {text[:5000]}  # Limit to first 5000 characters to avoid token limits
            
            Provide a JSON response with:
            1. Top 5-10 key concepts
            2. Brief definition for each concept
            3. Relevance and importance""",
            
            # Summary
            f"""Create a comprehensive summary of the following text:
            {text[:5000]}
            
            Provide a JSON response with:
            1. Overall summary (3-4 sentences)
            2. Main topics covered
            3. Key takeaways""",
            
            # Learning Recommendations
            f"""Based on the content of this document, suggest:
            {text[:5000]}
            
            Provide a JSON response with:
            1. Related topics to explore
            2. Recommended next steps for learning
            3. Potential practice exercises"""
        ]

        # Collect analysis from multiple prompts
        comprehensive_analysis = {
            'key_concepts': {},
            'summary': {},
            'recommendations': {}
        }

        for i, prompt in enumerate(analysis_prompts, 1):
            try:
                response = model.generate_content(prompt)
                if response and response.text:
                    parsed_response = json.loads(response.text)
                    
                    # Store based on prompt type
                    if i == 1:
                        comprehensive_analysis['key_concepts'] = parsed_response
                    elif i == 2:
                        comprehensive_analysis['summary'] = parsed_response
                    else:
                        comprehensive_analysis['recommendations'] = parsed_response
            except Exception as parse_err:
                logger.error(f"Analysis prompt {i} parsing error: {str(parse_err)}")

        # Cleanup
        os.remove(filepath)
        
        return jsonify(comprehensive_analysis)

    except Exception as e:
        logger.error(f"Error analyzing notes: {str(e)}")
        return jsonify({'error': 'Failed to analyze notes', 'details': str(e)}), 500

# Learning Path Routes
@app.route('/api/analyze-progress', methods=['POST'])
def analyze_progress():
    try:
        data = request.get_json()
        user_data = data.get('userData', {})
        
        prompt = f"""Analyze the user's learning progress:
        Current skills and knowledge: {user_data.get('skills', [])}
        Completed topics: {user_data.get('completed', [])}
        Learning goals: {user_data.get('goals', [])}
        
        Provide:
        1. Skill assessment for each area
        2. Recommended next topics
        3. Areas needing improvement
        4. Personalized study tips
        5. Estimated timeline for goals
        
        Format as JSON with sections for each category.
        """
        
        response = model.generate_content(prompt)
        return jsonify({'analysis': json.loads(response.text)})
    except Exception as e:
        logger.error(f"Error analyzing progress: {str(e)}")
        return jsonify({'error': 'Failed to analyze progress'}), 500

# Helper functions
def extract_text_from_pdf(file_path):
    try:
        # Use PyPDF2 for text extraction
        import PyPDF2
        
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            full_text = ""
            
            # Extract text from all pages
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            return full_text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def analyze_image(file_path):
    try:
        # Use Gemini's vision capabilities to analyze the image
        from PIL import Image
        
        # Open the image
        img = Image.open(file_path)
        
        # Generate a prompt for comprehensive image analysis
        prompt = """Analyze this image and provide:
        1. A detailed description of the image contents
        2. Key insights or information
        3. Potential learning topics related to the image
        4. Suggested study questions based on the image
        """
        
        # Use Gemini's vision model to analyze the image
        response = model.generate_content([prompt, img])
        
        return response.text
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return f"Error processing image: {str(e)}"

@app.route('/open_dashboard')
def open_dashboard():
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
