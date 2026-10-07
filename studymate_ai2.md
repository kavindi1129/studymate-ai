# StudyMate AI — ZCode Development Specification

## 1. Goal

Upgrade the existing StudyMate AI application from a Gemini-only app into a flexible AI study assistant supporting:

- Gemini as the default provider.
- Custom AI providers through a Settings page.
- OpenAI-compatible custom APIs.
- Secure API-key handling.
- Provider/model selection.
- Summary, Explanation, and Flashcards as normal generation.
- MCQs generated **only when the user explicitly clicks a Generate MCQs button**.

Preserve all existing working functionality.

---

## 2. Important Rules

Before changing anything:

1. Inspect the existing codebase.
2. Inspect `app.py`, `requirements.txt`, `.gitignore`, and the current structure.
3. Preserve working features.
4. Do not unnecessarily rewrite the project.
5. Do not expose API keys.
6. Do not commit `.env`.
7. Do not automatically push to GitHub.
8. Keep the architecture simple and suitable for a student portfolio project.
9. Test the application after major changes.

---

# 3. Current Project

Current structure:

```text
studymate-ai/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env
└── .venv/
```

Current technology:

- Python
- Streamlit
- Google Gemini API
- `google-genai`
- `python-dotenv`
- `pypdf`

The current application contains most logic in `app.py` and communicates directly with Gemini.

The goal is to introduce a provider layer without breaking the existing application.

---

# 4. New Architecture

```text
                         USER
                           |
                           v
                    STREAMLIT UI
                           |
              +------------+------------+
              |                         |
              v                         v
       Study Workspace             Settings
              |                         |
              |                   Provider Manager
              |                         |
              |              +----------+----------+
              |              |                     |
              |              v                     v
              |           Gemini            Custom Provider
              |                                    |
              |                              Base URL / Key / Model
              |                                    |
              +---------------+--------------------+
                              |
                              v
                       AI PROVIDER LAYER
                              |
                              v
                         AI SERVICE
                              |
                 +------------+------------+
                 |            |            |
                 v            v            v
              Summary    Explanation   Flashcards
                              |
                              v
                       User requests MCQs
                              |
                              v
                         Generate MCQs
                              |
                              v
                         Streamlit UI
```

---

# 5. Provider Abstraction

Do not let the Streamlit UI call Gemini-specific SDK code directly.

Use a common provider interface:

```text
UI
 |
 v
AI Service
 |
 v
Provider Interface
 |
 +-- Gemini Provider
 |
 +-- OpenAI-Compatible Provider
 |
 +-- Future Providers
```

The common provider should expose a simple operation conceptually equivalent to:

```text
generate(prompt)
```

Optionally support system instructions or other generation parameters where useful.

The exact Python implementation is up to the coding agent.

---

# 6. Gemini Provider

Gemini must remain fully supported.

Create a dedicated Gemini provider responsible for:

- Gemini client creation.
- API authentication.
- Model selection.
- Sending requests.
- Returning generated text.
- Provider-specific error handling.

Do not remove the existing Gemini functionality.

Gemini should remain the default provider when a Gemini API key is configured.

---

# 7. Custom Provider

Add support for a generic **OpenAI-compatible provider**.

The user should be able to configure:

```text
Provider Name
API Base URL
API Key
Model Name
```

Optional fields can be added only if genuinely useful:

```text
Organization
Temperature
Max Output Tokens
Context Limit
```

Do not hard-code a particular third-party service.

The purpose is to let users connect compatible APIs to StudyMate AI.

Example:

```text
Provider Name:
My AI Provider

API Base URL:
https://example.com/v1

API Key:
**************

Model:
example-model
```

---

# 8. Settings Page

Add a Settings area to the Streamlit application.

Suggested navigation:

```text
📚 Study
⚙️ Settings
```

Settings should contain:

```text
⚙️ Settings

AI Providers

Default Provider
[ Gemini ▼ ]

Configured Providers
----------------------------

🟢 Gemini
   Model: gemini-3.5-flash

🟢 My Custom Provider
   Model: example-model

[ + Add Provider ]
```

