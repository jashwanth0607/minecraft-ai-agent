import streamlit as st
import json
import os
from groq import Groq

st.set_page_config(
    page_title="MineAgent",
    page_icon="⛏️",
    layout="wide"
)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("GROQ_API_KEY is not configured.")
    st.stop()

client = Groq(api_key=api_key)

@st.cache_data
def get_farms():
    with open("data/farms.json", "r") as f:
        return json.load(f)

farms = get_farms()

def search_farms(category=None, edition=None):
    results = []

    for farm in farms:
        if category and category != "All":
            if category.lower() not in farm["category"].lower():
                continue

        if edition and edition != "All":
            if farm["edition"].lower() != edition.lower():
                continue

        results.append(farm)

    return results

def minecraft_agent(question, edition):
    relevant_farms = search_farms(edition=edition)
    farm_information = json.dumps(relevant_farms, indent=2)

    prompt = f"""
You are MineAgent, an AI assistant for a Minecraft farm community.

The user plays Minecraft {edition}.

Your job is to help users with:
- Minecraft farms
- Farm recommendations
- Materials
- Difficulty
- Build time
- Minecraft versions
- Farm rates
- Troubleshooting

Use the supplied database when providing specific farm information.

Farm database:
{farm_information}

User question:
{question}

Rules:
1. Do not invent farm specifications.
2. Do not invent materials or rates.
3. If the database does not contain the requested information, clearly say that the information is not currently available.
4. Keep the response easy to understand.
5. Mention the Minecraft edition when relevant.
6. Give structured answers using headings and bullet points when useful.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are MineAgent, a helpful and accurate Minecraft farm assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content

def generate_forum_post(question, answer):
    prompt = f"""
Create a Minecraft community forum post based on the following user question and AI answer.

User question:
{question}

AI answer:
{answer}

Create a useful Markdown forum post.

Include:
# Title
## Overview
## Minecraft Edition
## Difficulty
## Required Materials
## Build Information
## Notes

Do not invent information that isn't present in the answer.

Return only the Markdown forum post.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You create clear Minecraft community guides."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content

st.sidebar.title("⛏️ MineAgent")
st.sidebar.write("AI-powered Minecraft farm assistant")

edition = st.sidebar.selectbox(
    "Minecraft Edition",
    ["Java", "Bedrock"]
)

category = st.sidebar.selectbox(
    "Farm Category",
    [
        "All",
        "Iron Farm",
        "Mob Farm",
        "Crop Farm",
        "XP Farm",
        "Gold Farm"
    ]
)

st.title("⛏️ MineAgent")
st.subheader("Minecraft Farm AI Assistant")

st.write(
    "Ask questions about Minecraft farms, materials, difficulty, versions and more."
)

question = st.text_area(
    "Ask your Minecraft question",
    placeholder="Example: I need an easy iron farm for Minecraft Java",
    height=120
)

if st.button("🤖 Ask MineAgent", use_container_width=True):
    if not question.strip():
        st.warning("Please enter a Minecraft question.")
    else:
        with st.spinner("MineAgent is thinking..."):
            answer = minecraft_agent(question, edition)

        st.session_state["question"] = question
        st.session_state["answer"] = answer

        st.markdown("## 🤖 MineAgent Response")
        st.markdown(answer)

if "answer" in st.session_state:
    st.divider()
    st.subheader("📝 Forum Post Generator")

    if st.button("Generate Forum Post", use_container_width=True):
        with st.spinner("Creating forum post..."):
            forum_post = generate_forum_post(
                st.session_state["question"],
                st.session_state["answer"]
            )

        st.session_state["forum_post"] = forum_post

    if "forum_post" in st.session_state:
        st.markdown("### 📄 Generated Forum Post")
        st.markdown(st.session_state["forum_post"])

        st.download_button(
            label="⬇️ Download Forum Post",
            data=st.session_state["forum_post"],
            file_name="minecraft-forum-post.md",
            mime="text/markdown",
            use_container_width=True
        )
