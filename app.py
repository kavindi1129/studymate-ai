import streamlit as st
import re
from google import genai
from dotenv import load_dotenv
from pypdf import PdfReader
import os

load_dotenv()

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="StudyMate AI",
    page_icon="🤖",
    layout="centered"
)

# -----------------------------
# Title
# -----------------------------
st.title("🤖 StudyMate AI")
st.subheader("Your AI-powered study assistant")

st.write(
    "Turn your study notes or lecture PDFs into "
    "summaries, explanations, MCQs and flashcards."
)

st.divider()

# -----------------------------
# Choose input method
# -----------------------------
input_method = st.radio(
    "How would you like to provide your study material?",
    ["📚 Paste Notes", "📄 Upload PDF"],
    horizontal=True
)

notes = ""

# -----------------------------
# Paste notes
# -----------------------------
if input_method == "📚 Paste Notes":

    notes = st.text_area(
        "📚 Paste your study notes here",
        height=250,
        placeholder="Paste your notes here..."
    )

# -----------------------------
# Upload PDF
# -----------------------------
else:

    uploaded_file = st.file_uploader(
        "📄 Upload your lecture PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        try:
            pdf_reader = PdfReader(uploaded_file)

            pdf_text = ""

            for page in pdf_reader.pages:
                text = page.extract_text()

                if text:
                    pdf_text += text + "\n"

            notes = pdf_text

            st.success(
                f"✅ PDF loaded successfully — "
                f"{len(pdf_reader.pages)} page(s)"
            )

        except Exception as e:
            st.error(f"Could not read the PDF: {e}")

# -----------------------------
# Generate button
# -----------------------------
if st.button("✨ Generate Study Material"):

    if not notes.strip():

        st.warning(
            "Please paste some notes or upload a PDF first."
        )

    else:

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:

            st.error("Gemini API key was not found.")

        else:

            try:

                client = genai.Client(api_key=api_key)

                prompt = f"""
You are StudyMate AI, a helpful study assistant.

Analyze these study materials:

{notes}

Return your answer using EXACTLY these four headings:

===SUMMARY===
Write a short and clear summary.

===EXPLANATION===
Explain the important concepts using simple,
student-friendly language.

===MCQS===
Create 5 multiple-choice questions.

Each question must have:
A, B, C and D options.

Clearly show the correct answer.

===FLASHCARDS===
Create 5 flashcards.

Use this format:

Question: ...
Answer: ...

Important:
- Keep the information accurate.
- Do not add any other headings.
- Keep the content suitable for a student.
"""

                with st.spinner(
                    "🤖 StudyMate is preparing your study material..."
                ):

                    response = client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=prompt
                    )

                result = response.text

                # -----------------------------
                # Separate sections
                # -----------------------------

                summary = (
                    result
                    .split("===SUMMARY===")[1]
                    .split("===EXPLANATION===")[0]
                    .strip()
                )

                explanation = (
                    result
                    .split("===EXPLANATION===")[1]
                    .split("===MCQS===")[0]
                    .strip()
                )

                mcqs = (
                    result
                    .split("===MCQS===")[1]
                    .split("===FLASHCARDS===")[0]
                    .strip()
                )

                flashcards = (
                    result
                    .split("===FLASHCARDS===")[1]
                    .strip()
                )

                # -----------------------------
                # Display results
                # -----------------------------

                st.success(
                    "✨ Your study material is ready!"
                )

                summary_tab, explanation_tab, mcq_tab, flashcard_tab = st.tabs(
                    [
                        "📖 Summary",
                        "💡 Explanation",
                        "📝 MCQs",
                        "🗂️ Flashcards"
                    ]
                )

                with summary_tab:

                    st.markdown("### 📖 Summary")
                    st.markdown(summary)

                with explanation_tab:

                    st.markdown("### 💡 Simple Explanation")
                    st.markdown(explanation)

                with mcq_tab:

                    st.markdown("### 📝 Practice MCQs")

                    # Put each MCQ option on a separate line
                    formatted_mcqs = re.sub(
                        r'\s+([A-D])\.\s+',
                        r'\n\n\1. ',
                        mcqs
                    )

                    # Preserve line breaks when displaying the MCQs
                    formatted_mcqs = formatted_mcqs.replace("\n", "  \n")

                    st.markdown(formatted_mcqs)

                with flashcard_tab:

                    st.markdown("### 🗂️ Flashcards")
                    st.markdown(flashcards)

            except Exception as e:

                st.error(
                    f"Something went wrong: {e}"
                )