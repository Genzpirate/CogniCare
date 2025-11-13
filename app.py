# Import the tools we just installed
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
# Add these new imports at the top of the file
import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv() # This loads the variables from your .env file


from flask import Flask, request, jsonify, render_template
import datetime # <-- Add this line
import random
import json
# Create our main application, like starting a new company
app = Flask(__name__)

# --- CONFIGURATION ---
# This is a secret password for the app itself to keep things safe
app.config['SECRET_KEY'] = 'a_super_secret_key_you_should_change'

# This tells our app where our database is located
# IMPORTANT: Replace 'username', 'password', and 'cognicare_db' with your actual PostgreSQL details
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:0000@localhost/cognicare_db'
# --------------------

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- HTML RENDERING ROUTES ---
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register.html')
def register_page():
    return render_template('register.html')


# --- CHECKLIST ADD ITEM ROUTE ---
@app.route('/add_checklist_item', methods=['POST'])
@login_required
def add_checklist_item():
    # 1. Get the text content from the JavaScript form
    data = request.get_json()
    content = data.get('content')

    if not content:
        return jsonify({'message': 'Content cannot be empty.'}), 400

    # 2. Create the new item linked to the current user
    new_item = ChecklistItem(
        user_id=current_user.id,
        content=content,
        is_completed=False
    )
    
    # 3. Add to database and save
    db.session.add(new_item)
    db.session.commit()
    
    # 4. Send the new item's data back to the frontend
    return jsonify({
        'message': 'Item added!',
        'item': {
            'item_id': new_item.item_id,
            'content': new_item.content,
            'is_completed': new_item.is_completed
        }
    }), 201    

@app.route('/dashboard.html')
@login_required
def dashboard_page():
    health_alert_data = get_local_health_alert()
    daily_myth_data = get_daily_myth() # <-- This line now calls our new function
    checklist_items = ChecklistItem.query.filter_by(user_id=current_user.id).order_by(ChecklistItem.created_at).all()
    
    return render_template(
        'dashboard.html', 
        health_alert=health_alert_data,
        daily_myth=daily_myth_data,
        checklist_items=checklist_items  # <-- Pass the items to the HTML
    )

# Initialize our database and password-scrambler tools
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)


# --- DATABASE BLUEPRINT (MODEL) ---
# This class is a "blueprint" for a user. It tells Python what a user looks like
# and that it matches the "users" table in our database.
class User(db.Model, UserMixin):
    __tablename__ = 'users'  # Explicitly name the table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(50))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)


class SymptomLog(db.Model):
    __tablename__ = 'symptom_logs'
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symptom_name = db.Column(db.String(100), nullable=False)
    log_date = db.Column(db.Date, nullable=False)
    severity = db.Column(db.String(50))
    notes = db.Column(db.Text)


# This class is a "blueprint" for a checklist item.
class ChecklistItem(db.Model):
    __tablename__ = 'checklist_items'
    item_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=db.func.current_timestamp())


    # --- USER LOADER ---
# This function helps Flask-Login understand how to find a specific user from our database.
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

#2.  Stick to common wellness, nutrition, or everyday health topics.
#Your task is to generate one common, safe, and verifiable health "myth" and its corresponding "fact".
#1.  Do not discuss severe diseases, medications, or life-threatening conditions.

def get_daily_myth():
    """
    Generates a new myth/fact by calling the Gemini API.
    This version does NOT use a JSON file.
    """
    try:
        # 1. Create a prompt to generate a health myth and fact
        prompt = f"""
        You are CogniCare, a health awareness AI.
        Your task is to generate one verifiable health "myth" and its corresponding "fact".
        
        RULES:
        1.  The "fact" must be widely accepted scientific knowledge and random.
        2.  You MUST format your response with "MYTH:" and "FACT:" as separators.
        
        Example:
        MYTH: Cracking your knuckles will give you arthritis.
        FACT: Fact: There is no scientific evidence to support this. The 'pop' sound is just gas bubbles bursting in your joint fluid.

        Generate a new one now.
        """

        # 2. Call the Gemini API
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        ai_choice_text = response.text

        # 3. Parse the AI's response
        if "FACT:" in ai_choice_text and "MYTH:" in ai_choice_text:
            parts = ai_choice_text.split("FACT:", 1)
            selected_myth = parts[0].replace("MYTH:", "").strip()
            selected_fact = "Fact: " + parts[1].strip()
            
            return {
                "myth": selected_myth,
                "fact": selected_fact
            }
        else:
            # If the AI formatted it weirdly, raise an error to use the fallback
            raise Exception("AI response format was not as expected.")

    except Exception as e:
        # --- Fallback in case the API fails or has an error ---
        print(f"Error calling AI for myth: {e}. Falling back to a hardcoded default.")
        # We will use one single, safe, hardcoded myth as a fallback
        return {
            "myth": "Going out in the cold weather will give you a cold.",
            "fact": "Fact: Colds are caused by viruses, not by cold air. You get sick by being exposed to a virus, often indoors."
        }