Keep the interface clean and student-friendly.

---

# 9. Add Provider Form

When the user clicks `+ Add Provider`, show:

```text
Provider Name
[________________]

Provider Type
[ OpenAI Compatible ▼ ]

API Base URL
[________________]

API Key
[________________]

Model
[________________]

[ Test Connection ]

[ Save Provider ]
```

The API key input must be a password/secret-style field.

Never display the full saved API key.

---

# 10. Test Connection

The user should be able to test a provider before using it.

Flow:

```text
Enter provider details
        |
        v
Test Connection
        |
        v
Small test request
        |
        +----> Success
        |
        +----> Error
```

Success:

```text
✅ Connection successful.
Provider is ready to use.
```

Failure:

```text
❌ Connection failed.

Check:
- API key
- Base URL
- Model name
- Provider availability
```

Never expose the API key in an error message.

---

# 11. Provider Manager

Create a provider manager or equivalent service responsible for:

- Registering providers.
- Listing configured providers.
- Selecting the active provider.
- Getting the active provider.
- Testing providers.
- Removing providers if the chosen storage approach safely supports it.

Conceptual flow:

```text
Settings
   |
   v
Provider Manager
   |
   v
Provider Configuration
   |
   v
Provider Factory / Resolver
   |
   v
Provider Implementation
```

---

# 12. Provider Configuration

Use a structured provider configuration.

Conceptually:

```text
ProviderConfig

name
type
base_url
api_key
model
```

Optional:

```text
organization
temperature
max_output_tokens
context_limit
```

Keep this model simple.

---

# 13. Provider Factory / Resolver

Use a simple factory or equivalent mechanism.

Conceptually:

```text
type = Gemini
    -> GeminiProvider

type = OpenAI Compatible
    -> OpenAICompatibleProvider
```

This allows future providers to be added without rewriting the StudyMate application.

Possible future providers:

- OpenAI
- Anthropic
- OpenRouter
- Local models
- Other OpenAI-compatible APIs

Do not implement all future providers now unless the implementation is straightforward.

---

# 14. AI Service

Create an application-level AI service.

Responsibilities:

```text
AIService
   |
   +-- get active provider
   +-- generate study content
   +-- generate MCQs on request
   +-- return results to UI
```

The UI should call the AI service rather than directly calling provider SDKs.

Preferred:

```text
Streamlit UI
     |
     v
AIService
     |
     v
Selected Provider
```

Avoid:

```text
Streamlit UI
     |
     v
Gemini SDK
```

---

# 15. Recommended Project Structure

Refactor into a small modular structure:

```text
studymate-ai/
|
├── app.py
|
├── services/
│   ├── __init__.py
│   ├── ai_service.py
│   └── provider_manager.py
|
├── providers/
│   ├── __init__.py
│   ├── base.py
│   ├── gemini_provider.py
│   └── openai_compatible_provider.py
|
├── utils/
│   ├── __init__.py
│   ├── pdf_utils.py
│   └── response_parser.py
|
├── config/
│   ├── __init__.py
│   └── settings.py
|
├── requirements.txt
├── README.md
├── .gitignore
├── .env
└── .venv/
```

If the coding agent finds a cleaner structure, keep the same responsibilities without creating unnecessary files.

---

# 16. File Responsibilities

## `app.py`

Main Streamlit UI:

- Navigation.
- User input.
- Study workspace.
- Settings UI.
- Calling services.
- Displaying results.

It should not contain all provider-specific API code.

## `providers/base.py`

Common AI provider interface/contract.

Conceptually:

```text
AIProvider
    generate(...)
```

## `providers/gemini_provider.py`

Gemini-specific implementation.

## `providers/openai_compatible_provider.py`

Generic OpenAI-compatible API implementation.

Responsibilities:

- Base URL.
- API key.
- Model.
- Request.
- Response.
- Error handling.

## `services/ai_service.py`

Application-level AI orchestration.

Responsibilities:

