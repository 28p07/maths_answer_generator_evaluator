import requests
import streamlit as st
import streamlit.components.v1 as components
from typing import Optional
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup

class Input(BaseModel):
    question: str = Field(..., description="Question")
    reference_answer: str = Field(..., description="Reference answer")
    question_image_description: Optional[str] = None
    answer_image_description: Optional[str] = None
    student_answer: str = Field(..., description="Student answer")
    total_marks: int = Field(..., description="Total marks")
    question_type: str = Field(..., description="Question type")


EVALUATOR_API = "https://chat-backend-test.prepzy.ai/maths-answer-evaluator"
SAMPLE_API = "https://chat-backend-test.prepzy.ai/maths-sample-answer-generator"


st.set_page_config(page_title="CBSE Answer Evaluator", layout="centered")

st.title("📘 CBSE Answer Evaluator")

col1, col2 = st.columns([3, 1])

with col1:
    question = st.text_area(
        "Question",
        height=120,
        placeholder="Enter the question..."
    )

with col2:
    class_name = st.selectbox(
        "Class",
        options=("Class 6","Class 7","Class 8","Class 9", "Class 10", "Class 11", "Class 12")
    )


if "sample_answer_html" not in st.session_state:
    st.session_state.sample_answer_html = None

if "sample_answer_text" not in st.session_state:
    st.session_state.sample_answer_text = None


if st.button("✨ Generate Sample Answer"):

    if not question:
        st.error("Please enter a question first.")

    else:
        with st.spinner("Generating sample answer..."):

            try:
                response = requests.post(
                    SAMPLE_API,
                    json={
                        "query": question,
                        "class_name": class_name
                    }
                )

                html_response = response.text

                styled_html = f"""
                <div style="background-color:white; color:black; padding:15px; border-radius:10px;">
                    {html_response}
                </div>
                """

                st.session_state.sample_answer_html = styled_html

                # Convert HTML → text
                soup = BeautifulSoup(html_response, "html.parser")
                st.session_state.sample_answer_text = soup.get_text()

                st.success("Sample answer generated!")

            except Exception as e:
                st.error("Failed to generate sample answer")
                st.exception(e)

if st.session_state.sample_answer_html:

    st.subheader("📖 Generated Sample Answer")

    components.html(
        st.session_state.sample_answer_html,
        height=400,
        scrolling=True
    )

st.divider()

student_answer = st.text_area(
    "Student Answer",
    height=200,
    placeholder="Enter student's answer..."
)

st.subheader("📊 Question Configuration")

question_config = st.selectbox(
    "Select Question Type & Marks",
    options=(
        "Very Short (2 marks)",
        "Short (3 marks)",
        "Long (5 marks)"
    )
)

# Mapping logic
config_map = {
    "Very Short (2 marks)": {"type": "very short", "marks": 2},
    "Short (3 marks)": {"type": "short", "marks": 3},
    "Long (5 marks)": {"type": "long", "marks": 5}
}

question_type = config_map[question_config]["type"]
total_marks = config_map[question_config]["marks"]

if st.button("🚀 Evaluate Answer"):

    if not question or not student_answer:
        st.error("Please fill all required fields.")

    elif not st.session_state.sample_answer_text:
        st.error("Please generate the sample answer first.")

    else:

        payload = Input(
            question=question,
            reference_answer=st.session_state.sample_answer_text,
            question_image_description=None,
            answer_image_description=None,
            student_answer=student_answer,
            total_marks=total_marks,
            question_type=question_type
        )

        with st.spinner("Evaluating answer..."):

            try:
                response = requests.post(
                    EVALUATOR_API,
                    json=payload.model_dump()
                )

                result = response.json()

                st.success("Evaluation completed")

                st.subheader("✅ Marks Awarded")

                st.metric(
                    label="Score",
                    value=result["marks"]
                )

                st.subheader("📝 Student Feedback")

                st.text_area(
                    "Feedback",
                    value=result["feedback"],
                    height=200
                )

                left_col, right_col = st.columns(2)

                with left_col:
                    st.subheader("📋 Rubric")
                    st.json(result["rubric"])

                with right_col:
                    st.subheader("📊 Evaluation Details")
                    st.json(result["eval_list"])

            except Exception as e:
                st.error("Evaluation failed")
                st.exception(e)