!pip install gradio groq PyPDF2 gTTS --quiet

import gradio as gr
from groq import Groq
import PyPDF2
from gtts import gTTS

# -------------------------
# 1️⃣ إعداد Groq
# -------------------------
client = Groq(api_key="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")

# -------------------------
# 2️⃣ قراءة PDF كامل
# -------------------------
def get_pdf_text(file):
    if file is None: return ""
    try:
        reader = PyPDF2.PdfReader(file.name)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content: text += content + "\n"
        return text
    except:
        return ""

# -------------------------
# 3️⃣ اكتشاف لغة المستخدم
# -------------------------
def detect_language(text):
    arabic_chars = "اأإآءبتثجحخدذرزسشصضطظعغفقكلمنهوي"
    return "arabic" if any(c in arabic_chars for c in text) else "english"

# -------------------------
# 4️⃣ تلخيص PDF كامل
# -------------------------
def summarize_pdf(document):
    system_prompt = f"""
You are Khadija's Smart Reader.
Summarize the following text in a concise way in Arabic/Darija if the text contains Arabic, otherwise English.
Text:
{document[:8000]}
"""
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.2
        )
        return res.choices[0].message.content
    except:
        return "❌ Unable to summarize PDF"

# -------------------------
# 5️⃣ الدردشة مع PDF
# -------------------------
def chat_khadija(message, history, pdf_file, voice=False):
    if pdf_file is None:
        return history + [("⚠️", "خديجة، حطي PDF الأول")], None

    document = get_pdf_text(pdf_file)
    if not document:
        return history + [("❌", "ماقدرتش نقرا الملف")], None

    user_lang = detect_language(message)

    # context-relevant: نجيب الجمل اللي فيها كلمات السؤال
    lines = document.split("\n")
    question_words = set(message.lower().split())
    context_lines = [line for line in lines if set(line.lower().split()) & question_words]
    context = "\n".join(context_lines[:30]) or document[:1000]

    system_prompt = f"""
You are Khadija's Smart Reader.
Respond ONLY in the same language as the user: {user_lang}.
Use ONLY the context below.
Be concise, clear, and smart.
CONTEXT:
{context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    for u, a in history:
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": a})
    messages.append({"role": "user", "content": message})

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2
        )
        answer = res.choices[0].message.content

        audio_path = None
        if voice:
            tts = gTTS(text=answer, lang='ar' if user_lang=='arabic' else 'en')
            audio_path = "/content/res.mp3"
            tts.save(audio_path)

        history.append((message, answer))
        return history, audio_path
    except Exception as e:
        history.append((message, f"❌ Error: {str(e)}"))
        return history, None

# -------------------------
# 6️⃣ واجهة Gradio
# -------------------------
with gr.Blocks() as demo:
    gr.HTML("<h1 style='text-align:center;'>  Smarter Reader </h1>")

    with gr.Row():
        pdf_input = gr.File(label="📄 Upload PDF", file_types=[".pdf"])
        voice_opt = gr.Checkbox(label="🔊 تفعيل الصوت", value=False)

    chatbot = gr.Chatbot(height=450)
    audio_output = gr.Audio(type="filepath", interactive=False)

    with gr.Row():
        msg = gr.Textbox(placeholder="اسال عن الكتاب...")
        submit = gr.Button("إرسال")


    # وظيفة إرسال السؤال
    def user_msg(message, history):
        return "", history + [(message, None)]

    def bot_res(history, pdf, voice):
        user_message = history[-1][0]
        new_history, audio = chat_khadija(user_message, history[:-1], pdf, voice)
        return new_history, audio

    # وظيفة تلخيص كامل PDF
    def summarize(pdf):
        document = get_pdf_text(pdf)
        summary = summarize_pdf(document)
        return summary

    msg.submit(user_msg, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot_res, [chatbot, pdf_input, voice_opt], [chatbot, audio_output]
    )
    submit.click(user_msg, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot_res, [chatbot, pdf_input, voice_opt], [chatbot, audio_output]
    )
    summarize_btn.click(summarize, [pdf_input], [chatbot])

demo.launch(share=True)
