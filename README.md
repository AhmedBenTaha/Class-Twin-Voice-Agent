# Class Twin Voice Agent

> A tool-using AI agent that listens to class questions and responds in Ahmed's communication style, using the appropriate language, knowledge, conversation memory, and voice output.

**Phase 1 — Brain + Voice**

The Class Twin is designed to answer questions in **English, Egyptian Arabic, or mixed Arabic/English**, while following a controlled decision policy that prevents unnecessary guessing or speaking when the question should be ignored or deferred.

---

## Overview

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
       ┌──────┼───────────┐
       ▼      ▼           ▼
     Notes   Style      Profile
              │           │
       └──────┼───────────┘
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

Phase 1 is evaluated using **recorded audio** rather than a live meeting.

---

## What It Can Do

- 🎙️ Transcribe recorded class questions
- 🌍 Handle English, Egyptian Arabic, and mixed speech
- 🧠 Decide whether Ahmed should answer
- 🤫 Stay silent when a question is addressed to someone else
- 🔁 Ask for repetition when audio quality is too low
- 🛑 Defer questions outside the available knowledge scope
- 🔎 Search the local knowledge pack
- 🗣️ Retrieve examples of Ahmed's answering style
- 👤 Load Ahmed's communication profile
- 🧵 Maintain rolling conversation memory
- 🧩 Execute independent tool branches through a dependency graph
- 📦 Return a structured `TwinReply`
- 🔊 Generate spoken responses
- 📊 Track latency across pipeline stages
- 🧪 Run an automated 8-case evaluation suite

---

# Architecture

The main pipeline is intentionally modular:

```text
transcribe()
     ↓
decide()
     ↓
reply()
     ↓
speak()
```

At a higher level:

```text
Audio
  ↓
Speech-to-Text
  ↓
Decision Layer
  ↓
Agent + Tools
  ↓
Context + Memory
  ↓
LLM
  ↓
Structured Reply
  ↓
Text-to-Speech
```

Each stage can be replaced independently without redesigning the complete system.

---

# 1. Speech-to-Text

Recorded audio is transcribed using:

**Groq Whisper — `whisper-large-v3-turbo`**

The transcription stage returns structured information:

```python
{
    "text": "...",
    "language": "...",
    "detected_language": "mixed",
    "quality_score": 0.939,
    "segments": [...]
}
```

The system uses the transcription quality score as part of the decision process.

If the audio is too unclear:

```text
Low Quality
     ↓
ask_to_repeat
```

The agent does not attempt to generate an answer from unreliable input.

---

# 2. Decision Policy

The Class Twin does not automatically answer every question.

It chooses exactly one of four actions:

```text
answer
ask_to_repeat
defer
stay_silent
```

## Decision Flow

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
      ask_to_repeat       Addressing Check
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
           Ahmed              Other             Class
              │                 │                 │
              ▼                 ▼                 ▼
        Knowledge Check    stay_silent       Topic Check
                                                   │
                                           ┌───────┴───────┐
                                           ▼               ▼
                                       Supported      Unsupported
                                           │               │
                                           ▼               ▼
                                        answer          defer
```

The system first performs cheap deterministic checks.

Only questions that survive these checks are passed to the LLM-based decision scoring layer.

This keeps the decision process both **safer and more efficient**.

---

## LLM Decision Scoring

For eligible questions, the decision layer asks the LLM to score the possible actions:

```python
{
    "answer": 0.97,
    "defer": 0.05,
    "ask_to_repeat": 0.08,
    "stay_silent": 0.02
}
```

The scores are then processed by:

```python
prune_and_select()
```

Only candidates above the confidence threshold remain eligible.

Example:

```text
Candidates

answer          0.97
ask_to_repeat   0.08
defer           0.05
stay_silent     0.02

        ↓ pruning

Remaining

answer

Pruned

ask_to_repeat
defer
stay_silent
```

If no action clears the threshold, the system safely falls back to:

```text
ask_to_repeat
```

The design prioritizes **safe behavior over guessing**.

---

# 3. Tool-Using Agent

The agent currently exposes four tools.

## `search_my_notes(query)`

Searches the local Phase 1 knowledge source.

The current implementation uses a **course glossary** as the local knowledge pack.

This keeps the Phase 1 system grounded in a controlled set of available information.

---

## `get_style_examples(question, language)`

Retrieves semantically similar examples from Ahmed's Q&A dataset.

The current retrieval stack is:

```text
FastEmbed
    ↓
Multilingual MiniLM
    ↓
384-dimensional embeddings
    ↓
ChromaDB
    ↓
