from __future__ import annotations

import json
import os
import time
from typing import Literal

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

from app.decision_llm import decide_with_llm
from app.reply_graph import build_reply_plan
from app.memory import RollingMemory


# ============================================================
# Configuration
# ============================================================

load_dotenv()

MODEL = "openai/gpt-oss-120b"

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

memory = RollingMemory(max_turns=5)


# ============================================================
# Twin Reply Schema
# ============================================================

class TwinReply(BaseModel):
    addressed_to_me: bool

    action: Literal[
        "answer",
        "ask_to_repeat",
        "defer",
        "stay_silent",
    ]

    language: Literal[
        "ar",
        "en",
        "mixed",
    ]

    reply_text: str

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    tools_used: list[str]

    sources: list[str]

    # Debug / demo information
    decision_reason: str = ""

    pruned_branches: list[str] = []

    remaining_branches: list[str] = []

    follow_up: bool = False

    tool_calls: list[dict] = []

    timings: dict[str, float] = {}


# ============================================================
# Language Detection
# ============================================================

def detect_language(
    question: str,
) -> Literal["ar", "en", "mixed"]:

    arabic = sum(
        "\u0600" <= char <= "\u06ff"
        for char in question
    )

    latin = sum(
        char.isascii() and char.isalpha()
        for char in question
    )

    if arabic > 0 and latin > 0:
        return "mixed"

    if arabic > latin:
        return "ar"

    return "en"


# ============================================================
# Follow-up Detection
# ============================================================

def is_follow_up(question: str) -> bool:

    text = question.lower().strip()

    follow_up_patterns = [
        # English
        "earlier",
        "before",
        "what you said",
        "what you mentioned",
        "what you explained",
        "the previous",
        "previous answer",
        "previous explanation",
        "different from what",
        "and how",
        "and what about",
        "how is that different",
        "how does that",
        "what about that",
        "that one",
        "this one",

        # Egyptian Arabic
        "اللي فات",
        "قبل كده",
        "اللي قولته",
        "اللي قلته",
        "اللي شرحته",
        "الإجابة اللي فاتت",
        "الشرح اللي فات",
        "ده",
        "دي",
        "وده",
        "ودي",
        "طب و",
        "طيب و",
        "وكمان",
    ]

    return any(
        pattern in text
        for pattern in follow_up_patterns
    )


# ============================================================
# Prompt Construction
# ============================================================

def build_prompt(
    question: str,
    language: str,
    context: dict,
    memory_context: list[dict[str, str]] | None = None,
) -> str:

    profile = context["profile"]
    notes = context["notes"]
    style_examples = context["style_examples"]

    memory_context = memory_context or []

    return f"""
You are generating a Class Twin reply for Ahmed Elsayed Taha.

Your job is to answer the instructor in Ahmed's natural
communication style.

============================================================
CURRENT QUESTION
============================================================

{question}

============================================================
LANGUAGE
============================================================

{language}

============================================================
PREVIOUS CONVERSATION
============================================================

{json.dumps(
    memory_context,
    ensure_ascii=False,
    indent=2,
)}

============================================================
AHMED'S PROFILE
============================================================

{json.dumps(
    profile,
    ensure_ascii=False,
    indent=2,
)}

============================================================
AVAILABLE KNOWLEDGE
============================================================

{json.dumps(
    notes,
    ensure_ascii=False,
    indent=2,
)}

============================================================
STYLE EXAMPLES
============================================================

{json.dumps(
    style_examples,
    ensure_ascii=False,
    indent=2,
)}

============================================================
RULES
============================================================

1. Use ONLY the supplied knowledge and previous conversation.

2. Never invent personal experience.

3. Never invent facts that are not supported by the
   supplied knowledge or previous conversation.

4. Keep the answer short to medium.

5. Be casual, clear, direct and technical.

6. Start with a simple explanation, then give the technical
   details when useful.

7. Preserve English technical terms such as:
   RAG, LLM, embedding, vector database, fine-tuning,
   agent, workflow, tool calling, LangGraph, etc.

============================================================
LANGUAGE RULES — VERY IMPORTANT
============================================================

8. If LANGUAGE is "en":

   - Write the ENTIRE answer in English.
   - Do NOT use Arabic words.
   - Do NOT use Egyptian Arabic openings such as:
     "بص", "يعني", "ببساطة", "آه", "خلينا".
   - Technical terms should remain in English.

9. If LANGUAGE is "ar":

   - Write in Egyptian Arabic.
   - Keep technical AI/software terms in English.
   - Do not unnecessarily translate technical terms.

10. If LANGUAGE is "mixed":

   - Use Egyptian Arabic as the main language.
   - Keep technical AI/software terms in English.

11. The requested LANGUAGE has priority over the
    style examples.

12. Match Ahmed's communication style:
    - casual
    - clear
    - direct
    - technical
    - simple explanation first
    - technical details second

13. Do not over-explain.

14. Use PREVIOUS CONVERSATION to resolve follow-up questions.

15. If the question contains references such as:
    "that", "this", "earlier", "before",
    "what you said", "what you mentioned",
    or their Arabic equivalents,
    use the previous conversation to understand
    what the user is referring to.

16. If the previous conversation does not contain
    enough information to answer a follow-up,
    do NOT guess.

17. If the available knowledge does not support an answer,
    do NOT fabricate an answer.

18. Do not claim Ahmed personally used a technology,
    completed an assignment, or had an experience unless
    that information is explicitly available.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

{{
    "reply_text": "the final answer",
    "confidence": 0.0,
    "sources": ["source1", "source2"]
}}
"""


