from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_session import Session
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import google.generativeai as genai
import os
import requests
import datetime
import json
import random
import nltk
import re
import spacy
 
# Download required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')

# Initialize spaCy and sentiment analyzer
nlp = spacy.load("en_core_web_sm")
sentiment_analyzer = SentimentIntensityAnalyzer()

genai.configure(api_key=os.environ["API_KEY"])

# Initialize Flask app
app = Flask(__name__)

# Configure Flask to use sessions (store on filesystem)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'supersecretkey'  # Required to use session
Session(app)

# Setup SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
Session(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    chats = db.relationship('ChatHistory', backref='user', lazy=True)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)

# Initialize the database
with app.app_context():
    db.create_all()

# Load intents from JSON file
with open('intents.json') as f:
    intents = json.load(f)

# Sentiment analysis function with strong positive/negative thresholds
def analyze_sentiment(user_input):
    """Analyze the sentiment of user input using VADER and detect strong sentiments."""
    sentiment_scores = sentiment_analyzer.polarity_scores(user_input)
    
    # Debugging: Print sentiment scores to console
    print(f"Sentiment analysis for '{user_input}': {sentiment_scores}")
    
    # Strong Positive 
    if sentiment_scores['compound'] > 0.4:
        return 'positive'
    
    # Strong Negative
    elif sentiment_scores['compound'] < -0.4:
        return 'negative'
    
    # Everything else is neutral
    else:
        return 'neutral'
    
import requests

def gemini_fallback(user_input):
    """Use Gemini API SDK to generate content as a fallback."""
    
    try:
        # Specify the model to use
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Generate a response using the Gemini model
        response = model.generate_content(user_input)
        
        # Return the generated response text
        return response.text

    except Exception as e:
        print(f"Error communicating with Gemini API: {e}")
        return "Sorry, something went wrong while trying to process your request."


def get_news(api_key="fc016c0ac52745dd9118efaee5ef1096"):
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        articles = data.get("articles", [])
        if articles:
            news_headlines = [f" -> {article['title']}  " for article in articles[:5]]
            return "Here are some of the latest news headlines:\n" + "\n".join(news_headlines)
        else:
            return "Sorry, I couldn't find any news articles right now."
    except Exception as e:
        return f"Error fetching news: {str(e)}"

def get_movies(api_key="be01c0d709040362032aa9de9a664881"):
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1"
    try:
        response = requests.get(url)
        data = response.json()
        movies = data.get("results", [])
        if movies:
            movie_titles = [f"- {movie['title']}" for movie in movies[:5]]
            return "Here are some popular movies:\n" + "\n".join(movie_titles)
        else:
            return "Sorry, I couldn't find any movie recommendations right now."
    except Exception as e:
        return f"Error fetching movie data: {str(e)}"

def get_weather(city_name, api_key="9eb7d214877e5e39789c8601fb5ab232"):
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={city_name}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(complete_url)
        data = response.json()
        
        if data.get("cod") == 200:
            weather_info = data["main"]
            weather_desc = data["weather"][0]["description"]
            temp = weather_info["temp"]
            return f"The temperature in {city_name} is {temp}°C with {weather_desc}."
        else:
            return data.get("message", "Unable to fetch weather data.")
    
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"

def extract_entities(text):
    doc = nlp(text)
    entities = {ent.label_: ent.text for ent in doc.ents}
    return entities

def extract_city_from_input(user_input):
    entities = extract_entities(user_input)
    return entities.get("GPE", None)

def get_current_datetime():
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%d-%m-%Y")
    return f"The current time is {current_time} and the date is {current_date}."

def process_input(text, remove_stopwords=True):
    stop_words = set(stopwords.words('english'))
    text = re.sub(r'[^\w\s]', '', text.lower())
    tokens = word_tokenize(text)
    
    if remove_stopwords:
        return [word for word in tokens if word not in stop_words]
    else:
        return tokens

