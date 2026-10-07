"""Robust parsing of AI text responses.

Providers return free text that should contain JSON. This module tolerates
markdown code fences, surrounding prose, and minor answer-format drift so the
interactive quiz can compare answers reliably.
"""

import json


class ResponseFormatError(RuntimeError):
    """The AI response could not be parsed into the expected structure."""


def extract_json(text: str):
    """Parse the first JSON object or array found in a model response."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ResponseFormatError(
            "The AI returned an empty response. Please try again."
        )

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        while lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    starts = [i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1]
    if not starts:
        raise ResponseFormatError(
            "The AI returned an unexpected response format. Please try again."
        )
    start = min(starts)
    ends = [i for i in (cleaned.rfind("}"), cleaned.rfind("]")) if i != -1]
    if not ends or max(ends) <= start:
        raise ResponseFormatError(
            "The AI returned an unexpected response format. Please try again."
        )

    snippet = cleaned[start : max(ends) + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError as exc:
        raise ResponseFormatError(
            "The AI returned an unexpected response format. Please try again."
        ) from exc


def parse_study_result(text: str) -> dict:
    """Parse the summary / explanation / flashcards generation response."""
    data = extract_json(text)
    if not isinstance(data, dict):
        raise ResponseFormatError(
            "The AI response was missing the expected sections. "
            "Please try generating again."
        )

    result = {}
    for key in ("summary", "explanation"):
        value = str(data.get(key) or "").strip()
        if not value:
            raise ResponseFormatError(
                f"The AI response was missing the section '{key}'. "
                "Please try generating again."
            )
        result[key] = value

    flashcards = []
    for item in data.get("flashcards") or []:
        if not isinstance(item, dict):
            continue
        front = str(item.get("front") or "").strip()
        back = str(item.get("back") or "").strip()
        if front and back:
            flashcards.append({"front": front, "back": back})
    if not flashcards:
        raise ResponseFormatError(
            "The AI response was missing the section 'flashcards'. "
            "Please try generating again."
        )
    result["flashcards"] = flashcards
    return result


def parse_mcqs(text: str) -> list[dict]:
    """Parse an on-demand MCQ generation response into quiz questions."""
    data = extract_json(text)
    if isinstance(data, dict):
        items = data.get("mcqs") or data.get("questions") or []
    elif isinstance(data, list):
        items = data
    else:
        raise ResponseFormatError(
            "No MCQs were generated. Please try again."
        )

    mcqs = [_normalize_mcq(item) for item in items if isinstance(item, dict)]
    # Only keep questions whose correct answer maps onto a real option —
    # otherwise the question could never be answered correctly.
    mcqs = [
        mcq
        for mcq in mcqs
        if mcq["question"]
        and len(mcq["options"]) >= 2
        and mcq["correct_answer"] in mcq["options"]
    ]
    if not mcqs:
        raise ResponseFormatError(
            "No MCQs were generated. Please try again."
        )
    return mcqs


def parse_question(text: str) -> dict:
    """Parse a single generated question (e.g. a similar-question request)."""
    data = extract_json(text)
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        raise ResponseFormatError(
            "The AI returned an unexpected response format. Please try again."
        )

    question = _normalize_mcq(data)
    if (
        not question["question"]
        or len(question["options"]) < 2
        or question["correct_answer"] not in question["options"]
    ):
        raise ResponseFormatError(
            "The generated question could not be read. Please try again."
        )
    return question


def _normalize_mcq(item: dict) -> dict:
    """Coerce one MCQ dict into the internal question format."""
    question = str(item.get("question") or item.get("prompt") or "").strip()
    raw_options = item.get("options") or item.get("choices") or []
    options = [str(option).strip() for option in raw_options if str(option).strip()]
    correct = str(item.get("correct_answer") or item.get("answer") or "").strip()
    explanation = str(item.get("explanation") or "").strip()
    return {
        "question": question,
        "options": options,
        "correct_answer": _match_option(correct, options),
        "explanation": explanation,
    }


def _match_option(correct: str, options: list[str]) -> str:
    """Snap a correct-answer string onto one of the options.

    Models sometimes prefix the answer with a letter ("B. ...") or vary the
    casing; interactive checking needs an exact option match.
    """
    if not options:
        return correct

    stripped = correct
    if len(correct) >= 2 and correct[0].upper() in "ABCDEF" and correct[1] in ".):":
        stripped = correct[2:].strip()

    for candidate in (correct, stripped):
        for option in options:
            if candidate == option or (candidate and candidate.lower() == option.lower()):
                return option

    # Partial-match fallback for minor wording drift on long answers.
    for candidate in (correct, stripped):
        if len(candidate) >= 10:
            for option in options:
                if candidate in option or option in candidate:
                    return option

    return correct
