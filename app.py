import streamlit as st
from groq import Groq
import PyPDF2
from gtts import gTTS
import uuid
import os

# 1. Page Configuration
st.set_page_config(page_title="Smarter Reader Pro", layout="wide")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #ddd; }
    .stChatFloatingInputContainer { background-color: transparent; }
    </style>
    """, unsafe_allow_html=True)

# 2. Memory Setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "full_text" not in st.session_state:
    st.session_state.full_text = ""

st.title("📄 Smarter Reader Pro")

# 3. Groq Connection
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY missing!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. English Professional Sidebar
with st.sidebar:
    st.header("Settings")
    target_lang = st.selectbox("Response Language", ["English", "Arabic", "French"])
    
    st.divider()
    uploaded_file = st.file_uploader("Upload PDF Document", type="pdf")
    
    if uploaded_file:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text_data = ""
        for page in pdf_reader.pages:
            text_data += page.extract_text() + "\n"
        st.session_state.full_text = text_data
        st.success("Document analyzed successfully.")
    
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# Professional Instructions (Neutral & Focused)
instructions = {
    "English": "You are a professional assistant. Answer the question DIRECTLY and objectively based on the text. Do not quote long paragraphs unless asked.",
    "Arabic": "أنت مساعد مهني ومحايد. أجب على السؤال بشكل مباشر وموضوعي بناءً على النص. تجنب الاقتباسات الطويلة جداً.",
    "French": "Vous êtes un assistant professionnel. Répondez directement et objectivement selon le texte fourni."
}

# 5. Chat Display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Chat Logic
if prompt := st.chat_input("Ask a professional question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.full_text:
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    # Optimized Prompt to stop "messy" answers
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": f"{instructions[target_lang]} \n\nUSE THIS TEXT TO ANSWER:\n{st.session_state.full_text[:8000]}"},
                        ] + st.session_state.messages[-3:],
                        model="llama-3.1-8b-instant",
                        temperature=0.0, # 0.0 means ZERO creativity, only facts.
                    )
                    
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                    
                    # Voice Output
                    lang_map = {"English": "en", "Arabic": "ar", "French": "fr"}
                    audio_filename = f"audio_{uuid.uuid4()}.mp3"
                    tts = gTTS(text=answer, lang=lang_map[target_lang])
                    tts.save(audio_filename)
                    st.audio(audio_filename)
                    os.remove(audio_filename)

                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.warning("Please upload a PDF file.")
