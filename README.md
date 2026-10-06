# Class Twin Voice Agent

> A tool-using AI agent that listens to a class question and responds in Ahmed's communication style, using the appropriate language, personal knowledge, memory, and voice output.

**Phase 1 — Brain + Voice**

The system is designed to answer questions in **English, Egyptian Arabic, or mixed Arabic/English**, while following a controlled decision policy to avoid guessing or speaking when it should stay silent.

---

## Overview

The Class Twin sits conceptually inside a class meeting:

```text
Instructor Audio
      │
      ▼
   Whisper STT
      │
      ▼
Question + Language + Quality
      │
      ▼
Decision Policy
      │
      ├── stay_silent
      ├── ask_to_repeat
      ├── defer
      └── answer
             │
             ▼
       Tool-Using Agent
             │
       ┌─────┼──────────┐
       ▼     ▼          ▼
     Notes Style      Profile
       │   Examples      │
       └─────┬──────────┘
             ▼
       Context + Memory
             │
             ▼
          Groq LLM
             │
             ▼
        Structured Reply
             │
             ▼
          Edge TTS
             │
             ▼
        Audio Response
```

Phase 1 is tested using **recorded audio** rather than a live meeting.

---

## What It Can Do

- 🎙️ Transcribe recorded class questions
- 🌍 Detect English, Egyptian Arabic, and mixed speech
- 🧠 Decide whether Ahmed should answer
- 🤫 Stay silent when a question is addressed to someone else
- 🔁 Ask for repetition when audio quality is too low
- 🛑 Defer when the topic is outside the available knowledge
- 🔎 Search the local knowledge pack
- 🗣️ Retrieve examples of Ahmed's own answering style
- 👤 Load Ahmed's communication profile
- 🧵 Maintain rolling conversation memory
- 🧩 Execute independent tools in parallel using a dependency graph
- 📦 Return a structured `TwinReply`
- 🔊 Generate spoken responses
- 📊 Measure latency for each pipeline stage
- 🧪 Run an automated 8-case evaluation suite

---

## Core Design

The project separates the system into four main stages:

```text
transcribe()
    ↓
decide()
    ↓
reply()
    ↓
speak()
```

This keeps the architecture modular and makes it possible to replace individual components later.

---

# 1. Speech-to-Text

Recorded audio is transcribed using:

**Groq Whisper — `whisper-large-v3-turbo`**

The transcription stage returns:

```python
{
    "text": "...",
    "language": "...",
    "detected_language": "mixed",
    "quality_score": 0.939,
    "segments": [...]
}
```

The quality score is used by the decision layer.

If the audio is too unclear, the system does not continue to answer.

Instead:

```text
Low Quality
    ↓
ask_to_repeat
```

---

# 2. Decision Policy

The agent does not automatically answer every question.

It chooses between four actions:

```text
answer
ask_to_repeat
defer
stay_silent
```

### Decision Flow

```text
                 Question
                    │
                    ▼
             Quality Check
                    │
          ┌─────────┴─────────┐
          │                   │
       Too Low              Good
          │                   │
          ▼                   ▼
 ask_to_repeat        Addressing Check
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
           Ahmed             Other           Class
              │               │               │
              ▼               ▼               ▼
          Knowledge       stay_silent     Topic Check
            Check                              │
                                      ┌────────┴────────┐
                                      ▼                 ▼
                                  Supported         Unsupported
                                      │                 │
                                      ▼                 ▼
                                   answer            defer
```

The system also uses an LLM scoring stage for cases that survive the cheap checks.

### Pruning

Candidate actions are scored and passed through:

```python
prune_and_select()
```

Only branches that clear the confidence threshold remain eligible.

For example:

```text
Candidates:

answer        0.97
ask_to_repeat 0.08
defer         0.05
stay_silent   0.02

After pruning:

Remaining:
answer

Pruned:
ask_to_repeat
defer
stay_silent
```

