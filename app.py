import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from openai import OpenAI
import yt_dlp
import requests
import tempfile
import re
import time
import random

load_dotenv()
client = OpenAI()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Summora.AI", page_icon="✨", layout="centered")

# ---------------- HEADER ----------------
st.markdown("""
<h1 style='text-align:center; font-size:48px; font-weight:700; letter-spacing:2px;'>
<span style="color:#8B00FF;">S</span>
<span style="color:#4B0082;">u</span>
<span style="color:#0000FF;">m</span>
<span style="color:#00FF00;">m</span>
<span style="color:#FFFF00;">o</span>
<span style="color:#FF7F00;">r</span>
<span style="color:#FF0000;">a</span>
<span style="color:#94a3b8;">.</span>
<span style="color:#00FF00;">AI</span>
</h1>
<p style='text-align:center;color:#64748b; font-size:18px;'>
YouTube Video Summarize Agent
</p>
""", unsafe_allow_html=True)

st.divider()

# ---------------- LANGUAGE + MODE ----------------
output_language = st.selectbox(
    "Select Output Language",
    ["English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali"]
)

summary_mode = st.radio(
    "Select Summary Mode",
    ["Text Summary", "Audio Summary"]
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
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# ---------------- FUN FACTS ----------------
def show_fun_fact():
    facts = [
        "🤖 AI models process thousands of tokens per second.",
        "📊 Semantic chunking improves reasoning accuracy.",
        "🧠 Overlapping chunks reduce information loss.",
        "🌍 GPT models support over 100 languages.",
        "⚡ Extract-first summarization reduces hallucination.",
        "🎯 Grounded prompts prevent invented information.",
        "🔍 Structured extraction improves completeness.",
        "📈 Hierarchical summarization improves quality."
    ]
    return random.choice(facts)

# ---------------- TRANSCRIPT ----------------
def get_video_data(video_url):
    try:
        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            duration = info.get("duration", 0)
            if duration > 1800:
                return None, None, "Video too long. Use under 30 minutes."

            detected_language = info.get("language", None)

            subtitle_url = None

            if "subtitles" in info and info["subtitles"]:
                if "en" in info["subtitles"]:
                    subtitle_url = info["subtitles"]["en"][0]["url"]
                else:
                    first_lang = list(info["subtitles"].keys())[0]
                    subtitle_url = info["subtitles"][first_lang][0]["url"]

            elif "automatic_captions" in info and info["automatic_captions"]:
                if "en" in info["automatic_captions"]:
                    subtitle_url = info["automatic_captions"]["en"][0]["url"]
                else:
                    first_lang = list(info["automatic_captions"].keys())[0]
                    subtitle_url = info["automatic_captions"][first_lang][0]["url"]

            if not subtitle_url:
                return None, None, "No captions available."

        response = requests.get(subtitle_url)
        return response.text, detected_language, None

    except:
        return None, None, "Transcript extraction failed."

# ---------------- LANGUAGE FALLBACK ----------------
def detect_language_from_text(text):
    prompt = f"""
Detect the primary language of this text.
Respond with only the language name.

{text[:2000]}
"""
    response = llm.invoke(prompt)
    return response.content.strip()

# ---------------- CHUNKING ----------------
def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3500,
        chunk_overlap=600
    )
    return splitter.split_text(text)

# ---------------- AUDIO ----------------
def generate_audio(text):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
            speech = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text
            )
            tmpfile.write(speech.content)
            return tmpfile.name
    except:
        return None

# ---------------- PROMPTS ----------------
section_prompt = PromptTemplate.from_template("""
Extract ONLY factual information from this transcript section.

Identify:
- Main claims
- Key explanations
- Examples mentioned
- Any numbers/statistics

Rules:
- Do NOT generalize.
- Do NOT invent.
- Only extract explicit information.

{text}

Return structured bullet points.
""")

final_prompt = PromptTemplate.from_template("""
Using ONLY the extracted bullet points below, generate a structured report.

Rules:
- Do NOT invent.
- Do NOT generalize.
- If missing info, say "Not explicitly mentioned."

Provide:
1. Executive Summary
2. Key Insights
3. Actionable Takeaways

Write in {language}.

Extracted Content:
{combined_summary}
""")

# ---------------- INPUT ----------------
url = st.text_input("Paste YouTube URL")
generate = st.button("🚀 Generate Summary")

# ---------------- MAIN LOGIC ----------------
if generate:
    if not url:
        st.warning("Please enter a YouTube URL.")
    else:
        st.session_state.usage_count += 1

        progress_box = st.empty()
        fact_box = st.empty()
        progress_bar = st.progress(0)

        progress_box.info("🔍 Fetching transcript...")
        progress_bar.progress(10)
        fact_box.caption(show_fun_fact())
        time.sleep(1)

        transcript, detected_lang, error = get_video_data(url)

        if error:
            st.error(error)
        else:
            transcript = re.sub("<.*?>", "", transcript)
            transcript = transcript[:25000]

            if not detected_lang:
                detected_lang = detect_language_from_text(transcript)

            st.info(f"Detected Language: {detected_lang}")
            st.session_state["transcript"] = transcript

            progress_box.info("🧠 Analyzing transcript structure...")
            progress_bar.progress(30)
            fact_box.caption(show_fun_fact())
            time.sleep(1)

            chunks = split_text(transcript)
            section_extractions = []

            progress_box.info("📊 Extracting key insights...")
            progress_bar.progress(50)
            fact_box.caption(show_fun_fact())

            for i, chunk in enumerate(chunks):
                formatted = section_prompt.format(text=chunk)
                response = llm.invoke(formatted)
                section_extractions.append(response.content)

                chunk_progress = 50 + int((i + 1) / len(chunks) * 20)
                progress_bar.progress(chunk_progress)

            combined_extraction = "\n\n".join(section_extractions)

            progress_box.info("🧩 Synthesizing intelligence report...")
            progress_bar.progress(80)
            fact_box.caption(show_fun_fact())
            time.sleep(1)

            final_formatted = final_prompt.format(
                combined_summary=combined_extraction,
                language=output_language
            )
            final_response = llm.invoke(final_formatted)

            progress_bar.progress(95)

            if summary_mode == "Audio Summary":
                progress_box.info("🔊 Generating AI voice narration...")
                fact_box.caption("🎧 Converting summary into natural speech...")
                audio_file = generate_audio(final_response.content)
                progress_bar.progress(100)
                progress_box.success("✅ Audio Summary Ready")
                fact_box.empty()

                if audio_file:
                    st.audio(audio_file)
                else:
                    st.error("Audio generation failed.")
            else:
                progress_bar.progress(100)
                progress_box.success("✅ Summary Ready")
                fact_box.empty()
                st.markdown(final_response.content)

# ---------------- Q&A ----------------
st.divider()
st.markdown("## 💬 Ask Questions About This Video")

if "transcript" in st.session_state:
    question = st.text_input("Ask something about the video")

    if st.button("Ask Question"):
        if question:
            qa_prompt = f"""
Answer based ONLY on the transcript below.

Respond in {output_language}.
If not found, say "Not explicitly mentioned."

Transcript:
{st.session_state['transcript'][:18000]}

Question:
{question}
"""
            response = llm.invoke(qa_prompt)
            st.markdown("### 🤖 Answer")
            st.write(response.content)
