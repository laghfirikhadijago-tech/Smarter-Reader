import streamlit as st
from groq import Groq
import PyPDF2
from gtts import gTTS 
import uuid
import os

# 1. Page Configuration
st.set_page_config(page_title="Smarter Reader ", layout="wide") 

# 2. Memory Setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "full_text" not in st.session_state:
    st.session_state.full_text = ""

st.title(" Smarter Reader ")

# 3. Groq Connection
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY missing!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. English Sidebar
with st.sidebar:
    st.header("Settings")
    target_lang = st.selectbox("Response Language", ["English", "Arabic", "French"])
    st.divider()
    uploaded_file = st.file_uploader("Upload PDF Document", type="pdf")
    if uploaded_file:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        st.session_state.full_text = "\n".join([p.extract_text() for p in pdf_reader.pages if p.extract_text()])
        st.success("Document Ready!")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# --- التغيير الجذري هنا لضبط جودة الأجوبة ---
instructions = {
    "English": "You are a professional analyst. Summarize the answer from the text in your own words. Be concise and direct. Do not just copy-paste long chunks of text.",
    "Arabic": "أنت محلل مهني. لخص الإجابة من النص بأسلوبك الخاص. كن مختصراً ومباشراً ولا تنقل نصوصاً طويلة حرفياً.",
    "French": "Vous êtes un analyste professionnel. Résumez la réponse avec vos propres mots. Soyez concis et direct."
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
            with st.spinner("Analyzing..."):
                try:
                    # استعملنا نظام جديد للرسائل باش يفصل بين النص والتعليمات
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": instructions[target_lang]},
                            {"role": "user", "content": f"Based on this text: {st.session_state.full_text[:7000]}\n\nQuestion: {prompt}\n\nAnswer in a professional and summarized way:"}
                        ],
                        model="llama-3.1-8b-instant",
                        temperature=0.0, # باش يكون دقيق وميخرفش
                        max_tokens=300   # باش يضطر يختصر وميعطيكش جريدة
                    )
                    
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                    
                    # Voice Output
                    lang_map = {"English": "en", "Arabic": "ar", "French": "fr"}
                    audio_fn = f"v_{uuid.uuid4()}.mp3"
                    tts = gTTS(text=answer, lang=lang_map[target_lang])
                    tts.save(audio_fn)
                    st.audio(audio_fn)
                    os.remove(audio_fn)

                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.warning("Upload PDF first.")