If no candidate clears the threshold, the system safely falls back to:

```text
Sorry, could you repeat the question?
```

The goal is to **avoid guessing**.

---

# 3. Tool-Using Agent

The system currently exposes four tools:

### `search_my_notes(query)`

Searches the local Phase 1 knowledge pack.

The current implementation uses a course glossary as the local knowledge source.

### `get_style_examples(question, language)`

Retrieves similar examples from Ahmed's Q&A dataset.

The retrieval layer currently uses:

```text
TF-IDF
Character n-grams
```

This was chosen as a lightweight CPU-friendly Phase 1 baseline.

### `get_profile()`

Loads Ahmed's communication profile, including:

- preferred names
- technical background
- language preferences
- tone
- answer length
- explanation style
- common openings
- response constraints

### `get_course_glossary(term)`

Looks up a specific AI/course concept from the local glossary.

---

# 4. Style Matching

The goal is not to make the model answer like a generic chatbot.

Instead, the system retrieves examples of how Ahmed has previously answered similar questions.

For example:

```text
Question
   │
   ▼
TF-IDF Retrieval
   │
   ├── Similar Example 1
   ├── Similar Example 2
   └── Similar Example 3
            │
            ▼
       LLM Context
            │
            ▼
       Ahmed-style Reply
```

The style dataset currently contains **17 real recorded Q&A examples**.

No synthetic recordings are used as replacements for missing examples.

---

# 5. Dependency Graph

The response planning stage uses Python's `graphlib.TopologicalSorter`.

The execution plan is:

```text
                prepare
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
  search_notes  style      profile
                   │
        └──────────┼──────────┘
                   ▼
           compose_context
```

The three independent branches:

```text
search_notes
style_examples
profile
```

can run in parallel.

This demonstrates the required dependency-graph execution rather than simply calling tools sequentially.

---

# 6. Conversation Memory

The agent maintains rolling conversation memory.

```python
RollingMemory(max_turns=5)
```

Each turn stores:

```text
question
reply
```

This allows follow-up questions such as:

> "Ahmed, and how is that different from what you said earlier?"

to use the previous conversation as context.

Memory can also be cleared from the Gradio interface.

---

# 7. Structured TwinReply

The final response is represented using Pydantic:

```python
class TwinReply(BaseModel):
    addressed_to_me: bool
    action: Literal[
        "answer",
        "ask_to_repeat",
        "defer",
        "stay_silent"
    ]
    language: Literal[
        "ar",
        "en",
        "mixed"
    ]
    reply_text: str
    confidence: float
    tools_used: list[str]
    sources: list[str]
```

Additional metadata tracks:

- decision reason
- pruned branches
- remaining branches
- follow-up status
- tool calls
- stage timings

This makes the agent's behavior inspectable instead of returning only raw text.

---

# 8. Language Behavior

The system supports:

### English

```text
Question → English
Answer   → English
```

### Egyptian Arabic

```text
Question → Egyptian Arabic
Answer   → Egyptian Arabic
```

### Mixed

```text
Question → Egyptian Arabic + English technical terms
Answer   → Egyptian Arabic + English technical terms
```

Technical terms such as:

```text
RAG
LLM
fine-tuning
embedding
vector database
agent
workflow
LangGraph
tool calling
```

are intentionally preserved in English when appropriate.

---

# 9. Voice Output

Phase 1 uses **Edge TTS** for speech generation.

Current voices:

```text
Arabic:
ar-EG-SalmaNeural

English:
en-US-AndrewNeural
```

Mixed responses use the Arabic voice.

The generated response is saved as an audio file and displayed in the Gradio interface.

### Important

This is **not voice cloning**.

Phase 1 focuses on validating:

```text
STT
+
Decision Policy
+
Tools
+
Style Retrieval
+
Memory
+
LLM Response
+
Speech Output
```

