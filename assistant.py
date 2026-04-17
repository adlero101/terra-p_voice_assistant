import streamlit as st
from openai import OpenAI
import speech_recognition as sr
import edge_tts
import asyncio
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="TERRA-P", page_icon="🌱")
st.title("🌱 Therapeutic Enlightening Robust Retinue")

try:
    # This looks for GITHUB_TOKEN in your Streamlit Cloud Secrets or .streamlit/secrets.toml
    token = st.secrets["GITHUB_TOKEN"]
except Exception:
    st.error("Missing GITHUB_TOKEN! Please add it to your Streamlit Secrets.")
    st.stop()

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=token
)

# Initialize Session States
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Your name is TERRA-P. You are an empathetic, patient Mentor. Keep responses concise and supportive. Be a bit funny. Just use plain text and no emoji. Do not add asterisks."}
    ]
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

# the accent
async def generate_voice(text):
    """Generates a high-quality Indian Male voice using Edge-TTS"""
    # 'en-IN-PrabhatNeural' is the specific male Indian English voice
    communicate = edge_tts.Communicate(text, "en-IN-PrabhatNeural")
    await communicate.save("response.mp3")

# streamlit UI
for message in st.session_state.messages:
    if message["role"] != "system":
        avatar = "🤝" if message["role"] == "user" else "🌿"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# --- AUDIO INPUT ---
st.write("---")
audio_file = st.audio_input("Record your thoughts")

# Logic: Only process if the audio is new to prevent infinite loops
if audio_file and audio_file != st.session_state.last_processed_audio:
    st.session_state.last_processed_audio = audio_file
    
    with st.spinner("Mentor is listening..."):
        # 1. Transcribe (Free Google Engine)
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            try:
                user_input = r.recognize_google(audio_data)
            except Exception:
                user_input = "I'm sorry, I couldn't hear clearly."

        # 2. Get AI Response from GitHub Models
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        try:
            response = client.chat.completions.create(
                messages=st.session_state.messages,
                model="gpt-4o",
                temperature=0.7
            )
            ai_response = response.choices[0].message.content
        except Exception as e:
            ai_response = "I encountered a connection error. Let's try again."

        st.session_state.messages.append({"role": "assistant", "content": ai_response})

        # 3. Generate Male Indian Speech
        # We use asyncio.run because edge-tts is an asynchronous library
        asyncio.run(generate_voice(ai_response))
        
        # 4. Refresh to show new messages
        st.rerun()

# --- AUDIO PLAYBACK ---
# This remains outside the processing block to avoid being cut off by the rerun
if len(st.session_state.messages) > 1 and st.session_state.messages[-1]["role"] == "assistant":
    if os.path.exists("response.mp3"):
        st.audio("response.mp3", format="audio/mp3", autoplay=False)