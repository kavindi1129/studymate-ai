"""StudyMate AI — provider-agnostic AI study assistant.

Streamlit UI: a study workspace (notes/PDF → summary, explanation,
flashcards), on-demand interactive MCQs with mistake explanations, and a
Settings page for AI provider management. All AI work goes through
services.ai_service — the UI never calls a provider SDK directly.
"""

import uuid

import streamlit as st

from config import settings
from providers.base import ProviderError
from services import ai_service
from services.provider_manager import ProviderConfig, ProviderManager
from utils.pdf_utils import extract_pdf_text

manager = ProviderManager()

NAV_STUDY = "📚 Study"
NAV_SETTINGS = "⚙️ Settings"

PROVIDER_TYPE_LABELS = {"OpenAI Compatible": "openai_compatible"}


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _init_session_state() -> None:
    st.session_state.setdefault("study_text", "")
    st.session_state.setdefault("results", None)
    st.session_state.setdefault("quiz", None)


def _new_question_id() -> str:
    return f"q_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Provider selection widget (sidebar + Settings page)
# ---------------------------------------------------------------------------

def _provider_selectbox(label: str) -> None:
    configs = manager.list_configs()
    if manager.load_error:
        st.warning(manager.load_error)
    if not configs:
        st.info("No AI provider configured yet — add one in Settings.")
        return
    labels = [f"{config.name} — {config.model}" for config in configs]
    active = manager.active_config()
    ids = [config.id for config in configs]
    index = ids.index(active.id) if active and active.id in ids else 0
    choice = st.selectbox(label, labels, index=index)
    if choice != labels[index]:
        manager.set_active(ids[labels.index(choice)])
        st.rerun()


# ---------------------------------------------------------------------------
# Study page
# ---------------------------------------------------------------------------

def _render_study_page() -> None:
    st.title("🤖 StudyMate AI")
    st.markdown(
        "Paste your study notes or upload a lecture PDF and let AI turn them "
        "into a summary, a simple explanation, and flashcards. Quiz yourself "
        "with MCQs whenever you're ready."
    )

    mode_tab_notes, mode_tab_pdf = st.tabs(["📚 Paste Notes", "📄 Upload PDF"])

    study_text = ""

    with mode_tab_notes:
        notes = st.text_area(
            "Study notes",
            height=250,
            placeholder="Paste your study notes here...",
            label_visibility="collapsed",
        )
        study_text = notes.strip()

    with mode_tab_pdf:
        uploaded_pdf = st.file_uploader(
            "Upload a PDF",
            type=["pdf"],
            help="Lecture slides, notes, or any text-based PDF",
        )
        if uploaded_pdf is not None:
            try:
                pdf_text = extract_pdf_text(uploaded_pdf.getvalue())
            except Exception:
                st.error(
                    "The uploaded file could not be read as a PDF. "
                    "Please check the file and try again."
                )
                pdf_text = ""
            if pdf_text:
                study_text = pdf_text
                with st.expander("👀 Preview extracted text"):
                    st.text(
                        pdf_text[:2000] + ("..." if len(pdf_text) > 2000 else "")
                    )
            else:
                st.warning(
                    "No readable text was found in this PDF. "
                    "It may be a scanned or image-only document — "
                    "try pasting your notes instead."
                )

    if study_text and len(study_text) > settings.MAX_INPUT_CHARS:
        st.warning(
            f"The study material is very long ({len(study_text):,} characters). "
            f"Only the first {settings.MAX_INPUT_CHARS:,} characters will be used."
        )
        study_text = study_text[: settings.MAX_INPUT_CHARS]

    generate_clicked = st.button(
        "✨ Generate study resources",
        type="primary",
        disabled=not study_text,
    )

    if generate_clicked and study_text:
        # Reset quiz state from any previous generation.
        st.session_state.results = None
        st.session_state.quiz = None
        try:
            with st.spinner("StudyMate AI is working on your material..."):
                results = ai_service.generate_study_material(study_text)
            st.session_state.study_text = study_text
            st.session_state.results = results
            st.rerun()
        except ProviderError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Something went wrong while generating: {exc}")

    if st.session_state.results is not None:
        st.divider()
        _render_results(st.session_state.results)
        st.divider()
        _render_quiz_section()
        if st.button("🗑️ Clear results"):
            st.session_state.results = None
            st.session_state.quiz = None
            st.session_state.study_text = ""
            st.rerun()


