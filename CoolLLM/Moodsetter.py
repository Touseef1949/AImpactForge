import streamlit as st
import requests
import time
import dotenv
import os
from gtts import gTTS
import io
import random

dotenv.load_dotenv()

# Initialize the Groq client
api_key = os.getenv("GROQ_API_KEY")
GROQ_API_KEY = api_key
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Replace if needed

# --- UI/UX Helpers ---

def set_background_color(mood):
    """Set the background color based on the user's mood."""
    mood_lower = mood.lower()
    if "sad" in mood_lower:
        color = "#add8e6"  # light blue
    elif "happy" in mood_lower:
        color = "#ffffe0"  # light yellow
    elif "anxious" in mood_lower:
        color = "#d3d3d3"  # light grey
    elif "excited" in mood_lower:
        color = "#ffdab9"  # peach
    else:
        color = "#ffffff"  # default white
    st.markdown(
        f"""
        <style>
        .reportview-container {{
            background-color: {color};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

@st.cache_data
def get_quote_from_api():
    """Fetch a random motivational quote from the ZenQuotes API."""
    try:
        response = requests.get("https://zenquotes.io/api/random")
        if response.status_code == 200:
            data = response.json()
            return data[0]["q"]
        else:
            return "Keep your head up and stay positive!"
    except Exception as e:
        return "Stay positive, every day is a new beginning!"

# Curated quotes for specific moods
mood_quotes = {
    "sad": [
        "Every storm runs out of rain.",
        "Tough times never last, but tough people do."
    ],
    "happy": [
        "Happiness is a journey, not a destination.",
        "Keep smiling, because life is a beautiful thing."
    ],
    "anxious": [
        "You don't have to control your thoughts, you just have to stop letting them control you.",
        "Inhale confidence, exhale doubt."
    ],
    "excited": [
        "Let your passion lead the way!",
        "The future belongs to those who believe in the beauty of their dreams."
    ]
}

def get_mood_based_quote(mood):
    """Return a quote based on the mood if available; otherwise, fetch a random quote."""
    mood_lower = mood.lower()
    for key in mood_quotes:
        if key in mood_lower:
            return random.choice(mood_quotes[key])
    return get_quote_from_api()

def generate_ai_response(name, mood):
    """Generate a comforting AI response using Groq's generative AI API."""
    prompt = f"User {name} is feeling {mood}. Provide a comforting and empathetic response to cheer them up."
    payload = {
        "model": "llama-3.3-70b-versatile",  # Ensure this model name is correct
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        data = response.json()
        if response.status_code == 200 and "choices" in data:
            return data["choices"][0]["message"]["content"]
        else:
            error_detail = data.get('error', 'Unknown API response error')
            return f"Error: {error_detail}"
    except Exception as e:
        return f"Exception: {str(e)}"

def text_to_speech(text):
    """Convert text to speech and return audio bytes."""
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp

def get_music_recommendation(mood):
    """Return a YouTube link for a music video based on the user's mood."""
    mood_lower = mood.lower()
    if "sad" in mood_lower:
        return "https://www.youtube.com/watch?v=2Vv-BfVoq4g"  # Example calm video
    elif "happy" in mood_lower:
        return "https://www.youtube.com/watch?v=ZbZSe6N_BXs"  # Uplifting track
    elif "anxious" in mood_lower:
        return "https://www.youtube.com/watch?v=UceaB4D0jpo"  # Relaxing music
    else:
        return "https://www.youtube.com/watch?v=5qap5aO4i9A"  # Default chill video

def get_daily_challenge():
    """Return a random daily affirmation or challenge."""
    challenges = [
        "Take a 10-minute walk outside today.",
        "Write down three things you're grateful for.",
        "Call a friend or loved one.",
        "Spend 5 minutes meditating.",
        "Try a new healthy recipe today."
    ]
    return random.choice(challenges)

# --- Streamlit UI ---

st.set_page_config(page_title="Mood Setter", page_icon="😊")
st.title("🌞 Mood Setter App")
st.write("Tell me how you're feeling today and I'll do my best to cheer you up!")

# Initialize session state for conversation history and journaling
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "journal_entries" not in st.session_state:
    st.session_state.journal_entries = []

# Collect user input for name and mood
name = st.text_input("Enter your name:")
mood = st.text_input("How are you feeling today?")

# Set background based on mood (if provided)
if mood:
    set_background_color(mood)

if st.button("Submit"):
    if name and mood:
        with st.spinner("Let me think..."):
            ai_response = generate_ai_response(name, mood)
            quote = get_mood_based_quote(mood)
            daily_challenge = get_daily_challenge()
            music_link = get_music_recommendation(mood)

            # Convert AI response to audio
            audio_bytes = text_to_speech(ai_response)

            # Save conversation details for history
            st.session_state.conversation_history.append({
                "name": name,
                "mood": mood,
                "ai_response": ai_response,
                "quote": quote,
                "challenge": daily_challenge,
                "music_link": music_link
            })

        st.subheader("💬 AI Response")
        st.write(f"🤗 {ai_response}")
        st.audio(audio_bytes, format="audio/mp3")

        st.subheader("📜 Motivational Quote")
        st.write(f"❝ {quote} ❞")

        st.subheader("🎯 Daily Challenge")
        st.write(f"💡 {daily_challenge}")

        st.subheader("🎵 Music Recommendation")
        st.write(f"[Click here to listen]({music_link})")

        # Display an animated GIF based on mood
        mood_lower = mood.lower()
        if "sad" in mood_lower:
            st.image("https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif", caption="Cheer up!")
        elif "happy" in mood_lower:
            st.image("https://media.giphy.com/media/l0HlOvJ7yaacpuSas/giphy.gif", caption="Keep smiling!")
        elif "anxious" in mood_lower:
            st.image("https://media.giphy.com/media/1BXa2alBjrCXC/giphy.gif", caption="Breathe in, breathe out.")
        else:
            st.image("https://media.giphy.com/media/26ufdipQqU2lhNA4g/giphy.gif", caption="Stay motivated!")

    else:
        st.warning("Please enter both your name and your current mood!")

# st.subheader("📝 Journal Your Thoughts")
# journal_text = st.text_area("Write your thoughts here...")
# if st.button("Save Journal Entry"):
#     if journal_text:
#         st.session_state.journal_entries.append(journal_text)
#         st.success("Journal entry saved!")
#     else:
#         st.warning("Please write something in your journal before saving.")

# if st.session_state.conversation_history:
#     st.subheader("🗒 Conversation History")
#     for entry in st.session_state.conversation_history:
#         st.write(f"**Name:** {entry['name']} | **Mood:** {entry['mood']}")
#         st.write(f"**AI Response:** {entry['ai_response']}")
#         st.write(f"**Quote:** {entry['quote']}")
#         st.write(f"**Daily Challenge:** {entry['challenge']}")
#         st.write(f"**Music Recommendation:** [Listen Here]({entry['music_link']})")
#         st.markdown("---")

# --- Reset Button ---
if st.button("Reset App"):
    st.session_state.conversation_history = []
    st.session_state.journal_entries = []
    st.rerun()