- Use selected provider.
- Generate summary/explanation/flashcards.
- Generate MCQs on demand.

## `services/provider_manager.py`

Provider configuration and selection.

## `utils/pdf_utils.py`

PDF text extraction using `pypdf`.

## `utils/response_parser.py`

Response parsing, section extraction, and MCQ parsing.

## `config/settings.py`

Application/environment configuration.

---

# 17. Existing Study Workflow

Preserve:

```text
User
 |
 +--> Paste Notes
 |
 +--> Upload PDF
          |
          v
       pypdf
          |
          v
     Extract Text
          |
          v
      AI Service
          |
          v
   Selected Provider
          |
          v
   Summary / Explanation / Flashcards
```

---

# 18. MCQ Requirement — IMPORTANT

MCQs must **NOT** be generated automatically during the initial study-material generation.

Current/old behavior:

```text
Generate
   |
   +--> Summary
   +--> Explanation
   +--> MCQs
   +--> Flashcards
```

New behavior:

```text
Generate
   |
   +--> Summary
   +--> Explanation
   +--> Flashcards
```

Then:

```text
User clicks:

📝 Generate MCQs

        |
        v
Selected Provider
        |
        v
MCQ Generation
        |
        v
Display MCQs
```

Do not regenerate the other study sections when the MCQ button is clicked.

---

# 19. MCQ UI

After normal results:

```text
📖 Summary
...

💡 Explanation
...

🗂️ Flashcards
...

--------------------------------

📝 Test Yourself

[ Generate MCQs ]
```

Only after clicking the button should MCQs appear.

---

# 20. MCQ Prompt

Use a dedicated MCQ prompt.

Conceptually:

```text
Generate multiple-choice questions based only on the provided study material.

For each question provide:

Question:
A:
B:
C:
D:
Answer:
```

The coding agent may improve the prompt while keeping the same structured output requirement.

---

# 21. MCQ Display

Use a clean format:

```text
📝 MCQs

Question 1
...

A. ...
B. ...
C. ...
D. ...

Answer:
...
```

If practical, answers may be hidden/revealed, but this is optional.

The mandatory requirement is:

**MCQs are generated only after the user requests them.**

---

# 22. Provider Selection

The user must be able to select the active provider.

Suggested sidebar:

```text
⚙️ AI Settings

Provider
[ Gemini ▼ ]

Model
[ gemini-3.5-flash ]
```

Example configured providers:

```text
Gemini — gemini-3.5-flash
My Custom Provider — example-model
```

The selected provider should be used for:

- Summary.
- Explanation.
- Flashcards.
- MCQs.

---

# 23. Security

API keys are sensitive.

Rules:

- Never hard-code API keys.
- Never print API keys.
- Never log API keys.
- Never show full API keys.
- Never put API keys in README.
- Never commit `.env`.
- Keep `.env` in `.gitignore`.
- Do not expose secrets unnecessarily through Streamlit session state.
- Do not change the existing `.env` destructively.

For local development, environment variables / `.env` are acceptable.

For user-added provider credentials, use the safest simple local storage approach practical for this student project. If persistent encrypted secret storage would require excessive complexity, document the limitation clearly rather than pretending the storage is production-grade.

---

# 24. Error Handling

Handle:

### Invalid API key

```text
❌ Authentication failed.
Please check your API key.
```

### Invalid URL

```text
❌ Unable to connect to the provider.
Please check the API base URL.
```

### Invalid model

```text
❌ The selected model could not be used.
Please check the model name.
```

### Provider unavailable

```text
❌ The AI provider is currently unavailable.
Try again later or select another provider.
```

### Empty material

```text
Please provide notes or upload a PDF first.
```

### PDF extraction failure

```text
We couldn't extract readable text from this PDF.
Please try another PDF or paste the notes directly.
```

### MCQ failure

MCQ failure must not remove already generated Summary, Explanation, or Flashcards.

---

# 25. Session State

Use Streamlit session state where appropriate for:

