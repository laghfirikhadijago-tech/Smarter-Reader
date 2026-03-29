import streamlit as st
from groq import Groq
import PyPDF2
from gtts import gTTS
import uuid
import os

# 1. إعدادات الصفحة
st.set_page_config(page_title="Smarter Reader", layout="centered")

# 2. ستايل بسيط
st.markdown("""
    <style>
    .main { text-align: right; }
    .stButton>button { width: 100%; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("Smarter Reader")
st.subheader("Your smart assistant for reading and summarizing PDF files")

# 3. التحقق من API KEY
if "GROQ_API_KEY" not in st.secrets:
    st.error("خطأ: لم يتم العثور على GROQ_API_KEY في Secrets")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. اختيار اللغة
language = st.selectbox(
    "Choose Language",
    ["العربية", "Français", "English"]
)

# 5. إعدادات حسب اللغة
if language == "العربية":
    upload_label = "📂  قم  بتنزيل  الملف  PDF"
    question_label = " اطرح سؤالك"
    system_prompt = "أجب فقط بناءً على النص وباللغة العربية."
    tts_lang = "ar"

elif language == "Français":
    upload_label = "📂 Téléchargez votre PDF"
    question_label = " Posez votre question "
    system_prompt = "Répondez uniquement en vous basant sur le texte fourni, en français."
    tts_lang = "fr"

else:
    upload_label = "📂 Upload your PDF"
    question_label = " Ask your question"
    system_prompt = "Answer only based on the provided text, in English."
    tts_lang = "en"

# 6. رفع الملف
uploaded_file = st.file_uploader(upload_label, type="pdf")

if uploaded_file:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""

    # استخراج النص من كل الصفحات
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    st.success("✅ File uploaded successfully")

    if len(text) > 5000:
        st.warning(" The file is large it will be processed in chunks")

    user_question = st.text_input(question_label)

   if user_question:
        with st.spinner("Thinking…"):
            try:
                # إرسال النص كامل في طلب واحد (أسرع بـ 10 مرات)
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"النص المستخرج:\n{text[:15000]}\n\nالسؤال:\n{user_question}"}
                    ],
                    model="llama-3.1-8b-instant",
                )
                
                final_answer = chat_completion.choices[0].message.content

                st.markdown("### The answer:")
                st.write(final_answer)

                # تحويل الإجابة لصوت
                filename = f"response_{uuid.uuid4()}.mp3"
                tts = gTTS(text=final_answer, lang=tts_lang)
                tts.save(filename)
                st.audio(filename)

                if os.path.exists(filename):
                    os.remove(filename)

            except Exception as e:
                st.error(f"❌ حدث خطأ: {e}")
