import streamlit as st
import uuid
from llm_handler import ask_phi
from file_reader import read_file
from prompt_router import route_prompt
import re

def clean_text(text):
    # remove multiple dots
    text = re.sub(r"\.{2,}", " ", text)

    # fix merged words like DataEngineering
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    # fix common OCR patterns
    text = text.replace("S.Q.L", "SQL")
    text = text.replace("S Q L", "SQL")

    return text.strip()


# -------- PAGE CONFIG --------

st.set_page_config(page_title="Cover Letter Generator", layout="wide")
st.title("AI Assistant")


# -------- SESSION STATE INIT --------

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_chat_id" not in st.session_state:
    chat_id = str(uuid.uuid4())
    st.session_state.current_chat_id = chat_id
    st.session_state.conversations[chat_id] = {
        "title": "New Chat",
        "messages": [],
        "user_name": "",
        "company_name": "",
        "role_name": "",
        "job_description": ""
    }

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""


# -------- SIDEBAR --------

with st.sidebar:
    st.header("Chats")

    if st.button("➕ New Chat"):
        chat_id = str(uuid.uuid4())
        st.session_state.current_chat_id = chat_id
        st.session_state.conversations[chat_id] = {
            "title": "New Chat",
            "messages": [],
            "user_name": "",
            "company_name": "",
            "role_name": "",
            "job_description": ""
        }
        st.rerun()

    st.divider()

    for cid, chat_data in st.session_state.conversations.items():
        if st.button(chat_data["title"], key=f"chat_{cid}"):
            st.session_state.current_chat_id = cid
            st.rerun()


# -------- LOAD CURRENT CHAT --------

current_chat_id = st.session_state.current_chat_id
current_chat = st.session_state.conversations[current_chat_id]
messages = current_chat["messages"]


# -------- JOB DETAILS --------

st.subheader("Job Details")

col1, col2 = st.columns(2)

with col1:
    current_chat["user_name"] = st.text_input(
        "Your Name",
        value=current_chat["user_name"],
        key=f"user_name_{current_chat_id}"
    )

    current_chat["role_name"] = st.text_input(
        "Role Name",
        value=current_chat["role_name"],
        key=f"role_name_{current_chat_id}"
    )

with col2:
    current_chat["company_name"] = st.text_input(
        "Company Name",
        value=current_chat["company_name"],
        key=f"company_name_{current_chat_id}"
    )



st.divider()

# -------- JD & RESUME SIDE BY SIDE --------

col_left, col_right = st.columns(2)

# -------- LEFT: JOB DESCRIPTION --------
with col_left:
    st.subheader("Job Description")

    jd_file = st.file_uploader(
        "Upload Job Description",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        key=f"jd_upload_{current_chat_id}"
    )

    if jd_file:
        extracted_jd = read_file(jd_file)
        cleaned_jd = clean_text(extracted_jd)
        current_chat["job_description"] = cleaned_jd
        st.success("Job Description loaded successfully")

        with st.expander("🔍 View Extracted JD Text"):
            current_chat["job_description"] = st.text_area(
                "Extracted JD (Editable)",
                value=current_chat["job_description"],
                height=200
            )

   
        


# -------- RIGHT: RESUME --------
with col_right:
    st.subheader("Resume")

    resume_file = st.file_uploader(
        "Upload your Resume",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        key=f"resume_upload_{current_chat_id}"
    )

    if resume_file:
        raw_text = read_file(resume_file)
        cleaned_text = clean_text(raw_text)
        st.session_state.resume_text = cleaned_text
        st.success("Resume loaded successfully")

        with st.expander("🔍 View Extracted Resume Text"):
            st.session_state.resume_text = st.text_area(
                "Extracted Resume (Editable)",
                value=st.session_state.resume_text,
                height=200
            )






# -------- DISPLAY CHAT --------

for i, message in enumerate(messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])

        # Download only for assistant messages
        if message["role"] == "assistant":
            st.download_button(
                "⬇ Download",
                data=message["content"],
                file_name="cover_letter.txt",
                mime="text/plain",
                key=f"download_{current_chat_id}_{i}"
            )


# -------- CHAT INPUT --------

if prompt := st.chat_input("Ask me anything..."):

    messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    # Auto title first message
    if current_chat["title"] == "New Chat" and len(messages) == 1:
        try:
            title_response = ask_phi([
                {"role": "user", "content": f"Create a short 3-word title for: {prompt}"}
            ])
            current_chat["title"] = title_response.strip().split("\n")[0]
        except:
            current_chat["title"] = "Chat"

    final_prompt = route_prompt(
        prompt,
        st.session_state.resume_text,
        current_chat["user_name"],
        current_chat["company_name"],
        current_chat["role_name"],
        current_chat["job_description"]
    )

    try:
        with st.spinner("Thinking..."):
            response = ask_phi(
                messages[:-1] + [{"role": "user", "content": final_prompt}]
            )
    except Exception as e:
        response = f"Error: {e}"

    messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.write(response)

        st.download_button(
            "⬇ Download",
            data=response,
            file_name="cover_letter.txt",
            mime="text/plain",
            key=f"download_new_{current_chat_id}_{len(messages)}"
        )