# ============================================================
# LLM Answer Generation
# ============================================================

def generate_answer(
    question: str,
    language: str,
    context: dict,
    memory_context: list[dict[str, str]] | None = None,
) -> tuple[TwinReply, float]:

    prompt = build_prompt(
        question=question,
        language=language,
        context=context,
        memory_context=memory_context,
    )

    start = time.perf_counter()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate grounded Class Twin answers "
                    "for Ahmed. Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    llm_seconds = round(
        time.perf_counter() - start,
        3,
    )

    raw = response.choices[0].message.content.strip()

    data = json.loads(raw)

    answer = TwinReply(
        addressed_to_me=True,
        action="answer",
        language=language,
        reply_text=data["reply_text"],
        confidence=float(data["confidence"]),
        tools_used=[
            "search_my_notes",
            "get_style_examples",
            "get_profile",
        ],
        sources=data.get("sources", []),
    )

    return answer, llm_seconds


# ============================================================
# Main Reply Pipeline
# ============================================================

def reply(
    question: str,
    quality_score: float = 1.0,
) -> TwinReply:

    # --------------------------------------------------------
    # 1. Detect language
    # --------------------------------------------------------

    language = detect_language(question)

    # --------------------------------------------------------
    # 2. Detect follow-up
    # --------------------------------------------------------

    follow_up = is_follow_up(question)

    # --------------------------------------------------------
    # 3. Read previous memory
    # --------------------------------------------------------

    previous_memory = memory.get_context()

    has_memory = not memory.is_empty()

    # --------------------------------------------------------
    # 4. Build decision input
    # --------------------------------------------------------

    decision_question = question

    if follow_up and has_memory:

        decision_question = f"""
Current question:
{question}

Previous conversation:
{json.dumps(
    previous_memory,
    ensure_ascii=False,
    indent=2,
)}

This may be a follow-up question.

Use the previous conversation to understand
what the current question refers to.

Do not invent information that is not present
in the previous conversation.
"""

    # --------------------------------------------------------
    # 5. Decision Tree
    # --------------------------------------------------------

    decision_start = time.perf_counter()

    decision = decide_with_llm(
        {
            "text": decision_question,
            "quality_score": quality_score,
        },
        has_memory=bool(previous_memory),
    )

    decision_seconds = round(
        time.perf_counter() - decision_start,
        3,
    )

    # --------------------------------------------------------
    # Common debug data
    # --------------------------------------------------------

    base_debug = {
        "decision_reason": decision.reason,
        "pruned_branches": decision.pruned_branches,
        "remaining_branches": decision.remaining_branches,
        "follow_up": follow_up,
        "timings": {
            "decision_total_seconds": decision_seconds,
            "decision_llm_seconds": decision.decision_llm_seconds,
        },
    }

    # --------------------------------------------------------
    # 6. Handle STAY SILENT
    # --------------------------------------------------------

    if decision.action == "stay_silent":

        return TwinReply(
            addressed_to_me=decision.addressed_to_me,
            action="stay_silent",
            language=language,
            reply_text="",
            confidence=decision.confidence,
            tools_used=[],
            sources=[],
            **base_debug,
        )

    # --------------------------------------------------------
    # 7. Handle ASK TO REPEAT
    # --------------------------------------------------------

    if decision.action == "ask_to_repeat":

        if language == "en":

            text = (
                "Sorry, could you repeat the question?"
            )

        elif language == "ar":

            text = (
                "معلش، ممكن تكرر السؤال؟"
            )

        else:

            text = (
                "معلش، ممكن تكرر السؤال؟"
            )

        return TwinReply(
            addressed_to_me=decision.addressed_to_me,
            action="ask_to_repeat",
            language=language,
            reply_text=text,
            confidence=decision.confidence,
            tools_used=[],
            sources=[],
            **base_debug,
        )

    # --------------------------------------------------------
    # 8. Handle DEFER
    # --------------------------------------------------------

    if decision.action == "defer":

        if language == "en":

            text = (
                "I'm not sure about that from the "
                "information I have."
            )

        else:

            text = (
                "مش متأكد من النقطة دي بناءً على "
                "المعلومات اللي عندي."
            )

        return TwinReply(
            addressed_to_me=decision.addressed_to_me,
            action="defer",
            language=language,
            reply_text=text,
            confidence=decision.confidence,
            tools_used=[],
            sources=[],
            **base_debug,
        )

    # --------------------------------------------------------
    # 9. ANSWER BRANCH
    # --------------------------------------------------------

    plan_start = time.perf_counter()

    plan = build_reply_plan(
        question=question,
        language=language,
    )

    plan_seconds = round(
        time.perf_counter() - plan_start,
        3,
    )

    context = plan["tool_results"]["compose_context"]

    # --------------------------------------------------------
    # 10. Generate grounded answer
    # --------------------------------------------------------

    answer, llm_seconds = generate_answer(
        question=question,
        language=language,
        context=context,
        memory_context=previous_memory,
    )

    # --------------------------------------------------------
    # 11. Combine decision + answer confidence
    # --------------------------------------------------------

    answer.addressed_to_me = decision.addressed_to_me

    answer.confidence = min(
        answer.confidence,
        decision.confidence,
    )

    # --------------------------------------------------------
    # 12. Tool call information for demo
    # --------------------------------------------------------

    answer.tool_calls = [
        {
            "tool": "search_my_notes",
            "args": {
                "query": question,
            },
        },
        {
            "tool": "get_style_examples",
            "args": {
                "question": question,
                "language": language,
            },
        },
        {
            "tool": "get_profile",
            "args": {},
        },
    ]

    # --------------------------------------------------------
    # 13. Debug information
    # --------------------------------------------------------

    answer.decision_reason = decision.reason

    answer.pruned_branches = (
        decision.pruned_branches
    )

    answer.remaining_branches = (
        decision.remaining_branches
    )

    answer.follow_up = follow_up

    answer.timings = {
        "decision_total_seconds": decision_seconds,
        "decision_llm_seconds": decision.decision_llm_seconds,
        "tool_and_graph_seconds": plan_seconds,
        "answer_llm_seconds": llm_seconds,
    }
    # --------------------------------------------------------
    # 14. Save successful answer to rolling memory
    # --------------------------------------------------------

    memory.add(
        question=question,
        reply=answer.reply_text,
    )

    return answer


# ============================================================
# Demo / Local Test
# ============================================================

if __name__ == "__main__":

    conversation = [
        "Ahmed, what's the difference between RAG and fine-tuning?",
        "Ahmed, and how is that different from what you said earlier?",
        "Sara, can you share your screen?",
        "Ahmed, how did your assignment use Kubernetes?",
    ]

    for question in conversation:

        print("\n" + "=" * 70)
        print(question)
        print("=" * 70)

        result = reply(question)

        print(
            result.model_dump_json(
                indent=2,
                ensure_ascii=False,
            )
        )

    print("\n" + "=" * 70)
    print("ROLLING MEMORY")
    print("=" * 70)

    print(
        json.dumps(
            memory.get_context(),
            ensure_ascii=False,
            indent=2,
        )
    )