"""Application-level AI orchestration: prompts and generation flows.

The Streamlit UI only ever calls this module — never a provider SDK — so
every AI-powered feature (study content, MCQs, mistake explanations, similar
questions) automatically uses the currently selected provider.
"""

from providers.base import AIProvider
from services.provider_manager import ProviderConfig, ProviderManager
from utils.response_parser import parse_mcqs, parse_question, parse_study_result

manager = ProviderManager()

STUDY_SYSTEM = """\
You are StudyMate AI, a friendly study assistant for students.
Rules:
- Use clear, student-friendly language.
- Base every answer strictly on the provided study material. Do not invent facts.
- Keep the summary concise (about 150-250 words).
- The explanation should break down the most important concepts simply, as if
  teaching a student who finds the topic difficult.
- Generate 6 flashcards covering the key facts, terms, or definitions.\
"""

STUDY_PROMPT = """\
Turn the study material below into three learning resources: a summary, a
simple explanation, and flashcards.

Respond ONLY with a JSON object with exactly this structure:
{{
  "summary": "concise overview of the material",
  "explanation": "simple explanation of the key concepts",
  "flashcards": [
    {{"front": "term or question", "back": "answer or definition"}}
  ]
}}

STUDY MATERIAL:
{material}\
"""

MCQ_SYSTEM = """\
You are StudyMate AI, a study assistant that writes practice questions.
Base every question strictly on the provided study material. Do not invent facts.\
"""

MCQ_PROMPT = """\
Create 5 multiple-choice questions based only on the study material below.

Rules:
- Exactly 4 answer options per question.
- "correct_answer" must be the exact text of the correct option.
- Include a one-sentence explanation of why the correct answer is correct.
- Test understanding of the concepts, not just memorized wording.

Respond ONLY with a JSON object with exactly this structure:
{{
  "mcqs": [
    {{
      "question": "the question",
      "options": ["option 1", "option 2", "option 3", "option 4"],
      "correct_answer": "exact text of the correct option",
      "explanation": "one-sentence explanation"
    }}
  ]
}}

STUDY MATERIAL:
{material}\
"""

EXPLAIN_SYSTEM = """\
You are an AI study tutor. Explain the student's incorrect answer using the
provided study material as the primary source. Do not invent information that
is not supported by the material.\
"""

EXPLAIN_PROMPT = """\
A student answered a practice question incorrectly.

STUDY MATERIAL:
{material}

QUESTION:
{question}

ANSWER OPTIONS:
{options}

STUDENT'S ANSWER:
{student_answer}

CORRECT ANSWER:
{correct_answer}

Explain:
1. Why the student's answer is incorrect (the likely misconception).
2. Why the correct answer is correct.
3. The key concept the student should remember.
4. A short memory tip when useful.

Format the answer as student-friendly markdown with exactly these sections:

💡 Why was your answer wrong?

**You chose "{student_answer}" because...** (the likely misconception)

**The correct answer is "{correct_answer}" because...**

📚 **Key idea** ...

🧠 **Remember** ... (a short memory tip)

Keep it under 150 words unless the topic genuinely needs more detail.\
"""

SIMILAR_SYSTEM = """\
You are StudyMate AI, a study assistant that writes practice questions.
Base every question strictly on the provided study material. Do not invent facts.\
"""

SIMILAR_PROMPT = """\
A student answered the practice question below incorrectly and has reviewed an
explanation. Generate ONE new question that tests the SAME underlying concept
or misconception, but with different wording or a different example. Do not
simply restate the original question.

ORIGINAL QUESTION:
{question}

ORIGINAL OPTIONS:
{options}

ORIGINAL CORRECT ANSWER:
{correct_answer}

STUDY MATERIAL:
{material}

Respond ONLY with a JSON object with exactly this structure:
{{
  "question": "the new question",
  "options": ["option 1", "option 2", "option 3", "option 4"],
  "correct_answer": "exact text of the correct option",
  "explanation": "one-sentence explanation"
}}\
"""

TEST_PROMPT = "Reply with exactly: OK"
TEST_SYSTEM = (
    "You are a connection test for StudyMate AI. Follow the instruction exactly."
)


def get_active_provider() -> AIProvider:
    return manager.get_active_provider()


def generate_study_material(study_text: str) -> dict:
    """Generate the summary, explanation, and flashcards (no MCQs)."""
    provider = get_active_provider()
    prompt = STUDY_PROMPT.format(material=study_text)
    raw = provider.generate(prompt, system=STUDY_SYSTEM, json_mode=True)
    return parse_study_result(raw)


def generate_mcqs(study_text: str) -> list[dict]:
    """Generate practice questions — called only from the MCQ button."""
    provider = get_active_provider()
    prompt = MCQ_PROMPT.format(material=study_text)
    raw = provider.generate(prompt, system=MCQ_SYSTEM, json_mode=True)
    return parse_mcqs(raw)


def explain_mistake(study_text: str, question: dict, student_answer: str) -> str:
    """Explain why a wrong MCQ answer was wrong, grounded in the material."""
    provider = get_active_provider()
    options_block = "\n".join(f"- {option}" for option in question.get("options", []))
    prompt = EXPLAIN_PROMPT.format(
        material=study_text,
        question=question.get("question", ""),
        options=options_block,
        student_answer=student_answer,
        correct_answer=question.get("correct_answer", ""),
    )
    return provider.generate(prompt, system=EXPLAIN_SYSTEM)


def generate_similar_question(study_text: str, question: dict) -> dict:
    """Generate one new question testing the same concept."""
    provider = get_active_provider()
    options_block = "\n".join(f"- {option}" for option in question.get("options", []))
    prompt = SIMILAR_PROMPT.format(
        question=question.get("question", ""),
        options=options_block,
        correct_answer=question.get("correct_answer", ""),
        material=study_text,
    )
    raw = provider.generate(prompt, system=SIMILAR_SYSTEM, json_mode=True)
    return parse_question(raw)


def test_provider(config: ProviderConfig) -> None:
    """Send a tiny request to verify a provider configuration.

    Raises a ProviderError with a student-friendly message on failure.
    """
    provider = manager.create_provider(config)
    provider.generate(TEST_PROMPT, system=TEST_SYSTEM)
