import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from openai import OpenAI
import yt_dlp
import tempfile
import re
import time
import random
import os

load_dotenv()

client = OpenAI()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Summora.AI", page_icon="✨", layout="centered")

# ---------------- FUTURISTIC UI ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600&display=swap');

.title {
    text-align:center;
    font-family:'Orbitron', sans-serif;
    font-size:56px;
    background: linear-gradient(90deg,#00f5ff,#7c3aed,#00f5ff);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}
.subtitle {
    text-align:center;
    color:#9ca3af;
    margin-bottom:30px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Summora.AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-Powered YouTube Video Summaries</div>', unsafe_allow_html=True)

st.divider()

# ---------------- SETTINGS ----------------
output_language = st.selectbox(
    "Select Output Language",
    ["English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali"]
)

summary_mode = st.radio("Output Mode", ["Text Summary", "Audio Summary"])

professional_mode = st.selectbox(
    "Select Output Format",
    [
        "Executive Report",
        "Deep Analysis",
        "YouTube Script",
        "LinkedIn Post",
        "Twitter Thread",
        "Blog Draft"
    ]
)

# ---------------- USAGE LIMIT ----------------
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0

MAX_LIMIT = 5

if st.session_state.usage_count >= MAX_LIMIT:
    st.error("🚫 Daily free limit reached.")
    st.stop()

st.caption(f"Free usage left: {MAX_LIMIT - st.session_state.usage_count}")

# ---------------- LLM ----------------
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.2)

# ---------------- FUN FACT ----------------
def show_fun_fact():
    facts = [
        "🤖 AI models process thousands of tokens per second.",
        "🧠 Whisper can transcribe multiple languages accurately.",
        "📊 Structured extraction reduces hallucination.",
        "⚡ Chunking improves large context reasoning."
    ]
    return random.choice(facts)

# ---------------- DOWNLOAD AUDIO ----------------
def download_audio(video_url):
    try:
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "audio.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Find downloaded file
        for file in os.listdir(temp_dir):
            return os.path.join(temp_dir, file)

    except:
        return None

# ---------------- WHISPER TRANSCRIPTION ----------------
def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

# ---------------- CHUNKING ----------------
def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3500,
        chunk_overlap=500
    )
    return splitter.split_text(text)

# ---------------- PROFESSIONAL PROMPT ----------------
def generate_output(content, language, mode):

    if mode == "Executive Report":
        instruction = """
Provide:
1. Executive Summary
2. Key Insights
3. Actionable Takeaways
"""

    elif mode == "Deep Analysis":
        instruction = """
Provide:
1. Executive Summary
2. Detailed Breakdown
3. Strategic Implications
4. Risks
5. Action Plan
"""

    elif mode == "YouTube Script":
        instruction = """
Convert into engaging YouTube narration.
No headings.
Conversational style.
"""

    elif mode == "LinkedIn Post":
        instruction = """
Create high-value LinkedIn post.
Strong hook.
Professional tone.
"""

    elif mode == "Twitter Thread":
        instruction = """
Convert into Twitter thread format (1/,2/,3/).
Short lines.
"""

    else:
        instruction = """
Write SEO-friendly blog draft with sections.
"""

    prompt = f"""
Using ONLY the content below.
Do NOT invent.

Write in {language}.

{instruction}

Content:
{content}
"""

    return llm.invoke(prompt).content

# ---------------- EMOTION ANALYSIS ----------------
def analyze_emotion(text):
    prompt = f"""
Detect tone:
serious, inspirational, urgent, analytical, calm, exciting.

Return single word.

{text}
"""
    return llm.invoke(prompt).content.lower()

# ---------------- VOICE SELECTION ----------------
def select_voice(tone):
    if "inspirational" in tone:
        return "aria"
    elif "serious" in tone:
        return "verse"
    elif "exciting" in tone:
        return "aria"
    else:
        return "alloy"

# ---------------- INPUT ----------------
url = st.text_input("Paste YouTube URL")
generate = st.button("🚀 Generate Summary")

# ---------------- MAIN LOGIC ----------------
if generate:

    if not url:
        st.warning("Please enter URL.")
        st.stop()

    st.session_state.usage_count += 1

    progress = st.progress(0)
    status = st.empty()
    fact = st.empty()

    status.info("🎧 Downloading audio...")
    progress.progress(10)
    fact.caption(show_fun_fact())
    time.sleep(1)

    audio_file = download_audio(url)

    if not audio_file:
        st.error("Audio download failed.")
        st.stop()

    status.info("📝 Transcribing with Whisper...")
    progress.progress(30)

    transcript = transcribe_audio(audio_file)

    transcript = transcript[:30000]

    status.info("🧠 Analyzing transcript...")
    progress.progress(50)

    chunks = split_text(transcript)

    extracted = []
    for i, chunk in enumerate(chunks):
        result = llm.invoke(f"Extract key factual insights:\n{chunk}")
        extracted.append(result.content)
        progress.progress(50 + int((i+1)/len(chunks)*20))

    combined = "\n\n".join(extracted)

    status.info("📊 Generating professional output...")
    progress.progress(80)

    final_output = generate_output(
        combined,
        output_language,
        professional_mode
    )

    progress.progress(95)

    if summary_mode == "Text Summary":
        progress.progress(100)
        status.success("✅ Summary Report Ready")
        fact.empty()
        st.markdown(final_output)

        st.download_button(
            "📄 Download Summary",
            data=final_output,
            file_name="summora_output.txt"
        )

    else:
        status.info("🎙 Creating emotional narration...")
        tone = analyze_emotion(final_output)
        voice = select_voice(tone)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
            speech = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=final_output
            )
            tmpfile.write(speech.content)
            audio_path = tmpfile.name

        progress.progress(100)
        status.success("🎙 Emotion-Aware Audio Ready")
        fact.empty()
        st.audio(audio_path)

st.divider()
st.caption("© Summora.AI - Professional AI Video Intelligence")
