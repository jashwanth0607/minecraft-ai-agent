import streamlit as st
import json
from pathlib import Path
from groq import Groq

st.set_page_config(page_title="MineAgent", page_icon="⛏️", layout="wide")

try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("GROQ_API_KEY is not configured. Add it in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=api_key)

BASE_DIR = Path(__file__).resolve().parent
FARMS_FILE = BASE_DIR / "data" / "farms.json"

@st.cache_data
def get_farms():
    with open(FARMS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

farms = get_farms()

def search_farms(category="All", edition="All"):
    results = []
    for farm in farms:
        if category != "All" and category.lower() not in farm["category"].lower():
            continue
        if edition != "All" and edition.lower() not in farm["edition"].lower():
            continue
        results.append(farm)
    return results

def minecraft_agent(question, edition):
    relevant = search_farms(edition=edition)
    context = json.dumps(relevant, indent=2)

    prompt = f"""
You are MineAgent, a Minecraft farm-guide assistant.

Player edition: {edition}

Use ONLY the supplied knowledge base for farm-specific materials,
steps, rates, versions, and compatibility.

KNOWLEDGE BASE:
{context}

USER QUESTION:
{question}

Instructions:
- Give a detailed, beginner-friendly answer.
- If asked how to build a farm, provide numbered steps from the database.
- Include materials and quantities when available.
- Include edition and compatible versions.
- Explain basic farm mechanics.
- Include troubleshooting when available.
- Include source links and tutorial-video links when relevant.
- Never invent missing quantities, rates, mechanics, or steps.
- If information is insufficient, say what is missing.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an accurate Minecraft technical guide assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content

def generate_forum_post(question, answer):
    prompt = f"""
Turn this MineAgent answer into an original Minecraft community forum post.

QUESTION:
{question}

ANSWER:
{answer}

Use Markdown with:
# Title
## Overview
## Edition & Version
## Difficulty & Build Time
## Materials
## Step-by-Step Build
## How It Works
## Troubleshooting
## Sources & Tutorial Videos

Do not add facts that are absent from the answer.
Keep source URLs as links.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You write clear original Minecraft community guides."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content

st.sidebar.title("⛏️ MineAgent")
st.sidebar.caption("Minecraft Farm Guide AI")

edition = st.sidebar.selectbox("Minecraft Edition", ["Java", "Bedrock"])
categories = ["All"] + sorted(set(f["category"] for f in farms))
category = st.sidebar.selectbox("Farm Category", categories)

st.title("⛏️ MineAgent")
st.subheader("Minecraft Farm Guide AI")
st.write("Ask for farm recommendations, materials, construction steps, mechanics, troubleshooting, sources, and tutorial videos.")

with st.expander("📚 Available farms"):
    for farm in search_farms(category, edition):
        st.write(f"**{farm['name']}** — {farm['edition']} — {farm['difficulty']}")

question = st.text_area(
    "Ask your Minecraft question",
    placeholder="Example: How do I build the beginner iron farm step by step?",
    height=130
)

if st.button("🤖 Ask MineAgent", use_container_width=True):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Researching the farm guide..."):
            answer = minecraft_agent(question, edition)
        st.session_state["question"] = question
        st.session_state["answer"] = answer
        st.session_state.pop("forum_post", None)

if "answer" in st.session_state:
    st.divider()
    st.markdown("## 🤖 MineAgent Answer")
    st.markdown(st.session_state["answer"])

    if st.button("📝 Generate Forum Post", use_container_width=True):
        with st.spinner("Creating forum post..."):
            st.session_state["forum_post"] = generate_forum_post(
                st.session_state["question"],
                st.session_state["answer"]
            )

    if "forum_post" in st.session_state:
        st.markdown("## 📝 Forum Post Preview")
        st.markdown(st.session_state["forum_post"])
        st.download_button(
            "⬇️ Download Forum Post",
            st.session_state["forum_post"],
            file_name="minecraft-forum-post.md",
            mime="text/markdown",
            use_container_width=True
        )
