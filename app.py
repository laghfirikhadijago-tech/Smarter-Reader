import streamlit as st
from groq import Groq
import PyPDF2
from gtts import gTTS
import uuid
import os

# 1. Page Configuration
st.set_page_config(page_title="Smarter Reader Pro", layout="wide")

# Professional Styles
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "full_text" not in st.session_state:
    st.session_state.full_text = ""

st.title("📄 Smarter Reader Pro")

# 3. Connection with Groq
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY missing in secrets!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. Sidebar Settings
with st.sidebar:
    st.header("Settings")
    # تأكدي أن الأسماء مطابقة للكود التحت
    target_lang = st.selectbox("Response Language", ["Arabic", "French", "English"])
    
    st.divider()
    uploaded_file = st.file_uploader("Upload PDF Document", type="pdf")
    
    if uploaded_file:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text_data = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        st.session_state.full_text = text_data
        st.success("Document analyzed!")
    
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# Professional Instructions
instructions = {
    "Arabic": "أنت مساعد مهني ومحايد. أجب بدقة وموضوعية باللغة العربية بناءً على النص.",
    "French": "Vous êtes un assistant professionnel. Répondez objectivement en français.",
    "English": "You are a professional assistant. Provide objective responses in English."
}

# 5. Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Chat Input & Processing
if prompt := st.chat_input("Ask a professional question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.full_text:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    # AI Request
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": f"{instructions[target_lang]} \n\nContext:\n{st.session_state.full_text[:12000]}"},
                        ] + st.session_state.messages[-3:],
                        model="llama-3.1-8b-instant",
                        temperature=0.1,
                    )
                    
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                    
                    # --- تصحيح مشكل الصوت هنا ---
                    # تحويل اسم اللغة لكود مفهوم (ar, fr, en)
                    lang_codes = {"Arabic": "ar", "French": "fr", "English": "en"}
                    current_code = lang_codes[target_lang]
                    
                    audio_filename = f"voice_{uuid.uuid4()}.mp3"
                    tts = gTTS(text=answer, lang=current_code)
                    tts.save(audio_filename)
                    st.audio(audio_filename)
                    os.remove(audio_filename)
                    # ---------------------------

                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.warning("Please upload a PDF first.")