def _render_results(results: dict) -> None:
    tab_summary, tab_explanation, tab_flashcards = st.tabs(
        ["📖 Summary", "💡 Simple Explanation", "🗂️ Flashcards"]
    )
    with tab_summary:
        st.subheader("📖 Summary")
        st.markdown(results["summary"])
    with tab_explanation:
        st.subheader("💡 Simple Explanation")
        st.markdown(results["explanation"])
    with tab_flashcards:
        st.subheader("🗂️ Flashcards")
        st.caption("Click a card to reveal the answer — try answering first!")
        for index, card in enumerate(results.get("flashcards", []), start=1):
            with st.expander(f"**{index}. {card.get('front', f'Card {index}')}**"):
                st.markdown(card.get("back", ""))


# ---------------------------------------------------------------------------
# On-demand interactive MCQs
# ---------------------------------------------------------------------------

def _render_quiz_section() -> None:
    st.subheader("📝 Test Yourself")
    quiz = st.session_state.quiz

    if quiz is None:
        st.caption(
            "MCQs are not generated automatically — click below when you're "
            "ready to practice."
        )
        if st.button("📝 Generate MCQs", type="primary"):
            try:
                with st.spinner("Creating your practice questions..."):
                    mcqs = ai_service.generate_mcqs(st.session_state.study_text)
                questions = [
                    {**mcq, "id": _new_question_id(), "source": "original"}
                    for mcq in mcqs
                ]
                st.session_state.quiz = {
                    "questions": questions,
                    "answers": {},
                    "explanations": {},
                }
                st.rerun()
            except ProviderError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Something went wrong while generating MCQs: {exc}")
        return

    _render_quiz(quiz)


def _render_quiz(quiz: dict) -> None:
    questions = quiz["questions"]
    answers = quiz["answers"]
    correct_count = sum(
        1
        for question in questions
        if answers.get(question["id"]) == question["correct_answer"]
    )
    st.metric("Progress", f"{len(answers)} answered · {correct_count} correct")

    for index, question in enumerate(questions):
        _render_question(index, question, quiz)

    if st.button("🔄 Reset answers"):
        quiz["questions"] = [
            q for q in questions if q.get("source") == "original"
        ]
        quiz["answers"] = {}
        quiz["explanations"] = {}
        st.rerun()


def _render_question(index: int, question: dict, quiz: dict) -> None:
    qid = question["id"]
    options = question["options"]
    answer = quiz["answers"].get(qid)

    title = f"**{index + 1}. {question['question']}**"
    if question.get("source") == "similar":
        title += "\n\n🔁 *Similar question — same concept, new wording*"
    st.markdown(title)

    if answer is None:
        choice = st.radio(
            "Your answer",
            options=options,
            index=None,
            key=f"choice_{qid}",
            label_visibility="collapsed",
        )
        if st.button("Submit answer", key=f"submit_{qid}", disabled=choice is None):
            if choice is not None:
                quiz["answers"][qid] = choice
                st.rerun()
    else:
        correct = question["correct_answer"]
        st.markdown(f"**Your answer:** {answer}")
        if answer == correct:
            st.success("✅ Correct!")
            if question.get("explanation"):
                st.caption(question["explanation"])
        else:
            st.error(f"❌ Incorrect — the correct answer is: {correct}")
            _render_mistake_actions(question, quiz)
    st.divider()