Actual voice cloning is planned for Phase 2.

---

# 10. Gradio Demo

The project includes a Gradio interface for testing the complete pipeline.

The interface allows:

```text
Record / Upload Audio
        │
        ▼
     Transcribe
        │
        ▼
Show Transcript
        │
        ▼
Show Decision
        │
        ▼
Show Pruned Branches
        │
        ▼
Show Tool Calls
        │
        ▼
Show TwinReply JSON
        │
        ▼
Play Generated Audio
        │
        ▼
Show Stage Timings
```

It also includes a memory reset button.

---

# 11. Evaluation

The Phase 1 test suite contains eight required scenarios.

| Test | Scenario | Expected | Result |
|---|---|---|---|
| T01 | English addressed question | `answer` | ✅ PASS |
| T02 | Egyptian Arabic addressed question | `answer` | ✅ PASS |
| T03 | Mixed-language question | `answer` | ✅ PASS |
| T04 | Question addressed to Sara | `stay_silent` | ✅ PASS |
| T05 | Open question to the class | `defer` | ✅ PASS |
| T06 | Follow-up using memory | `answer` | ✅ PASS |
| T07 | Unsupported Kubernetes question | `defer` | ✅ PASS |
| T08 | Low-quality / unclear audio | `ask_to_repeat` | ✅ PASS |

### Result

```text
Tests     : 8
Passed    : 8
Failed    : 0
Accuracy  : 100%
```

This represents performance on the defined Phase 1 test set, not a claim of perfect real-world accuracy.

Detailed results are stored in:

```text
results/test_results.json
results/test_results.md
```

---

# 12. Example End-to-End Run

Example input:

```text
What is the difference between RAG and fine-tuning?
```

Pipeline:

```text
Audio
 ↓
Whisper
 ↓
Question detected
 ↓
Decision → answer
 ↓
Search knowledge
 ↓
Retrieve similar style examples
 ↓
Load profile
 ↓
Use previous memory if relevant
 ↓
Groq LLM
 ↓
TwinReply
 ↓
Edge TTS
 ↓
Audio response
```

Example response:

> بص، الفرق الأساسي إن الـRAG بيخلي الـmodel يجيب المعلومات وقت الـinference من مصدر knowledge خارجي، بينما الـfine-tuning بيغير الـmodel نفسه عن طريق تدريب إضافي على data جديدة.

---

# 13. Performance Tracking

The pipeline records timing for:

```text
STT
Decision
Decision LLM
Tool + Graph execution
Answer LLM
Speech
Total
```

Example Phase 1 run:

```text
STT                  1.020s
Decision              1.596s
Decision LLM          1.595s
Tools + Graph         0.076s
Answer LLM            1.394s
Speech                5.625s
Total                 9.714s
```

The largest current latency comes from speech generation.

This is expected for a Phase 1 prototype using Edge TTS.

---

# 14. Project Structure

```text
Class-Twin-Voice-Agent/
│
├── app/
│   ├── decision.py
│   ├── decision_llm.py
│   ├── gradio_app.py
│   ├── memory.py
│   ├── pipeline.py
│   ├── reply_generator.py
│   ├── reply_graph.py
│   ├── run_tests.py
│   ├── speak.py
│   ├── style_retriever.py
│   ├── tools.py
│   ├── transcribe.py
│   └── build_results_report.py
│
├── results/
│   ├── audio/
│   ├── transcripts/
│   ├── test_results.json
│   └── test_results.md
│
├── tests/
│
├── twin_data/
│   ├── profile.json
│   ├── style_examples.jsonl
│   ├── knowledge/
│   └── voice/
│
├── main.py
├── pyproject.toml
├── uv.lock
├── README.md
└── LICENSE
```

---

# 15. Setup

Requires:

```text
Python 3.11+
uv
Groq API key
```

Install dependencies:

```bash
uv sync
```

Create `.env`:

```env
GROQ_API_KEY=your_groq_api_key
```

Do not commit `.env`.

---

# 16. Run the Pipeline

Test the complete pipeline:

```bash
uv run python -m app.pipeline
```

Run the decision layer:

```bash
uv run python -m app.decision_llm
```

Run style retrieval:

```bash
uv run python -m app.style_retriever
```

Run the complete test suite:

```bash
uv run python -m app.run_tests
```

Generate the results report:

```bash
uv run python -m app.build_results_report
```

Launch the Gradio demo:

```bash
uv run python -m app.gradio_app
```

---

# 17. Decisions & Limitations

## Why TF-IDF instead of embeddings?

The assignment suggests an embedding-based retrieval system such as:

```text
intfloat/multilingual-e5-small
```

For this Phase 1 implementation, TF-IDF character n-gram retrieval was selected as a lightweight CPU-friendly baseline.

The development environment is an Intel Mac, where the required PyTorch/Sentence-Transformers dependency stack did not provide a suitable setup.

The retrieval layer is therefore intentionally simple and replaceable.

---

## Why Edge TTS?

Edge TTS provides a fast and accessible way to validate the speech-output pipeline.

It does not reproduce Ahmed's real voice.

Actual voice cloning is intentionally deferred to Phase 2.

---

## One Known Limitation

A major limitation is that the system's knowledge base is currently small.

The Phase 1 knowledge source is a local course glossary plus Ahmed's Q&A/style examples.

Therefore, questions outside this knowledge scope may be deferred even when a general-purpose LLM could answer them.

This is intentional.

The agent prioritizes:

```text
Grounded answer
      >
Safe defer
      >
Guessing
```

---

# 18. Responsible Use

This project is intended only as a personal AI twin prototype.

The system should:

- Clone/use only the owner's voice with consent
- Be clearly identified as an AI twin
- Be used only when the instructor knows about it
- Never be used for attendance
- Never be used during quizzes or exams
- Never attend a class in place of the student
- Keep a kill switch for immediately muting the system
- Keep personal voice recordings private

Voice recordings should **not** be committed to a public repository.

---

# 19. Phase 2 Roadmap

Phase 2 moves from recorded audio to a live meeting environment.

Planned components:

```text
Live Meeting Audio
        │
        ▼
Virtual Audio Device
        │
        ▼
Silero VAD
        │
        ▼
Whisper
        │
        ▼
Decision + Agent Loop
        │
        ▼
Tools / Memory / Re-planning
        │
        ▼
XTTS-v2
        │
        ▼
Virtual Microphone
        │
        ▼
Meeting
```

Planned improvements:

- Live Zoom / Google Meet audio
- Virtual microphone integration
- Silero VAD
- XTTS-v2 voice cloning
- Faster response latency
- Tool failure handling
- Agent re-planning
- Human approval / automatic mode
- One-key kill switch

---

# Phase 1 Status

```text
STT                         ✅
Language detection          ✅
Quality detection           ✅
Decision policy             ✅
Decision LLM scoring        ✅
Branch pruning              ✅
Tool calling                ✅
Knowledge retrieval         ✅
Style retrieval             ✅
Dependency graph            ✅
Rolling memory              ✅
Structured TwinReply        ✅
Speech output               ✅
Gradio demo                 ✅
8-case evaluation           ✅
Results report              ✅
Live meeting                ⏳ Phase 2
Voice cloning               ⏳ Phase 2
```

---

## Final Goal

The long-term goal is not simply to build a chatbot that sounds like Ahmed.

It is to build a controlled agent that can:

```text
Listen
  ↓
Understand
  ↓
Decide whether to respond
  ↓
Retrieve relevant personal knowledge
  ↓
Match Ahmed's communication style
  ↓
Use conversation memory
  ↓
Generate a grounded answer
  ↓
Speak
```

while remaining **transparent, controllable, and safe to use in a classroom environment**.