- Current study material.
- Summary.
- Explanation.
- Flashcards.
- MCQs.
- Selected provider.
- Current provider configuration state.

Do not introduce unnecessary session-state complexity.

---

# 26. Dependencies

Keep existing dependencies:

```text
streamlit
google-genai
python-dotenv
pypdf
```

Only add another package if it is genuinely needed for the OpenAI-compatible provider.

Avoid unnecessary frameworks.

---

# 27. Testing Plan

## Gemini

```text
Select Gemini
   |
Generate
   |
Verify Summary
Verify Explanation
Verify Flashcards
   |
Click Generate MCQs
   |
Verify MCQs
```

## Custom Provider

```text
Add custom provider
   |
Test Connection
   |
Select provider
   |
Generate
   |
Verify study content
   |
Generate MCQs
```

## PDF

```text
Upload PDF
   |
Extract text
   |
Generate
   |
Verify results
```

## Error cases

Test:

- Wrong API key.
- Wrong base URL.
- Wrong model.
- Empty notes.
- Invalid PDF.
- Provider unavailable.
- MCQ generation failure.

---

# 28. Acceptance Criteria

The implementation is complete when:

- [ ] Existing StudyMate functionality still works.
- [ ] Gemini remains supported.
- [ ] Gemini-specific code is separated from the UI.
- [ ] Provider abstraction exists.
- [ ] Provider manager/resolver exists.
- [ ] Settings page exists.
- [ ] User can add a custom provider.
- [ ] User can enter provider name.
- [ ] User can enter base URL.
- [ ] User can enter API key.
- [ ] User can enter model name.
- [ ] User can test the connection.
- [ ] User can select the active provider.
- [ ] Selected provider is actually used.
- [ ] API keys are protected.
- [ ] `.env` remains ignored by Git.
- [ ] Summary works.
- [ ] Explanation works.
- [ ] Flashcards work.
- [ ] MCQs are NOT generated automatically.
- [ ] MCQs appear only after clicking Generate MCQs.
- [ ] MCQs use the selected provider.
- [ ] PDF upload still works.
- [ ] Errors are handled gracefully.
- [ ] UI remains simple and student-friendly.

---

# 29. Final Architecture

```text
                         USER
                           |
                           v
                    STREAMLIT UI
                           |
              +------------+------------+
              |                         |
              v                         v
           STUDY                     SETTINGS
              |                         |
              |                  Provider Manager
              |                         |
              |              +----------+----------+
              |              |                     |
              |              v                     v
              |           Gemini            Custom Provider
              |                                    |
              +----------------+-------------------+
                               |
                               v
                        PROVIDER LAYER
                               |
                               v
                           AI SERVICE
                               |
                 +-------------+-------------+
                 |             |             |
                 v             v             v
              Summary     Explanation   Flashcards
                               |
                               v
                       User requests MCQs
                               |
                               v
                         Generate MCQs
                               |
                               v
                              USER
```

The key architectural principle is:

```text
StudyMate AI
     |
     v
AI Service
     |
     v
Provider Interface
     |
     +-- Gemini
     |
     +-- OpenAI-Compatible Custom Provider
     |
     +-- Future Providers
```

This makes StudyMate AI provider-agnostic and allows additional AI APIs to be added without rewriting the whole application.

---

# 30. Instructions to ZCode

Treat this document as the project specification.

Before editing:

1. Inspect the current codebase.
2. Identify how Gemini is currently connected.
3. Identify how MCQs are currently generated.
4. Preserve working functionality.
5. Refactor incrementally.
6. Implement provider abstraction.
7. Implement Gemini provider.
8. Implement OpenAI-compatible custom provider.
9. Implement Settings and provider management.
10. Implement provider selection.
11. Change MCQs to on-demand generation.
12. Test all major workflows.
13. Check that secrets are not staged.
14. Do not automatically commit or push to GitHub.

At the end, report:

- Files created.
- Files modified.
- Dependencies added.
- Features implemented.
- Tests performed.
- Remaining limitations.

Do not expose any API keys or other secrets in the final report.

