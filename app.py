import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path
from pypdf import PdfReader
from google import genai

st.set_page_config(
    page_title="AI Review Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI-Powered Review Feedback Chatbot")
st.write(
    "Automate task reviews, document analysis, "
    "feedback generation and internship review tracking."
)

DATA_FILE = Path("reviews.csv")

if DATA_FILE.exists():
    records = pd.read_csv(DATA_FILE)
else:
    records = pd.DataFrame(columns=[
        "Candidate",
        "Task",
        "Assigned Date",
        "Submission Date",
        "First Review Date",
        "AI Model",
        "Mistakes",
        "Feedback",
        "Next Review Date",
        "Status"
    ])

st.sidebar.header("⚙️ AI Settings")

api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    help="Enter your Gemini API key to enable real AI analysis."
)

st.sidebar.caption(
    "Your API key is used for this session and is not saved "
    "in the review records."
)

tab1, tab2, tab3 = st.tabs([
    "Task Assignment",
    "Document Review Chatbot",
    "Weekly Review Tracker"
])

with tab1:
    st.header("1. Candidate Task Assignment")

    with st.form("task_form"):
        candidate = st.text_input("Candidate Name")
        task = st.text_input("Assigned Task")

        assigned_date = st.date_input(
            "Task Assigned Date",
            value=date.today()
        )

        submission_date = st.date_input(
            "Task Submission Date",
            value=date.today()
        )

        first_review_date = st.date_input(
            "First Review Date",
            value=date.today()
        )

        ai_model = st.selectbox(
            "AI Model",
            ["Gemini"]
        )

        submitted = st.form_submit_button("Assign Task")

        if submitted:
            if not candidate.strip() or not task.strip():
                st.error("Please enter candidate name and task.")

            else:
                next_review = first_review_date + timedelta(days=7)

                new_record = {
                    "Candidate": candidate,
                    "Task": task,
                    "Assigned Date": str(assigned_date),
                    "Submission Date": str(submission_date),
                    "First Review Date": str(first_review_date),
                    "AI Model": ai_model,
                    "Mistakes": "Pending review",
                    "Feedback": "Pending review",
                    "Next Review Date": str(next_review),
                    "Status": "Pending"
                }

                records = pd.concat(
                    [records, pd.DataFrame([new_record])],
                    ignore_index=True
                )

                records.to_csv(DATA_FILE, index=False)

                st.success("Task assigned successfully!")
                st.rerun()


with tab2:
    st.header("2. Document Review Chatbot")

    st.write(
        "Upload a candidate's task document and ask the chatbot "
        "to review it."
    )

    uploaded_file = st.file_uploader(
        "Upload a task document (PDF or TXT)",
        type=["pdf", "txt"]
    )

    document_text = ""

    if uploaded_file is not None:
        try:
            if uploaded_file.name.lower().endswith(".pdf"):
                pdf = PdfReader(uploaded_file)

                document_text = "\n".join(
                    page.extract_text() or ""
                    for page in pdf.pages
                )
            else:
                document_text = uploaded_file.getvalue().decode(
                    "utf-8",
                    errors="ignore"
                )

            if document_text.strip():
                st.success("Document uploaded successfully!")
                st.write("Document:", uploaded_file.name)
            else:
                st.warning(
                    "No readable text found. The PDF may contain "
                    "scanned images instead of selectable text."
                )

        except Exception as error:
            st.error(f"Could not read the document: {error}")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input(
        "Ask about mistakes, feedback or improvements..."
    )

    if user_question:
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):
            st.markdown(user_question)

        if not api_key:
            answer = (
                "Please enter your Gemini API key in the sidebar "
                "to enable AI-powered document review. "
                "After entering the key, ask your question again."
            )

        elif not document_text.strip():
            answer = (
                "Please upload a readable PDF or TXT task document "
                "before asking me to review it."
            )

        else:
            try:
                client = genai.Client(api_key=api_key)

                prompt = f"""
You are an AI task-review assistant helping evaluate
a candidate's submitted work.

Review the document carefully and answer the candidate's question.

Identify:
1. Mistakes or missing information.
2. Areas that need improvement.
3. Clear, constructive feedback.
4. Recommended next steps.
5. Suggested date for the next review, if relevant.

Be honest. Do not invent mistakes or claim to have tested code
unless you actually have enough information to verify it.

DOCUMENT CONTENT:
{document_text[:25000]}

USER QUESTION:
{user_question}
"""

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )

                answer = response.text or (
                    "The AI did not return a text response. "
                    "Please try again."
                )

            except Exception as error:
                answer = (
                    "AI request failed. Please check your API key, "
                    "internet connection and model availability.\n\n"
                    f"Error details: {error}"
                )

        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer
        })

    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()


with tab3:
    st.header("3. Weekly Review Tracker")

    if not records.empty:
        st.dataframe(records, use_container_width=True)

        csv_data = records.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Review Records",
            data=csv_data,
            file_name="review_records.csv",
            mime="text/csv"
        )

    else:
        st.info("No review records available yet.")

st.divider()

st.caption(
    "AI Review Assistant | Task assignment, document analysis, "
    "feedback and weekly review tracking"
)