def _render_mistake_actions(question: dict, quiz: dict) -> None:
    """Explain My Mistake / Try a Similar Question for one wrong answer."""
    qid = question["id"]
    explanation = quiz["explanations"].get(qid)

    if explanation is None:
        if st.button("💡 Explain My Mistake", key=f"explain_{qid}"):
            try:
                with st.spinner("Analyzing your mistake..."):
                    text = ai_service.explain_mistake(
                        st.session_state.study_text,
                        question,
                        quiz["answers"][qid],
                    )
                quiz["explanations"][qid] = text
                st.rerun()
            except ProviderError as exc:
                st.warning(
                    "⚠️ We couldn't generate an explanation right now. "
                    "Please try again or continue to the next question.\n\n"
                    f"Details: {exc}"
                )
            except Exception:
                st.warning(
                    "⚠️ We couldn't generate an explanation right now. "
                    "Please try again or continue to the next question."
                )
        return

    st.markdown(explanation)

    already_has_similar = any(
        q.get("parent_id") == qid for q in quiz["questions"]
    )
    if already_has_similar:
        return
    if st.button("🔄 Try a Similar Question", key=f"similar_{qid}"):
        try:
            with st.spinner("Creating a similar question..."):
                similar = ai_service.generate_similar_question(
                    st.session_state.study_text, question
                )
            similar["id"] = _new_question_id()
            similar["source"] = "similar"
            similar["parent_id"] = qid
            questions = quiz["questions"]
            position = next(
                (i for i, q in enumerate(questions) if q["id"] == qid),
                len(questions) - 1,
            )
            questions.insert(position + 1, similar)
            st.rerun()
        except ProviderError as exc:
            st.warning(
                "⚠️ We couldn't generate a similar question right now.\n\n"
                f"Details: {exc}"
            )
        except Exception:
            st.warning("⚠️ We couldn't generate a similar question right now.")


# ---------------------------------------------------------------------------
# Settings page
# ---------------------------------------------------------------------------

def _render_settings_page() -> None:
    st.title("⚙️ Settings")
    st.markdown("Manage the AI providers StudyMate AI uses for every feature.")

    st.subheader("AI Providers")
    _provider_selectbox("Default Provider")
    _render_configured_providers()
    _render_add_provider_form()


def _render_configured_providers() -> None:
    configs = manager.list_configs()
    if manager.load_error:
        st.warning(manager.load_error)
    if not configs:
        st.info(
            "No providers configured yet — Gemini appears automatically once "
            "GEMINI_API_KEY is set in .env, or add a custom provider below."
        )
        return

    gemini_key_set = bool(settings.get_gemini_api_key())
    for config in configs:
        with st.container(border=True):
            col_info, col_actions = st.columns([3, 1])
            with col_info:
                if config.type == "gemini":
                    status = "🟢" if gemini_key_set else "⚪"
                    hint = (
                        "API key from .env (GEMINI_API_KEY)"
                        if gemini_key_set
                        else "No API key — set GEMINI_API_KEY in .env"
                    )
                    st.markdown(f"{status} **{config.name}**")
                    st.caption(
                        f"Type: Gemini (built-in) · Model: {config.model} · {hint}"
                    )
                else:
                    st.markdown(f"🟢 **{config.name}**")
                    key_hint = (
                        f"Key: {config.masked_api_key()}"
                        if config.api_key
                        else "No API key set"
                    )
                    st.caption(
                        f"Type: OpenAI-compatible · Model: {config.model} · {key_hint}"
                    )
            with col_actions:
                test_clicked = st.button("🔌 Test", key=f"test_{config.id}")

            if config.type == "gemini":
                new_model = st.text_input(
                    "Gemini model",
                    value=config.model,
                    key=f"model_{config.id}",
                )
                if new_model.strip() and new_model.strip() != config.model:
                    manager.set_gemini_model(new_model.strip())
                    st.rerun()
            else:
                if st.button("🗑️ Remove provider", key=f"remove_{config.id}"):
                    manager.remove(config.id)
                    st.rerun()

            if test_clicked:
                _test_provider(config)