---

# 31. Outstanding Learning Feature — Explain My Mistake

Add a new learning feature called **Explain My Mistake** to make StudyMate AI more than a simple quiz generator.

This feature should be built on top of the existing **on-demand MCQ system**.

The goal is to create a learning loop:

```text
Study Material
      |
      v
Generate MCQs
      |
      v
Student answers
      |
      v
Correct / Incorrect
      |
      v
If incorrect:
      |
      v
Explain My Mistake
      |
      v
AI explains the misunderstanding
      |
      v
Student tries a similar question
```

## 31.1 MCQ Interaction

MCQs should become interactive rather than only displaying a block of generated text.

For each MCQ, allow the student to select an answer.

Example:

```text
📝 Question 1

What is the purpose of a primary key?

( ) A. Store duplicate records
( ) B. Uniquely identify a record
( ) C. Sort a table
( ) D. Delete records

[ Submit Answer ]
```

After submission, determine whether the selected answer is correct.

Correct:

```text
✅ Correct!
```

Incorrect:

```text
❌ Incorrect

Your answer: A
Correct answer: B

[ 💡 Explain My Mistake ]
```

Do not automatically generate a long explanation before the user requests it. The user should be able to ask StudyMate why the answer was wrong.

## 31.2 Explain My Mistake Action

When the student gets an MCQ wrong, show:

```text
[ 💡 Explain My Mistake ]
```

When clicked, send a dedicated request to the currently selected AI provider.

The request should include enough context to explain the mistake accurately:

```text
- Original study material/context
- The question
- The answer choices
- Student's selected answer
- Correct answer
```

The AI should explain the mistake using the available study material as the primary context.

## 31.3 Explanation Format

The explanation should be student-friendly and structured.

Suggested result:

```text
💡 Why was your answer wrong?

You chose A because ...

The correct answer is B because ...

📚 Key idea
...

🧠 Remember
...
```

Avoid overly long explanations unless the topic requires more detail.

The explanation should focus on the **specific misconception** behind the student's incorrect answer.

## 31.4 Similar Question

After explaining the mistake, provide an optional action:

```text
[ 🔄 Try a Similar Question ]
```

When clicked, generate one new question targeting the same concept or misconception.

Flow:

```text
Wrong answer
    |
    v
Explain My Mistake
    |
    v
Identify misconception
    |
    v
Try a Similar Question
    |
    v
Student answers again
```

The similar question should not simply duplicate the original question.

It should test the same concept using different wording or a different example.

## 31.5 Correct Answer Behavior

If the student answers correctly, do not show the mistake explanation action.

Instead show:

```text
✅ Correct!

[ Next Question ]
```

Optionally, a short explanation can be shown if the student requests one, but this is not required for the first implementation.

## 31.6 AI Provider Integration

The Explain My Mistake feature must use the **currently selected AI provider**.

Do not hard-code Gemini for this feature.

The flow must remain:

```text
Student
  |
  v
Streamlit UI
  |
  v
AI Service
  |
  v
Selected Provider
  |
  +--> Gemini
  |
  +--> Custom OpenAI-Compatible Provider
```

This is important because the provider abstraction should apply to every AI-powered feature in StudyMate AI.

## 31.7 Prompt Requirements

Create a dedicated prompt for mistake explanations.

Conceptually:

```text
You are an AI study tutor.

Analyze the student's incorrect answer using the provided study material.

Question:
...

Options:
A: ...
B: ...
C: ...
D: ...

Student's answer:
...

Correct answer:
...

Explain:
1. Why the student's answer is incorrect.
2. Why the correct answer is correct.
3. The key concept the student should remember.
4. A short memory tip when useful.

Use the provided study material as the primary source.
Do not invent information that is not supported by the material when the answer depends on it.
```

The exact prompt can be improved by the coding agent while preserving these requirements.

## 31.8 State Management

Preserve enough state for each interactive MCQ to know:

```text
Question
Options
Correct answer
Student answer
Explanation state
Related concept
```