def get_local_health_alert():
    """
    Simulates a local health alert API for Bengaluru.
    """
    current_month = datetime.datetime.now().month

    # Post-monsoon season (Aug to Nov) is high-risk for Dengue
    if current_month >= 8 and current_month <= 11:
        alert = {
            'level': 'High Risk',
            'illness': 'Dengue Fever',
            'message': 'Post-monsoon season is a peak time for Dengue. Ensure no stagnant water is near your home.',
            'color_class': 'alert-orange' # CSS class we will create
        }
    else:
        alert = {
            'level': 'Low Risk',
            'illness': 'General Alert',
            'message': 'Health risks are currently low. Continue to follow good hygiene practices.',
            'color_class': 'alert-green'
        }
    return alert


# --- USER LOGIN ROUTE ---
# This is the instruction for logging in an existing user.
@app.route('/login', methods=['POST'])
def login():
    # 1. Get the email and password the user submitted.
    data = request.get_json()
    
    # 2. Find the user in our database by their email.
    user = User.query.filter_by(email=data['email']).first()
    
    # 3. Check if we found a user AND if their password matches the secret code we have stored.
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        # If they match, log them in and remember them.
        login_user(user)
        return jsonify({'message': 'Login successful!'}), 200
    
    # 4. If the email or password don't match, send an error message.
    return jsonify({'message': 'Invalid email or password.'}), 401

# --- USER REGISTRATION ROUTE ---
# This is the instruction for signing up a new user.
@app.route('/register', methods=['POST'])
def register():
    # 1. Get the data the user submitted (e.g., from a registration form).
    data = request.get_json()

    # 2. Check if a user with this email already exists in our database.
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        # If they do, send back an error message.
        return jsonify({'message': 'An account with this email already exists.'}), 409

    # 3. If the email is new, take the user's password and scramble it into a secret code (hash).
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    # 4. Create a new user "object" using our User blueprint, filling it with their info.
    new_user = User(
        name=data['name'],
        email=data['email'],
        age=data['age'],
        gender=data['gender'],
        password_hash=hashed_password
    )

    # 5. Add the new user to our database session and save the changes.
    db.session.add(new_user)
    db.session.commit()

    # 6. Send a success message back.
    return jsonify({'message': 'User registered successfully!'}), 201


# --- CHATBOT LOGIC ROUTE ---
@app.route('/chat', methods=['POST'])
@login_required # Ensures only logged-in users can use the chat
def chat():
    # 1. Get the user's message from the frontend
    user_message = request.json['message']

    # 2. Get the user's details for personalization
    user_name = current_user.name
    user_age = current_user.age

    # 3. Create the prompt for the AI model
    prompt = f"""
    You are CogniCare, a helpful and empathetic AI Public Health Chatbot.
    Your user's name is {user_name} and they are {user_age} years old.
    Your primary goal is to provide clear, safe, and reliable health information for disease awareness and prevention.
    
    IMPORTANT RULES:
    1. NEVER provide a diagnosis.
    2. ALWAYS include this disclaimer at the end of every response: "Disclaimer: I am an AI assistant and not a medical professional. Please consult a doctor for medical advice."
    3. If a question is outside the scope of health and wellness, politely decline to answer.
    4. Keep your answers concise and easy to understand.
    
    User's question: "{user_message}"
    """

    # 4. Send the prompt to the AI and get the response
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        bot_reply = response.text
    except Exception as e:
        # Handle potential API errors
        print(f"Error generating content: {e}")
        bot_reply = "Sorry, I'm having trouble connecting right now. Please try again later."
    
    # 5. Send the response back to the frontend
    return jsonify({'reply': bot_reply})


@app.route('/calendar.html')
@login_required
def calendar_page():
    return render_template('calendar.html')



# --- SYMPTOM LOGGING ROUTE ---
@app.route('/log_symptom', methods=['POST'])
@login_required
def log_symptom():
    # 1. Get the data sent from the JavaScript form
    data = request.get_json()
    
    # 2. Prepare the data for the database
    new_log = SymptomLog(
        user_id=current_user.id,
        symptom_name=data['symptom'],
        log_date=data['log_date'],
        severity=data['severity'],
        notes=data['notes']
    )
    
    # 3. Add the new log to the database and save it
    db.session.add(new_log)
    db.session.commit()
    
    # 4. Send a success message back to the frontend
    return jsonify({'message': 'Symptom logged successfully!'}), 201


