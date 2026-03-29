import streamlit as st
from groq import Groq
import PyPDF2
from gtts import gTTS
import uuid
import os

# 1. إعدادات الصفحة والستايل
st.set_page_config(page_title="Smarter Reader", layout="centered")
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 20px; background-color: #4CAF50; color: white; }
    .stTextInput>div>div>input { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("📚 Smarter Reader")
st.subheader("مساعدك الذكي لقراءة وتحليل ملفات PDF")

# 2. الربط مع Groq Cloud
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY in Secrets!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. اختيار اللغة وتخصيص الواجهة
language = st.selectbox("اختر لغة التواصل / Choose Language", ["العربية", "Français", "English"])

if language == "العربية":
    labels = {"up": "📂 ارفع ملف PDF", "q": "ما هو سؤالك حول الملف؟", "sys": "أجب بدقة وباللغة العربية.", "wait": "جاري التفكير...", "res": "الإجابة:"}
    tts_lang = "ar"
elif language == "Français":
    labels = {"up": "📂 Charger le PDF", "q": "Quelle est votre question ?", "sys": "Réponدي en Français.", "wait": "Réflexion...", "res": "Réponse :"}
    tts_lang = "fr"
else:
    labels = {"up": "📂 Upload PDF", "q": "What is your question?", "sys": "Answer in English.", "wait": "Thinking...", "res": "Answer:"}
    tts_lang = "en"

# 4. معالجة الملف
uploaded_file = st.file_uploader(labels["up"], type="pdf")

if uploaded_file:
    # استخراج النص
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    full_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    
    st.success("✅ File Ready!")

    # 5. خانة السؤال (وضعناها هنا لتبقى ثابتة)
    user_question = st.text_input(labels["q"], placeholder="Enter your question here...", key="main_q")

    if user_question:
        with st.spinner(labels["wait"]):
            try:
                # طلب الإجابة من الموديل السريع
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": labels["sys"]},
                        {"role": "user", "content": f"Text: {full_text[:15000]}\n\nQuestion: {user_question}"}
                    ],
                    model="llama-3.1-8b-instant",
                )
                
                answer = response.choices[0].message.content
                st.markdown(f"### {labels['res']}")
                st.info(answer)

                # 6. تحويل الإجابة لصوت
                audio_file = f"speech_{uuid.uuid4()}.mp3"
                tts = gTTS(text=answer, lang=tts_lang)
                tts.save(audio_file)
                st.audio(audio_file)
                os.remove(audio_file)

            except Exception as e:
                st.error(f"Error: {e}")

st.divider()
st.caption("Developed with Khadija")