def _render_add_provider_form() -> None:
    st.subheader("➕ Add Provider")
    st.caption(
        "Connect any OpenAI-compatible API. The key is stored locally in "
        "providers.json (gitignored) and never displayed in full."
    )

    name = st.text_input("Provider Name", placeholder="My AI Provider", key="add_name")
    provider_type = st.selectbox(
        "Provider Type", list(PROVIDER_TYPE_LABELS), key="add_type"
    )
    base_url = st.text_input(
        "API Base URL", placeholder="https://example.com/v1", key="add_base_url"
    )
    api_key = st.text_input(
        "API Key", type="password", placeholder="sk-...", key="add_api_key"
    )
    model = st.text_input(
        "Model Name", placeholder="example-model", key="add_model"
    )

    col_test, col_save = st.columns(2)
    test_clicked = col_test.button("🔍 Test Connection", key="add_test")
    save_clicked = col_save.button("💾 Save Provider", type="primary", key="add_save")

    if test_clicked:
        _test_new_provider(
            name.strip(), provider_type, base_url.strip(), api_key.strip(), model.strip()
        )
    if save_clicked:
        _save_new_provider(
            name.strip(), provider_type, base_url.strip(), api_key.strip(), model.strip()
        )


def _test_new_provider(
    name: str, provider_type: str, base_url: str, api_key: str, model: str
) -> None:
    if not base_url or not model:
        st.warning("Enter the base URL and model name before testing.")
        return
    config = ProviderConfig(
        id="unsaved",
        name=name or "New provider",
        type=PROVIDER_TYPE_LABELS[provider_type],
        model=model,
        base_url=base_url,
        api_key=api_key,
    )
    _test_provider(config)


def _save_new_provider(
    name: str, provider_type: str, base_url: str, api_key: str, model: str
) -> None:
    if not (name and base_url and model):
        st.warning("Provider name, base URL, and model name are required.")
        return
    configs = manager.list_configs()
    if any(config.name.lower() == name.lower() for config in configs):
        st.warning(f"A provider named '{name}' already exists. Choose a different name.")
        return

    config = manager.add_custom(
        name=name,
        base_url=base_url,
        api_key=api_key,
        model=model,
    )
    _ = provider_type  # currently only "OpenAI Compatible" is offered
    for key in ("add_name", "add_base_url", "add_api_key", "add_model"):
        st.session_state.pop(key, None)
    st.toast(f"Provider '{config.name}' saved and selected.")
    st.rerun()


def _test_provider(config: ProviderConfig) -> None:
    try:
        with st.spinner(f"Testing {config.name}..."):
            ai_service.test_provider(config)
        st.success("✅ Connection successful. Provider is ready to use.")
    except ProviderError as exc:
        st.error(
            "❌ Connection failed.\n\n"
            f"{exc}\n\n"
            "Check:\n"
            "- API key\n"
            "- Base URL\n"
            "- Model name\n"
            "- Provider availability"
        )
    except Exception:
        st.error(
            "❌ Connection failed.\n\n"
            "Check:\n"
            "- API key\n"
            "- Base URL\n"
            "- Model name\n"
            "- Provider availability"
        )


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="StudyMate AI",
        page_icon="🤖",
        layout="centered",
    )
    _init_session_state()

    with st.sidebar:
        st.title("🤖 StudyMate AI")
        page = st.radio(
            "Navigation",
            [NAV_STUDY, NAV_SETTINGS],
            label_visibility="collapsed",
        )
        st.divider()
        st.markdown("#### ⚙️ AI Settings")
        _provider_selectbox("Provider")

    if page == NAV_SETTINGS:
        _render_settings_page()
    else:
        _render_study_page()


if __name__ == "__main__":
    main()