Use Streamlit session state where appropriate.

Do not make the implementation unnecessarily complicated.

## 31.9 Preserve Quiz Progress

Generating an explanation must not reset the quiz.

The student should be able to:

```text
Answer Question 1
      |
      v
Get explanation
      |
      v
Try similar question
      |
      v
Continue quiz
```

The original quiz questions and progress should remain available during the session.

## 31.10 Error Handling

If the explanation request fails:

```text
⚠️ We couldn't generate an explanation right now.
Please try again or continue to the next question.
```

The original MCQ result must remain visible.

If the similar-question request fails:

```text
⚠️ We couldn't generate a similar question right now.
```

Do not lose quiz progress.

## 31.11 Acceptance Criteria — Explain My Mistake

- [ ] MCQs can be answered interactively.
- [ ] The student's selected answer is recorded.
- [ ] The system determines correct/incorrect status.
- [ ] Incorrect answers show an Explain My Mistake action.
- [ ] The explanation is generated only when requested.
- [ ] The explanation uses the selected AI provider.
- [ ] The explanation receives the question, options, student answer, correct answer, and relevant study context.
- [ ] The explanation identifies the likely misconception.
- [ ] The explanation is student-friendly.
- [ ] The student can request a similar question.
- [ ] The similar question targets the same concept.
- [ ] Quiz progress is preserved.
- [ ] Summary, Explanation, Flashcards, and other existing features are not broken.
- [ ] Provider abstraction is respected.
- [ ] API keys remain protected.

---

# 32. Updated Feature Roadmap

Implement the project in stages rather than attempting every advanced feature at once.

### Stage 1 — Current Upgrade

```text
Multi-provider system
        |
        v
Settings + Custom Provider
        |
        v
On-demand MCQs
```

### Stage 2 — First Outstanding Learning Feature

```text
Interactive MCQs
        |
        v
Explain My Mistake
        |
        v
Try a Similar Question
```

### Stage 3 — Future Adaptive Learning

```text
Quiz Performance
        |
        v
Adaptive Quiz Engine
        |
        v
Study Gap Detector
        |
        v
Personalized Study Plan
```

### Stage 4 — Future Advanced Features

Possible future additions:

- Exam Simulator
- Source-grounded answers
- Multi-document intelligence
- Past-paper analysis
- Knowledge map
- Socratic Tutor Mode
- Spaced-repetition flashcards
- Quick Revision Mode

Do not implement these future features unless explicitly requested.

---

# 33. Updated Final Product Vision

StudyMate AI should evolve from:

```text
Upload notes
    |
    v
Generate summary
```

toward:

```text
                    STUDYMATE AI
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
      LEARN           PRACTICE          REVIEW
        |                |                |
   Summary          Interactive MCQs   Flashcards
   Explanation           |                |
                         v                |
                  Explain Mistakes       |
                         |                |
                         v                |
                  Similar Questions      |
                         |                |
                         +-------+--------+
                                 |
                                 v
                         Better Understanding
```

The product should feel like an **AI learning assistant**, not just an AI content generator.

---

# 34. Updated Instructions to ZCode

In addition to the earlier instructions, implement the features in this specification in a controlled order.

Recommended order:

1. Inspect the existing project.
2. Implement/refactor the provider architecture.
3. Keep Gemini working.
4. Add the custom OpenAI-compatible provider.
5. Add Settings and provider management.
6. Add provider selection.
7. Change MCQs to on-demand generation.
8. Make MCQs interactive.
9. Add Explain My Mistake.
10. Add Try a Similar Question.
11. Test all workflows.
12. Verify that secrets are not staged.
13. Do not automatically commit or push to GitHub.

For the Explain My Mistake feature, do not create a completely separate AI architecture. Reuse the existing `AIService` and provider abstraction.

At the end, report:

- Files created.
- Files modified.
- Dependencies added.
- Provider features implemented.
- MCQ features implemented.
- Explain My Mistake features implemented.
- Tests performed.
- Remaining limitations.

Never include API keys or other secrets in the report.
