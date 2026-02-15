import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import yt_dlp
import requests
import os
import re

load_dotenv()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Summora.AI", page_icon="✨", layout="centered")

# ---------------- PREMIUM HEADER ----------------
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
<span style="color:#111827;">AI</span>
</h1>
<p style='text-align:center;color:#64748b; font-size:18px;'>
Advanced YouTube Video Summarize Agent
</p>
""", unsafe_allow_html=True)

st.divider()

# ---------------- USAGE LIMIT ----------------
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0

MAX_DAILY_LIMIT = 5

if st.session_state.usage_count >= MAX_DAILY_LIMIT:
    st.error("🚫 Daily free limit reached. Please try again tomorrow.")
    st.stop()

st.caption(f"Free usage left: {MAX_DAILY_LIMIT - st.session_state.usage_count}")

# ---------------- TRANSCRIPT FUNCTION ----------------
def get_transcript(video_url):
    try:
        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            if "subtitles" in info and "en" in info["subtitles"]:
                subtitle_url = info["subtitles"]["en"][0]["url"]
            elif "automatic_captions" in info and "en" in info["automatic_captions"]:
                subtitle_url = info["automatic_captions"]["en"][0]["url"]
            else:
                return None

        response = requests.get(subtitle_url)
        return response.text

    except:
        return None

# ---------------- TEXT SPLITTER ----------------
def split_text(text, chunk_size=4000):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks

# ---------------- LLM ----------------
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3
)

# ---------------- PROMPTS ----------------
section_prompt = PromptTemplate.from_template("""
Summarize this section of a YouTube transcript clearly.

Text:
{text}

Return concise bullet insights.
""")

final_prompt = PromptTemplate.from_template("""
You are an expert content analyst.

Based on the combined summaries below, generate:

1. 🔹 Executive Summary
2. 🔹 Key Insights (bullet points)
3. 🔹 Actionable Steps
4. 🔹 LinkedIn Post Version

Content:
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

        with st.spinner("Fetching transcript..."):
            transcript = get_transcript(url)

        if not transcript:
            st.error("Transcript not available for this video.")
        else:
            transcript = re.sub("<.*?>", "", transcript)
            transcript = transcript[:20000]  # cost control

            chunks = split_text(transcript)

            section_summaries = []

            with st.spinner("Analyzing video sections..."):
                for chunk in chunks:
                    formatted = section_prompt.format(text=chunk)
                    response = llm.invoke(formatted)
                    section_summaries.append(response.content)

            combined_summary = "\n\n".join(section_summaries)

            with st.spinner("Generating final intelligence report..."):
                final_formatted = final_prompt.format(combined_summary=combined_summary)
                final_response = llm.invoke(final_formatted)

            st.success("✨ Summary Generated Successfully")
            st.markdown(final_response.content)