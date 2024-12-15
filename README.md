# Pluto.ai - Python AI Chatbot 🤖

Pluto.ai is an AI-powered chatbot built using Flask on the backend and a responsive, interactive frontend. It leverages Natural Language Processing (NLP) and API integrations to deliver intelligent responses and provide features like sentiment analysis, weather updates, news headlines, and more.

---

## Features 🚀

### Backend (Python & Flask)
- **User Authentication**: Secure user registration and login system using Flask and SQLAlchemy.
- **Chat History**: Stores user-chatbot interactions in a SQLite database.
- **Sentiment Analysis**: Detects user emotions using NLTK's VADER sentiment analyzer.
- **NLP Integration**:
  - **Intent Matching**: Matches user queries with predefined intents.
  - **Entity Extraction**: Uses spaCy to extract relevant information like city names.
- **Generative AI Integration**: Google Gemini API as a fallback for unhandled queries.
- **API Integrations**:
  - **Weather**: Fetches live weather updates.
  - **News**: Retrieves top news headlines.
  - **Movies**: Displays popular movie recommendations.

### Frontend (HTML, CSS, JavaScript)
- **Responsive Design**: A sleek and modern design with glassmorphism effects and a space-themed background.
- **Dynamic Chat Interface**:
  - Real-time message handling and chat display.
  - Sentiment-based responses.
- **Pluto Animation**: A spinning Pluto planet SVG icon as a branding element.
- **Enhanced Message Formatting**:
  - Supports bold, italics, lists, and links in bot responses.
- **Logout Functionality**: Seamless logout for authenticated users.

---

## Usage 🛠️

### Chat Commands

- **Weather**: Ask about the weather in a city (e.g., "What's the weather in Mumbai?").
- **News**: Request the latest headlines (e.g., "Tell me the news").
- **Movies**: Get popular movie recommendations (e.g., "Suggest some movies").
- **AI Chat**: Ask general questions for intelligent AI responses.

---


  

