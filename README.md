# 🤖 StudyMate AI

An AI-powered study assistant that turns pasted notes and lecture PDFs into
summaries, simple explanations, and flashcards — then quizzes you on demand,
explains your mistakes, and helps you practice weak concepts with similar
questions. Works with Google Gemini (default) or any OpenAI-compatible API.

## ✨ Features

- 📖 **Summary** — a concise overview of your material
- 💡 **Simple Explanation** — key concepts in student-friendly language
- 🗂️ **Flashcards** — question-and-answer cards for active recall
- 📝 **On-demand MCQs** — practice questions are generated only when you
  click **Generate MCQs**, never bundled into the initial study material
- 💡 **Explain My Mistake** — when you answer wrong, StudyMate explains the
  specific misconception behind your answer using your own study material
- 🔄 **Try a Similar Question** — after a mistake, practice the same concept
  with a fresh question (different wording, different example)
- ⚙️ **Multi-provider AI** — Gemini works out of the box; connect any
  OpenAI-compatible API with its own base URL, API key, and model

## 🏛️ Architecture

```text
User
 ↓
Streamlit UI (Study workspace / Settings)
 ↓
AI Service (prompts + orchestration)
 ↓
Provider Manager (selection + configuration)
 ↓
Provider Interface
 ├── Gemini Provider (google-genai SDK)
 └── OpenAI-Compatible Provider (chat/completions over HTTP)
 ↓
Summary · Explanation · Flashcards
        └── (on click) MCQs → mistake explanations → similar questions
```

The UI never talks to a provider SDK directly. Every AI-powered feature —
including mistake explanations and similar questions — goes through the same
provider layer, so switching providers or adding new ones never rewrites the
app.

## 📁 Project Structure

```text
studymate-ai/
├── app.py                      # Streamlit UI (study + settings)
├── config/settings.py          # environment + app constants
├── providers/
│   ├── base.py                 # AIProvider interface + friendly errors
│   ├── gemini_provider.py      # Gemini via google-genai
│   └── openai_compatible_provider.py
├── services/
│   ├── ai_service.py           # prompts + all generation flows
│   └── provider_manager.py     # provider config, selection, factory
├── utils/
│   ├── pdf_utils.py            # pypdf text extraction
│   └── response_parser.py      # robust JSON/MCQ parsing
├── requirements.txt
├── README.md
├── .gitignore
├── .env                        # GEMINI_API_KEY (never commit)
└── providers.json              # custom providers (auto-created, gitignored)
```

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Language | Python |
| UI | Streamlit |
| Default AI | Google Gemini (`gemini-3.5-flash`, configurable in Settings) |
| Custom AI | Any OpenAI-compatible chat API (HTTP) |
| PDF Processing | PyPDF |
| Environment Management | python-dotenv |

## 🚀 Setup

1. **Create a virtual environment** (if you haven't already):

   ```bash
   python -m venv .venv
   ```

   Activate it:

   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`
   - Windows (Git Bash): `source .venv/Scripts/activate`
   - macOS/Linux: `source .venv/bin/activate`

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Add your Gemini API key** (optional but recommended — Gemini is the
   default provider):

   - Get a free key from [Google AI Studio](https://aistudio.google.com/apikey).
   - Open the `.env` file and set:

   ```text
   GEMINI_API_KEY=your-real-api-key
   ```

   The `.env` file is gitignored — never commit or share your key.

4. **Run the app**:

   ```bash
   streamlit run app.py
   ```

   The app opens automatically in your browser (usually `http://localhost:8501`).

## ⚙️ Custom AI Providers

1. Open the **⚙️ Settings** page.
2. Under **➕ Add Provider**, enter a name, the provider's API base URL
   (e.g. `https://example.com/v1`), your API key, and the model name.
3. Click **🔍 Test Connection** — a tiny request verifies the configuration.
4. Click **💾 Save Provider**, then select it in the sidebar or Settings.

Custom providers are stored in `providers.json` in the project root, which is
gitignored. **Limitation:** keys in that file are stored in plain text —
fine for a local student project, but not production-grade secret storage.
Don't sync or share that file.

## 📖 Usage

1. Choose **📚 Paste Notes** and paste your notes, or **📄 Upload PDF** for a
   lecture or study PDF.
2. Click **✨ Generate study resources** — you get Summary, Simple
   Explanation, and Flashcards. No MCQs yet.
3. When you're ready, click **📝 Generate MCQs** in the Test Yourself section.
4. Answer each question and click **Submit answer**.
5. Wrong answer? Click **💡 Explain My Mistake** for a grounded explanation of
   the misconception, then **🔄 Try a Similar Question** to practice the same
   concept again.
6. Track your progress with the live score, and reset answers anytime.

## ⚠️ Limitations

- AI-generated content can occasionally be incorrect — always cross-check
  with your original material.
- Scanned/image-only PDFs contain no extractable text.
- Very large documents are truncated to fit the model's context window.
- Generation depends on your selected provider's availability and limits.
- Custom provider API keys are stored locally in plain text
  (`providers.json`) — not production-grade secret management.
- MCQ answers are checked by exact text match; occasional provider quirks
  (e.g. cased differently) are normalized where possible.

## 🔮 Future Improvements

- Quiz performance tracking and an adaptive quiz engine
- Study gap detection and personalized study plans
- Spaced-repetition flashcards
- More provider types (Anthropic, OpenRouter, local models)
- Multi-document support and past-paper analysis