def match_intent(user_input):
    user_tokens = set(process_input(user_input))
    

    best_match = None
    highest_token_match_ratio = 0

    entities = extract_entities(user_input)

    if "weather" in user_tokens:
        city_name = entities.get("GPE")
        if city_name:
            return get_weather(city_name)
        else:
            return None

    if "time" in user_tokens or "date" in user_tokens:
        return get_current_datetime()
    
    if "news" in user_tokens:
        return get_news()
    
    if "movies" in user_tokens or "entertainment" in user_tokens:
        return get_movies()

    for intent in intents['intents']:
        for pattern in intent['patterns']:
            normalized_input = ' '.join(process_input(user_input, remove_stopwords=False))
            normalized_pattern = ' '.join(process_input(pattern, remove_stopwords=False))

            if normalized_input == normalized_pattern:
                return random.choice(intent['responses'])

            pattern_tokens = set(process_input(pattern))
            if pattern_tokens:
                common_tokens = user_tokens & pattern_tokens
                match_ratio = len(common_tokens) / len(pattern_tokens)
                if match_ratio > highest_token_match_ratio:
                    highest_token_match_ratio = match_ratio
                    best_match = random.choice(intent['responses'])

    if highest_token_match_ratio <= 0.5:
        return None
    
    return best_match



def chatbot_response(user_input):
    """Handle user input and return an appropriate response while maintaining context."""
    
    # Step 1: Check sentiment first
    sentiment = analyze_sentiment(user_input)
    
    if sentiment == 'positive':
        return "I'm glad you're feeling positive! How can I assist you further?"
    
    elif sentiment == 'negative':
        return "I'm sorry to hear that you're feeling sad. I'm here to help. What's bothering you?"
    # Retrieve previous context from session
    previous_context = session.get('context', {})
    current_topic = previous_context.get('topic', None)  # Retrieve the current topic from the session
    last_intent = previous_context.get('last_intent', None)

    # Step 1: Process follow-up questions in context (e.g., for weather)
    if current_topic == 'weather':
        city_name = extract_city_from_input(user_input)
        if city_name:
            # Handle a follow-up weather request with a new city
            response = get_weather(city_name)
            session['context']['last_intent'] = 'weather'
            session['context']['topic'] = 'weather'  # Maintain weather context
            return response
        elif "and" in user_input:
            return "Please provide a city name for the weather."
    
    # Step 2: Handle follow-up questions like "Tell me more" or "What about it?"
    if "more" in user_input or "tell me more" in user_input:
        if last_intent == 'weather':
            return "I can provide more details about the weather. Ask me about another city."
        return "Could you clarify what you'd like to know more about?"

    # Step 3: Handle specific user inputs like "news", "movies", or "weather"
    intent_response = match_intent(user_input)

    # Step 4: Handle weather-specific queries (if 'weather' is mentioned)
    if 'weather' in user_input and not extract_city_from_input(user_input):
        session['context'] = {'awaiting_city': True, 'topic': 'weather'}  # Set context to wait for city
        return "Which city would you like the weather for?"

    if 'weather' in user_input:
        city_name = extract_city_from_input(user_input)
        if city_name:
            session['context'] = {'topic': 'weather', 'last_intent': 'weather'}  # Set context to weather
            return get_weather(city_name)

    # Step 5: If intent matches, respond with the matched intent
    if intent_response:
        session['context'] = {'last_intent': intent_response, 'topic': 'general'}  # Set general conversation context
        return intent_response

    # Step 6: Fallback to Gemini API if no intents match
    print("No intent matched. Falling back to Gemini API.")
    return gemini_fallback(user_input)





@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.", "danger")
            return redirect(url_for('login'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route("/get_response", methods=["POST"])
def get_bot_response():
    user_input = request.form["user_input"]

    if 'user_id' not in session:
        return jsonify({"response": "Please log in to chat."})

    bot_response = chatbot_response(user_input)

    user_id = session['user_id']
    new_chat = ChatHistory(user_id=user_id, user_message=user_input, bot_response=bot_response)
    db.session.add(new_chat)
    db.session.commit()

    return jsonify({"response": bot_response})

@app.route("/get_chat_history", methods=["GET"])
def get_chat_history():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 403
    
    user_id = session['user_id']
    chats = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.id.desc()).limit(10).all()
    
    chat_data = [{"user_message": chat.user_message, "bot_response": chat.bot_response} for chat in chats]
    
    return jsonify({"chats": chat_data})

@app.route("/")
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
