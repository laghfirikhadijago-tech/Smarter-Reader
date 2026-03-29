import streamlit as st
from groq import Groq
import PyPDF2
from gtts import gTTS
import os

# إعداد المحرك (API Key)
client = Groq(api_key="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")

# إعدادات الصفحة الاحترافية
st.set_page_config(page_title="Khadija Smart Reader PRO", layout="wide", page_icon="🚀")

# تصميم الواجهة
st.title("🚀 Khadija's Smart Reader PRO")
st.markdown("---")

# القائمة الجانبية لإدارة الملفات
with st.sidebar:
    st.header("📂 إدارة المستندات")
    pdf_file = st.file_uploader("قم بتحميل ملف PDF", type="pdf")
    st.markdown("---")
    voice_on = st.checkbox("تفعيل النطق الصوتي 🔊")

# ذاكرة المحادثة
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض المحادثة
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# منطقة التفاعل
if prompt := st.chat_input("اسأل أي شيء حول المستند..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if pdf_file:
        # معالجة الملف
        reader = PyPDF2.PdfReader(pdf_file)
        context = ""
        for page in reader.pages[:15]:
            context += page.extract_text() + "\n"
        
        # طلب الإجابة من الذكاء الاصطناعي
        with st.spinner("جاري التحليل..."):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"You are Khadija's Smart Reader PRO. Use this context: {context[:6000]}. Answer in the user's language."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            answer = response.choices[0].message.content
            
            with st.chat_message("assistant"):
                st.markdown(answer)
                if voice_on:
                    tts = gTTS(text=answer, lang='ar' if "ا" in answer else 'en')
                    tts.save("response.mp3")
                    st.audio("response.mp3")
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
    else:
        st.warning("الرجاء تحميل ملف PDF للبدء في التحليل.")