# --- FETCH SYMPTOMS ROUTE ---
@app.route('/get_symptoms', methods=['GET'])
@login_required
def get_symptoms():
    # Get the month and year from the request, sent by the calendar
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    # Query the database for symptoms for the current user in the given month and year
    symptoms = SymptomLog.query.filter(
        SymptomLog.user_id == current_user.id,
        #extract('year', SymptomLog.log_date) == year,
        #extract('month', SymptomLog.log_date) == month
    ).all()

    # Format the data into a list that the calendar library can understand
    events = []
    for symptom in symptoms:
        color = '#F5A623' # Default Orange for Moderate
        if symptom.severity == 'Mild':
            color = '#7ED321' # Green
        elif symptom.severity == 'Severe':
            color = '#D0021B' # Red

        events.append({
            'title': symptom.symptom_name,
            'start': symptom.log_date.isoformat(),
            'color': color,
            'extendedProps': {
                'notes': symptom.notes,
                'severity': symptom.severity
            }
        })

    return jsonify(events)


# --- AI TREND ANALYSIS ROUTE ---
@app.route('/analyze_trends', methods=['POST'])
@login_required
def analyze_trends():
    # 1. Fetch all symptoms for the current user, ordered by date
    symptoms = SymptomLog.query.filter_by(user_id=current_user.id).order_by(SymptomLog.log_date).all()

    if not symptoms:
        return jsonify({'analysis': 'Not enough data to analyze. Please log more symptoms.'})

    # 2. Simple pattern detection logic in Python
    # We'll create a simple text summary of the user's health logs.
    health_summary = f"Health log for {current_user.name} ({current_user.age} years old):\n"
    for log in symptoms:
        health_summary += f"- On {log.log_date.strftime('%Y-%m-%d')}, logged '{log.symptom_name}' with {log.severity} severity. Notes: {log.notes}\n"

    # 3. Create a safe, detailed prompt for the AI model
    prompt = prompt = f"""
    You are CogniCare, a health analysis AI. Your role is to analyze a user's self-reported symptom log and provide a general, non-diagnostic, and safe summary with actionable wellness tips.

    IMPORTANT SAFETY RULES:
    1.  YOU MUST NOT DIAGNOSE ANY CONDITION or mention specific diseases.
    2.  Your PRIMARY advice for any persistent or severe symptom MUST be to consult a doctor.
    3.  Frame your analysis around patterns, not diagnoses. Use phrases like "We noticed a pattern of..."
    4.  You MUST include the standard disclaimer at the end of your response.

    GENERAL WELLNESS ADVICE GUIDELINES:
    - If you see a pattern of 'Headache' or 'Fatigue' for 2-3 consecutive days, you can suggest improving hydration (drinking more water) and ensuring adequate sleep as general wellness tips.
    - If you see a pattern of 'Stomach Ache' with 'Mild' severity, you can mention the importance of a balanced diet and being mindful of trigger foods.
    - If you see a pattern of 'Cough', you can suggest drinking warm liquids like tea or soup to soothe the throat.
    - These suggestions are ONLY for mild, non-persistent patterns. For anything lasting longer than 3 days or marked as 'Severe', your main advice MUST be to see a doctor.

    Here is the user's health summary:
    ---
    {health_summary}
    ---
    
    Based on the summary and adhering strictly to all rules and guidelines, please provide a brief, one-paragraph analysis of their health trends, incorporating relevant wellness tips if applicable.
    """

    # 4. Send the prompt to the AI and get the response
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        analysis_text = response.text
    except Exception as e:
        print(f"Error generating analysis: {e}")
        analysis_text = "Sorry, I was unable to analyze your trends at this time."

    return jsonify({'analysis': analysis_text})


# --- CHECKLIST UPDATE ITEM ROUTE (for checking the box) ---
@app.route('/update_checklist_item/<int:item_id>', methods=['POST'])
@login_required
def update_checklist_item(item_id):
    item = db.session.get(ChecklistItem, item_id) # Modern syntax
    
    if not item or item.user_id != current_user.id:
        return jsonify({'message': 'Item not found.'}), 404
        
    data = request.get_json()
    item.is_completed = data.get('is_completed')
    
    db.session.commit()
    return jsonify({'message': 'Item updated!'}), 200

# --- CHECKLIST DELETE ITEM ROUTE ---
@app.route('/delete_checklist_item/<int:item_id>', methods=['POST'])
@login_required
def delete_checklist_item(item_id):
    item = db.session.get(ChecklistItem, item_id) # Modern syntax
    
    if not item or item.user_id != current_user.id:
        return jsonify({'message': 'Item not found.'}), 404
        
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted!'}), 200   

# This part makes the server run when you execute the file
if __name__ == '__main__':
    app.run(debug=True)