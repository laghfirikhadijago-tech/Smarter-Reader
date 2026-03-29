import streamlit as st
from groq import Groq
import PyPDF2
from gtts import gTTS
import uuid
import os

# 1. Page Configuration (Professional Look)
st.set_page_config(page_title="Smarter Reader Pro", layout="wide")

# Custom CSS for a cleaner interface
st.markdown("""
    <style>
    .stChatFloatingInputContainer { background-color: rgba(255,255,255,0); }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "full_text" not in st.session_state:
    st.session_state.full_text = ""

st.title("📄 Smarter Reader Pro")
st.caption("AI-Powered Document Analysis & Conversation")

# 3. Connection with Groq
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY missing in secrets!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. Professional Sidebar (English Interface)
with st.sidebar:
    st.header("Settings")
    target_lang = st.selectbox("Response Language", ["Arabic", "French", "English"])
    
    st.divider()
    uploaded_file = st.file_uploader("Upload PDF Document", type="pdf")
    
    if uploaded_file:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text_data = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        st.session_state.full_text = text_data
        st.success("Document analyzed successfully!")
    
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# System Prompts (Neutral & Professional)
prompt_instructions = {
    "Arabic": "أنت مساعد مهني ومحايد. أجب بدقة وموضوعية باللغة العربية بناءً على النص فقط.",
    "French": "Vous êtes un assistant professionnel et neutre. Répondez objectivement en français en vous basant uniquement sur le texte.",
    "English": "You are a professional and neutral assistant. Provide objective responses in English based strictly on the provided text."
}

# 5. Chat Interface Display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Chat Input & Processing
if prompt := st.chat_input("Ask a professional question about the document..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.full_text:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing document..."):
                try:
                    # Optimized Request for Neutrality and Speed
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": f"{prompt_instructions[target_lang]} \n\nContext:\n{st.session_state.full_text[:12000]}"},
                        ] + st.session_state.messages[-3:], # Focus on the last 3 turns for context
                        model="llama-3.1-8b-instant",
                        temperature=0.1, # Lowest temperature for neutral, non-creative facts
                    )
                    
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                    
                    # Audio Response Generation
                    audio_lang = 'ar' if target_lang=="Arabic" else 'fr' if target_lang=="French" else 'en'
                    audio_path = f"res_{uuid.uuid4()}.mp3"
                    tts = gTTS(text=answer, lang=audio_path[:2] if audio_lang=='en' else audio_lang.lower()[:2])
                    # Fix for gTTS language codes
                    lang_code = {'Arabic': 'ar', 'French': 'fr', 'English': 'en'}[target_lang]
                    tts = gTTS(text=answer, lang=lang_code)
                    tts.save(audio_path)
                    st.audio(audio_path)
                    os.remove(audio_path)
                    
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.warning("Please upload a PDF document first.")
