import streamlit as st
import speech_recognition as sr
import pyttsx3
from openai import OpenAI

# --- CONFIGURATION ---
st.set_page_config(page_title="TERRA-P", page_icon="🌱")
st.title("🌱 Therapeutic Enlightening Robust Retinue")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are an empathetic, patient Mentor. Respond in the language used by the user. Use plain text."}
    ]
if "stop_speaking" not in st.session_state:
    st.session_state.stop_speaking = False
if "last_spoken_index" not in st.session_state:
    st.session_state.last_spoken_index = 0

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=st.secrets.get("GITHUB_TOKEN")
)

# --- HELPER FUNCTIONS ---
def speak_text(text):
    if not isinstance(text, str) or not text or text.lower() == "none":
        return
    try:
        engine = pyttsx3.init()
        clean_text = " ".join(text.split())
        if not st.session_state.get("stop_speaking", False):
            engine.say(clean_text)
            engine.runAndWait()
    except:
        pass
    finally:
        st.session_state.stop_speaking = False

def listen_to_user():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.toast("Listening...", icon="👂")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=0.7)
            audio = recognizer.listen(source, timeout=7)
            return recognizer.recognize_google(audio)
        except:
            return None

# --- UI DISPLAY ---
for message in st.session_state.messages:
    if message["role"] != "system":
        avatar = "🤝" if message["role"] == "user" else "🌿"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# --- INTERACTION LOGIC (PUT THE FIX HERE) ---
col1, col2 = st.columns(2)

with col1:
    if st.button("🎤 Share your thoughts"):
        st.session_state.stop_speaking = False 
        user_input = listen_to_user()
        
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner("Thinking..."):
                try:
                    response = client.chat.completions.create(
                        messages=st.session_state.messages,
                        model="gpt-4o",
                        temperature=0.75
                    )
                    # FIX: Safely retrieve content
                    ai_response = response.choices[0].message.content
                    
                    # Double-check if the API actually sent text
                    if not ai_response:
                        ai_response = "I'm having trouble connecting right now. Let's try again in a moment."
                
                except Exception as e:
                    ai_response = f"I'm sorry. I need a moment to process what I've just heard.: {str(e)}. Let's pause for a second."

                st.session_state.messages.append({"role": "assistant", "content": str(ai_response)})
            st.rerun()

with col2:
    if st.button("🛑 Quiet the Space"):
        st.session_state.stop_speaking = True
        try:
            pyttsx3.init().stop()
        except:
            pass

# --- AUTO-PLAY ---
if len(st.session_state.messages) > 0:
    last_msg = st.session_state.messages[-1]
    if last_msg["role"] == "assistant" and len(st.session_state.messages) > st.session_state.last_spoken_index:
        if not st.session_state.stop_speaking:
            st.session_state.last_spoken_index = len(st.session_state.messages)
            speak_text(last_msg.get("content", ""))