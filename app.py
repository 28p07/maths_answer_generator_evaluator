import base64
import requests
import streamlit as st

SAMPLE_API = "https://chat-backend-test.prepzy.ai/maths-sample-answer-generator"
OCR_API = "https://chat-backend-test.prepzy.ai/ocr-agent"
EVAL_API = "https://chat-backend-test.prepzy.ai/student-answer-evaluator"

def call_ocr_api(uploaded_file):
    try:
        files = {
            "image": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type or "image/jpeg"
            )
        }

        response = requests.post(OCR_API, files=files)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"OCR API Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        st.error(f"OCR Error: {e}")
        return None

def display_diagrams(diagrams, key_prefix):
    updated_diagrams = []
    for i, diag in enumerate(diagrams):
        col1, col2 = st.columns([4, 1])

        with col1:
            image_bytes = base64.b64decode(diag["base64"])
            st.image(image_bytes, use_container_width=True)

        with col2:
            remove = st.checkbox("Remove", key=f"{key_prefix}_remove_{i}")

        if not remove:
            updated_diagrams.append(diag)

    return updated_diagrams

if "answer_text" not in st.session_state:
    st.session_state.answer_text = ""

if "answer_diagrams" not in st.session_state:
    st.session_state.answer_diagrams = []

if "api_data" not in st.session_state:
    st.session_state.api_data = {}

if "show_solution" not in st.session_state:
    st.session_state.show_solution = True

if "show_rubric" not in st.session_state:
    st.session_state.show_rubric = True

st.set_page_config(page_title="Maths Sample Answer Generator", layout="wide")

st.title("📘 Maths Sample Answer Generator")

query = st.text_area("Enter your question", height=150)

class_name = st.selectbox(
    "Select Class",
    [
        'CLASS 6','CLASS 7','CLASS 8',
        'CLASS 9','CLASS 10','CLASS 11','CLASS 12'
    ]
)

uploaded_file = st.file_uploader(
    "Upload Diagram (optional)", 
    type=["png", "jpg", "jpeg"]
)

base64_str = None
if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    st.image(file_bytes, caption="Uploaded Diagram", use_container_width=True)
    base64_str = base64.b64encode(file_bytes).decode("utf-8")

if st.button("Generate Sample Answer"):
    if not query.strip():
        st.warning("Please enter a question")
    else:
        payload = {
            "query": query,
            "class_name": class_name,
            "base64": base64_str if base64_str else None
        }

        try:
            with st.spinner("Generating answer..."):
                response = requests.post(
                    SAMPLE_API,
                    json=payload,
                    timeout=150
                )

            st.write("Status Code:", response.status_code)

            if response.status_code == 200:
                data = response.json()
                st.session_state.api_data = data
                st.session_state.show_solution = True
                st.session_state.show_rubric = True
            else:
                st.error("API returned an error ❌")
                st.code(response.text)

        except requests.exceptions.Timeout:
            st.error("Request timed out ⏱️")

        except requests.exceptions.ConnectionError:
            st.error("Could not connect to backend 🚫")

        except Exception as e:
            st.error(f"Unexpected error: {e}")

if st.session_state.api_data:
    with st.expander("📘 Solution", expanded=st.session_state.show_solution):
        html_content = f"""
        <div style="background-color:white; color:black; padding:20px;">
            {st.session_state.api_data.get("solution_html", "No solution returned")}
        </div>
        """
        st.components.v1.html(
            html_content,
            height=900,
            scrolling=True
        )

    with st.expander("📊 Rubric", expanded=st.session_state.show_rubric):
        st.json(st.session_state.api_data.get("rubric", {}))

st.header("📄 Upload Answer")

a_file = st.file_uploader("Upload Answer Image", type=["png", "jpg", "jpeg"], key="answer_upload")

if st.button("🔍 Do OCR") and a_file:
    result = call_ocr_api(a_file)
    if result:
        st.session_state.answer_text = result.get("final_string", "")
        st.session_state.answer_diagrams = result.get("diagrams", [])
        st.session_state.show_solution = False
        st.session_state.show_rubric = False

st.header("✏️ Answer Input")

st.session_state.answer_text = st.text_area(
    "Answer Text (Edit if needed)",
    value=st.session_state.answer_text,
    height=200
)

st.header("🖼️ Diagrams")

st.session_state.answer_diagrams = display_diagrams(
    st.session_state.answer_diagrams,
    "a"
)

st.header("📊 Evaluate Answer")

total_marks = st.number_input("Total Marks", min_value=1, max_value=100, value=5)

if st.button("🚀 Evaluate Answer"):

    if not query:
        st.warning("Question is missing.")
        st.stop()

    if not st.session_state.answer_text.strip():
        st.warning("Please provide student answer (typed or OCR).")
        st.stop()

    if not st.session_state.api_data:
        st.warning("Please generate sample answer first.")
        st.stop()

    try:
        with st.spinner("Evaluating..."):

            a_diagrams_base64 = [
                d["base64"] for d in st.session_state.answer_diagrams
            ]

            payload = {
                "query":query,
                "student_answer":st.session_state.answer_text,
                "total_marks":total_marks,
                "rubric":st.session_state.api_data.get("rubric", {}),
                "base64": a_diagrams_base64[0] if a_diagrams_base64 else None
            }
            print("Payload : ",payload)

            result = requests.post(
                    EVAL_API,
                    json=payload,
                    timeout=150
                )
        result = result.json()
        marks = result.get("marks_awarded", 0)
        feedback_list = result.get("feedback", [])

        st.subheader(f"✅ Marks Awarded: {marks} / {total_marks}")
        st.progress(min(marks / total_marks, 1.0))

        st.subheader("📝 Feedback")

        if feedback_list:
            for i, fb in enumerate(feedback_list, 1):
                st.markdown(f"{i}. {fb}")
        else:
            st.info("No feedback available.")

    except Exception as e:
        st.error(f"Evaluation failed: {e}")