Cosine similarity search
```

---

## `get_profile()`

Loads Ahmed's communication profile, including:

- preferred names
- technical background
- language preferences
- tone
- answer length
- explanation style
- common openings
- response constraints

---

## `get_course_glossary(term)`

Looks up a specific AI or course concept from the local glossary.

---

# 4. Style Retrieval

The goal is not simply to ask an LLM to "sound like Ahmed."

Instead, the system retrieves examples of how Ahmed has actually answered similar questions and provides them as context to the generation model.

```text
                  Question
                     │
                     ▼
              FastEmbed Model
                     │
                     ▼
            384-dim Embedding
                     │
                     ▼
                 ChromaDB
                     │
            ┌────────┼────────┐
            ▼        ▼        ▼
         Example 1 Example 2 Example 3
            │        │        │
            └────────┼────────┘
                     ▼
                LLM Context
                     │
                     ▼
             Ahmed-style Reply
```

### Embedding Model

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

The model is accessed through **FastEmbed**, allowing the project to use ONNX-based inference without depending on the full PyTorch `sentence-transformers` stack.

Embedding dimension:

```text
384
```

The model supports multilingual retrieval, which is useful for:

```text
English
Egyptian Arabic
Mixed Arabic/English
```

The retrieval layer intentionally does not apply a hard language filter. Semantic similarity determines which examples are most relevant.

---

## Style Dataset

The current style dataset contains:

```text
17 real recorded Q&A examples
```

These examples cover topics such as:

- RAG
- Fine-tuning
- AI Agents
- Workflows
- LangGraph
- Tool Calling
- Hallucination
- Vector Databases
- Embeddings
- Decision Tree Pruning

No synthetic recordings are used as replacements for missing examples.

---

# 5. Dependency Graph

The response planning stage uses Python's:

```python
graphlib.TopologicalSorter
```

The execution plan is:

```text
                    prepare
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    search_notes     style       profile
          │            │            │
          └────────────┼────────────┘
                       ▼
                compose_context
```

The three branches:

```text
search_notes
style_examples
profile
```

are independent and can be executed in parallel.

This demonstrates a real dependency-graph execution model instead of simply calling tools sequentially.

---

# 6. Conversation Memory

The agent maintains rolling conversation memory using:

```python
RollingMemory(max_turns=5)
```

Each turn stores:

```text
question
reply
```

For example:

```text
User:
Ahmed, what's the difference between RAG and fine-tuning?

Twin:
بص، الفرق الأساسي إن الـRAG...
```

A follow-up question can then refer to that context:

```text
Ahmed, and how is that different from what you said earlier?
```

The memory allows the agent to understand that the new question refers to the previous topic.

Memory can also be cleared from the Gradio interface.

---

# 7. Structured `TwinReply`

The final agent output is represented using Pydantic.

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

```text
decision_reason
pruned_branches
remaining_branches
follow_up
tool_calls
timings
```

This makes the agent's behavior inspectable rather than returning only raw generated text.

---

# 8. Language Behavior

The Class Twin supports three response modes.

## English

```text
Question → English
Answer   → English
```

## Egyptian Arabic

```text
Question → Egyptian Arabic
Answer   → Egyptian Arabic
```

## Mixed

```text
Question → Egyptian Arabic + English technical terms
Answer   → Egyptian Arabic + English technical terms
```

Technical terms are intentionally preserved in English when appropriate:

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

This reflects Ahmed's normal technical communication style.

---

# 9. Voice Output

Phase 1 uses:

**Edge TTS**

Current voices include:

```text
Arabic:
ar-EG-SalmaNeural

English:
en-US-AndrewNeural
```

Mixed responses use the Arabic voice.

The generated audio is saved and displayed through the Gradio interface.

## Important

**Edge TTS is not voice cloning.**

Phase 1 is focused on validating the complete agent loop:

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

Actual voice cloning is planned for Phase 2 using a GPU-based voice cloning solution.

---

# 10. Gradio Demo

The project includes a Gradio interface for testing the complete Phase 1 pipeline.

The interface supports:

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

It also provides a memory reset control.

---

# 11. Evaluation

The Phase 1 test suite contains eight defined scenarios.

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

### Current Result

```text
Tests     : 8
Passed    : 8
Failed    : 0
Accuracy  : 100%
```

This is **100% on the predefined Phase 1 test suite**, not a claim of perfect real-world accuracy.

Detailed results are stored in:

```text
results/test_results.json
results/test_results.md
```

---

# 12. Example End-to-End Run

Example question:

```text
What is the difference between RAG and fine-tuning?
```

The complete flow is:

```text
Audio
  ↓
