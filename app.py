import streamlit as st
from groq import Groq
import PyPDF2
from gtts import gTTS
import uuid
import os

# 1. إعدادات الصفحة
st.set_page_config(page_title="Smarter Reader Chat", layout="wide")

# 2. تهيئة الذاكرة (Chat History)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "full_text" not in st.session_state:
    st.session_state.full_text = ""

st.title("💬 Smarter Reader Chat")
st.subheader("تحدث مع ملف الـ PDF الخاص بك")

# 3. الربط مع Groq
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. رفع الملف (في الجنب - Sidebar)
with st.sidebar:
    st.header("⚙️ الإعدادات")
    language = st.selectbox("اللغة / Language", ["العربية", "Français", "English"])
    uploaded_file = st.file_uploader("ارفع ملف PDF", type="pdf")
    
    if uploaded_file:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        st.session_state.full_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        st.success("✅ تم تحميل الملف!")
    
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = []
        st.rerun()

# إعداد لغة النظام
prompts = {
    "العربية": "أنت مساعد ذكي. أجب بناءً على النص المقدم وباللغة العربية.",
    "Français": "Tu es un assistant intelligent. Réponds en français basé sur le texte.",
    "English": "You are a smart assistant. Answer in English based on the text."
}

# 5. عرض المحادثة السابقة
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. منطقة السؤال (Chat Input)
if prompt := st.chat_input("اسأل أي شيء عن الملف..."):
    # إضافة سؤال المستخدم للذاكرة
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # توليد الإجابة
    if st.session_state.full_text:
        with st.chat_message("assistant"):
            with st.spinner("جاري الكتابة..."):
                try:
                    # إرسال المحادثة كاملة لـ Groq ليعرف سياق الكلام
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": prompts[language]},
                            {"role": "user", "content": f"النص المرجعي: {st.session_state.full_text[:10000]}"}
                        ] + st.session_state.messages,
                        model="llama-3.1-8b-instant",
                    )
                    
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                    
                    # تحويل الإجابة لصوت (اختياري لآخر إجابة)
                    tts = gTTS(text=answer, lang=('ar' if language=="العربية" else 'fr' if language=="Français" else 'en'))
                    audio_path = f"speech_{uuid.uuid4()}.mp3"
                    tts.save(audio_path)
                    st.audio(audio_path)
                    os.remove(audio_path)
                    
                    # إضافة إجابة الذكاء الاصطناعي للذاكرة
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"خطأ: {e}")
    else:
        st.warning("المرجو رفع ملف PDF أولاً!")
