from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import json
from datetime import datetime
import uuid

app = Flask(__name__)

# Enable CORS for React integration
CORS(app, origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "http://localhost:5174", "https://safehaven.co.ke/", "https://safehaven.co.ke/chat" ])

# Crisis keywords that trigger immediate resources
CRISIS_KEYWORDS = [
    'suicide', 'kill myself', 'end it all', 'want to die', 'hurt myself',
    'emergency', 'danger', 'threatened', 'going to hurt me', 'scared for my life'
]

# Intent patterns for different types of support
INTENT_PATTERNS = {
    'crisis': ['emergency', 'danger', 'scared', 'threatened', 'hurt', 'violence'],
    'safety_planning': ['safety plan', 'leave', 'escape', 'get out', 'plan to leave'],
    'emotional_support': ['sad', 'depressed', 'alone', 'scared', 'confused', 'angry'],
    'resources': ['help', 'support', 'services', 'hotline', 'shelter', 'legal'],
    'greeting': ['hello', 'hi', 'hey', 'good morning', 'good evening'],
    'goodbye': ['bye', 'goodbye', 'thank you', 'thanks', 'end chat']
}

# Emergency resources
EMERGENCY_RESOURCES = [
    {
        "name": "National Domestic Violence Hotline",
        "phone": "1-800-799-7233",
        "text": "TEXT START to 88788",
        "website": "https://www.thehotline.org",
        "available": "24/7"
    },
    {
        "name": "Crisis Text Line",
        "text": "Text HOME to 741741",
        "available": "24/7"
    }
]

# General resources
GENERAL_RESOURCES = [
    {
        "name": "National Domestic Violence Hotline",
        "phone": "1-800-799-7233",
        "website": "https://www.thehotline.org",
        "description": "24/7 confidential support"
    },
    {
        "name": "National Sexual Assault Hotline",
        "phone": "1-800-656-4673",
        "website": "https://www.rainn.org",
        "description": "24/7 confidential support"
    },
    {
        "name": "211 Local Resources",
        "phone": "211",
        "description": "Local community services and resources"
    }
]

# Response templates organized by intent
RESPONSES = {
    'crisis': [
        "I'm very concerned about your safety. Please know that you deserve to be safe and there are people who can help you right now. If you're in immediate danger, please call 911.",
        "Your safety is the most important thing. You don't have to face this alone - there are trained professionals available 24/7 who want to help you."
    ],
    'safety_planning': [
        "Creating a safety plan is a brave and important step. A safety plan is a personalized, practical plan to help you avoid dangerous situations and know how to react when you're in danger.",
        "Safety planning is something trained advocates can help you with. They can work with you to create a plan that fits your specific situation."
    ],
    'emotional_support': [
        "What you're feeling is completely valid. Surviving domestic violence takes incredible strength, and you've already shown so much courage.",
        "It's normal to feel confused, scared, or overwhelmed. These feelings don't define you - they're natural responses to trauma.",
        "You are not alone in this. Many people have walked this path and found healing and safety. Your feelings matter and you deserve support."
    ],
    'resources': [
        "There are many resources available to help you. I can share information about hotlines, local services, legal support, and safety planning.",
        "Help is available 24/7. Would you like me to share some resources that might be helpful for your situation?"
    ],
    'greeting': [
        "Hello, and welcome to a safe space. I'm here to provide support and resources. You're brave for reaching out.",
        "Hi there. This is a confidential space where you can talk about what's on your mind. How are you feeling today?"
    ],
    'goodbye': [
        "Take care of yourself. Remember that you're strong and you deserve safety and happiness. The resources I've shared are always available.",
        "You've shown courage by reaching out. Please remember the resources we discussed, and know that support is always available when you need it."
    ],
    'default': [
        "I hear you, and I want you to know that your feelings are valid. You deserve to be treated with respect and kindness.",
        "Thank you for sharing with me. What you're going through is difficult, but you don't have to face it alone."
    ]
}

def detect_crisis(message):
    """Detect if message contains crisis keywords"""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in CRISIS_KEYWORDS)

def classify_intent(message):
    """Simple rule-based intent classification"""
    message_lower = message.lower()
    
    for intent, keywords in INTENT_PATTERNS.items():
        if any(keyword in message_lower for keyword in keywords):
            return intent
    
    return 'default'

def get_response(intent, crisis_detected=False):
    """Get appropriate response based on intent"""
    if crisis_detected:
        return RESPONSES['crisis'][0]
    
    if intent in RESPONSES:
        # For simplicity, return first response. In production, you might rotate or use more sophisticated selection
        return RESPONSES[intent][0]
    
    return RESPONSES['default'][0]

def get_resources(intent, crisis_detected=False):
    """Get relevant resources based on intent and crisis status"""
    if crisis_detected:
        return EMERGENCY_RESOURCES
    
    if intent in ['resources', 'safety_planning', 'crisis']:
        return GENERAL_RESOURCES
    
    return []

# In-memory session storage (use database in production)
sessions = {}

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Message is required"}), 400
        
        message = data['message'].strip()
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        # Initialize or get session
        if session_id not in sessions:
            sessions[session_id] = {
                'messages': [],
                'created_at': datetime.now()
            }
        
        # Add user message to session
        sessions[session_id]['messages'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Analyze message
        crisis_detected = detect_crisis(message)
        intent = classify_intent(message)
        
        # Generate response
        response_text = get_response(intent, crisis_detected)
        resources = get_resources(intent, crisis_detected)
        
        # Add bot response to session
        sessions[session_id]['messages'].append({
            'role': 'bot',
            'content': response_text,
            'timestamp': datetime.now().isoformat(),
            'intent': intent,
            'crisis_detected': crisis_detected
        })
        
        return jsonify({
            'response': response_text,
            'resources': resources,
            'crisis_detected': crisis_detected,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/resources', methods=['GET'])
def get_all_resources():
    """Get all available resources"""
    return jsonify({
        "emergency": EMERGENCY_RESOURCES,
        "general": GENERAL_RESOURCES
    })

@app.route('/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete session for privacy"""
    if session_id in sessions:
        del sessions[session_id]
        return jsonify({"message": "Session deleted successfully"})
    return jsonify({"message": "Session not found"}), 404

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Emotional Support Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Send a message to the chatbot",
            "GET /resources": "Get all available resources",
            "DELETE /session/<id>": "Delete a chat session",
            "GET /health": "Health check"
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)