Whisper STT
  ↓
Question + Language + Quality
  ↓
Decision → answer
  ↓
Search Knowledge
  ↓
Retrieve Similar Style Examples
  ↓
Load Profile
  ↓
Use Conversation Memory
  ↓
Groq LLM
  ↓
TwinReply
  ↓
Edge TTS
  ↓
Audio Response
```

Example style-matched response:

> بص، الفرق الأساسي إن الـRAG بيخلي الـmodel يجيب المعلومات وقت الـinference من مصدر knowledge خارجي، بينما الـfine-tuning بيغير الـmodel نفسه عن طريق تدريب إضافي على data جديدة.

---

# 13. Performance Tracking

The pipeline records timing for each major stage:

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

The largest latency in this example comes from speech generation.

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

Local runtime data such as the ChromaDB index and private voice recordings are excluded from the public repository.

---

# 15. Setup

Requirements:

```text
Python 3.11+
uv
Groq API key
```

Install dependencies:

```bash
uv sync
```

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

Never commit `.env`.

---

# 16. Run the Project

Run the complete Phase 1 pipeline:

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

# 17. Technical Decisions & Limitations

## Why FastEmbed + ChromaDB?

The assignment suggests embedding-based retrieval using models such as:

```text
intfloat/multilingual-e5-small
```

The current implementation uses:

```text
FastEmbed
+
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
+
ChromaDB
```

instead.

The main reason is the development environment.

The project is developed on an **Intel-based macOS machine**, where the standard PyTorch/Sentence-Transformers dependency stack can be difficult to install with compatible native wheels.

FastEmbed provides an ONNX-based alternative that works well for this CPU-based Phase 1 prototype.

Current embedding dimension:

```text
384
```

This keeps semantic retrieval lightweight while still supporting English, Arabic, and mixed-language questions.

---

## Why ChromaDB?

ChromaDB provides a simple persistent vector store for the style examples.

The local collection stores:

```text
Question
Embedding
Answer
Language
Audio reference
```

The collection is automatically rebuilt from:

```text
twin_data/style_examples.jsonl
```

when necessary.

The local ChromaDB directory is ignored by Git and is not part of the public repository.

---

## Why Edge TTS?

Edge TTS provides an accessible way to validate the speech-output stage without requiring a local voice-cloning model.

It does **not** reproduce Ahmed's real voice.

Actual voice cloning is intentionally deferred to Phase 2.

---

## Small Knowledge Base

The current Phase 1 knowledge source is intentionally limited.

It currently consists primarily of:

```text
Course glossary
+
Ahmed's Q&A/style examples
```

It is not intended to represent a complete personal knowledge base.

Therefore, questions outside the supported knowledge scope may be deferred even when a general-purpose LLM could answer them.

This is intentional.

The system prioritizes:

```text
Grounded answer
      >
Safe defer
      >
Guessing
```

---

# 18. Responsible Use

This project is intended as a personal AI twin prototype.

The system should:

- Use only the owner's voice with explicit consent
- Clearly identify itself as an AI twin
- Be used only when the instructor knows about it
- Never be used for attendance
- Never be used during quizzes or exams
- Never attend a class in place of the student
- Keep a kill switch for immediately muting the system
- Keep personal voice recordings private

Voice recordings should **never be committed to a public repository**.

The AI twin should be treated as an assistant, not as a replacement for the student.

---

# 19. Phase 2 Roadmap

Phase 2 moves from recorded audio to a live meeting environment.

Planned architecture:

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

Planned improvements include:

- Live Zoom / Google Meet audio
- Virtual microphone integration
- Silero VAD
- XTTS-v2 voice cloning
- Lower response latency
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
ChromaDB                    ✅
FastEmbed                   ✅
Multilingual embeddings     ✅
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

# Final Goal

The long-term goal is not simply to build a chatbot that sounds like Ahmed.

It is to build a controlled agent that can:

```text
Listen
  ↓
Understand
  ↓
Decide whether to respond
  ↓
Retrieve relevant knowledge
  ↓
Retrieve Ahmed-style examples
  ↓
Use conversation memory
  ↓
Generate a grounded answer
  ↓
Speak
```

while remaining:

```text
Transparent
Controllable
Grounded
Safe
```

for use in a classroom environment.

---

## Phase 1 in One Sentence

> **A tool-using, memory-aware AI agent that listens to a class question, decides whether Ahmed should respond, retrieves relevant knowledge and Ahmed-style examples, generates a grounded answer, and converts it into speech.**