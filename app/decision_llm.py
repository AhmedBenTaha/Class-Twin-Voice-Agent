from __future__ import annotations

import json
import os
import time

from dotenv import load_dotenv
from groq import Groq

from app.decision import (
    DecisionResult,
    detect_addressing,
    has_supported_topic,
    is_low_quality,
    prune_and_select,
)


load_dotenv()

MODEL = "openai/gpt-oss-120b"

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def _extract_json(text: str) -> dict:
    """
    Extract JSON from an LLM response.
    """
    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM response.")

    return json.loads(text[start:end + 1])


def llm_score_question(
    question: str,
    addressed_to_me: bool,
    has_memory: bool = False,
) -> tuple[dict[str, float], float]:
    """
    Ask the LLM to score possible actions.

    Returns:
        scores,
        llm_seconds
    """

    prompt = f"""
You are the decision layer for Ahmed's Class Twin.

The agent can choose exactly one action:

- answer
- defer
- ask_to_repeat
- stay_silent

Question:
{question}

Explicitly addressed to Ahmed:
{addressed_to_me}

Conversation memory available:
{has_memory}

Rules:

1. If the question is explicitly addressed to another person,
   choose stay_silent.

2. If the question is addressed to Ahmed, answer when the topic
   is supported by the available knowledge.

3. If there is no person's name, the question may be open to the
   class. Do NOT automatically choose stay_silent.

4. If the question is about a supported topic, answer is preferred.

5. If the question requires personal information or knowledge
   that Ahmed's knowledge pack does not contain, defer.

6. If the audio/question is unclear, ask_to_repeat.

7. A follow-up question may refer to an earlier turn without
   repeating the topic keywords. If conversation memory is
   available and the question is clearly a follow-up, prefer
   answer over ask_to_repeat.

Return ONLY valid JSON:

{{
  "answer": 0.0,
  "defer": 0.0,
  "ask_to_repeat": 0.0,
  "stay_silent": 0.0
}}

Scores must be between 0 and 1.
"""

    # --------------------------------------------------------
    # Measure ONLY the decision LLM call
    # --------------------------------------------------------

    start = time.perf_counter()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict decision classifier. "
                    "Return JSON only."
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

    content = response.choices[0].message.content or ""

    scores = _extract_json(content)

    required_actions = {
        "answer",
        "defer",
        "ask_to_repeat",
        "stay_silent",
    }

    for action in required_actions:
        if action not in scores:
            scores[action] = 0.0

    normalized_scores = {
        action: float(scores[action])
        for action in required_actions
    }

    return normalized_scores, llm_seconds


def decide_with_llm(
    transcription: dict,
    threshold: float = 0.70,
    has_memory: bool = False,
) -> DecisionResult:
    """
    Hybrid decision policy.

    Cheap deterministic checks happen first.
    The LLM is used only when the question survives them.
    """

    question = transcription.get("text", "").strip()

    # --------------------------------------------------------
    # Branch 1: bad / empty audio
    # --------------------------------------------------------

    if is_low_quality(transcription):
        return DecisionResult(
            action="ask_to_repeat",
            addressed_to_me=False,
            reason="Audio/transcription quality is too low.",
            confidence=0.95,
            pruned_branches=[
                "answer",
                "defer",
                "stay_silent",
            ],
            remaining_branches=[
                "ask_to_repeat",
            ],
            decision_llm_seconds=0.0,
        )

    # --------------------------------------------------------
    # Branch 2: addressing
    # --------------------------------------------------------

    addressing = detect_addressing(question)

    # Explicitly addressed to someone else.
    if addressing == "other":
        return DecisionResult(
            action="stay_silent",
            addressed_to_me=False,
            reason="The question is addressed to another person.",
            confidence=0.98,
            pruned_branches=[
                "answer",
                "ask_to_repeat",
                "defer",
            ],
            remaining_branches=[
                "stay_silent",
            ],
            decision_llm_seconds=0.0,
        )

    addressed_to_me = addressing == "me"

    # --------------------------------------------------------
    # Branch 3: cheap knowledge check
    # --------------------------------------------------------

    supported = has_supported_topic(question)

    # A follow-up question may not repeat the original topic.
    # If valid conversation memory exists, allow the LLM
    # to resolve the question using that context.
    if not supported and not has_memory:
        return DecisionResult(
            action="defer",
            addressed_to_me=addressed_to_me,
            reason=(
                "The topic is outside the current "
                "Phase 1 knowledge pack."
            ),
            confidence=0.85,
            pruned_branches=[
                "answer",
                "stay_silent",
                "ask_to_repeat",
            ],
            remaining_branches=[
                "defer",
            ],
            decision_llm_seconds=0.0,
        )

    # --------------------------------------------------------
    # Branch 4: LLM scoring
    # --------------------------------------------------------

    scores, decision_llm_seconds = llm_score_question(
        question=question,
        addressed_to_me=addressed_to_me,
        has_memory=has_memory,
    )

    selected, pruned, remaining = prune_and_select(
        scores,
        threshold=threshold,
    )

    # --------------------------------------------------------
    # Branch 5: nothing cleared threshold
    # --------------------------------------------------------

    if selected is None:
        return DecisionResult(
            action="ask_to_repeat",
            addressed_to_me=addressed_to_me,
            reason=(
                "No candidate action cleared the "
                "confidence threshold."
            ),
            confidence=threshold,
            pruned_branches=pruned,
            remaining_branches=[
                "ask_to_repeat",
            ],
            decision_llm_seconds=decision_llm_seconds,
        )

    # --------------------------------------------------------
    # Final decision
    # --------------------------------------------------------

    return DecisionResult(
        action=selected,  # type: ignore[arg-type]
        addressed_to_me=addressed_to_me,
        reason=(
            "Question passed cheap checks and the LLM "
            "selected the highest-confidence action."
        ),
        confidence=scores[selected],
        pruned_branches=pruned,
        remaining_branches=remaining,
        decision_llm_seconds=decision_llm_seconds,
    )


if __name__ == "__main__":

    tests = [
        {
            "name": "English addressed",
            "text": (
                "Ahmed, what's the difference between "
                "RAG and fine-tuning?"
            ),
            "quality_score": 0.94,
        },
        {
            "name": "Direct question without name",
            "text": (
                "What is the difference between "
                "RAG and fine-tuning?"
            ),
            "quality_score": 0.94,
        },
        {
            "name": "Addressed to Sara",
            "text": (
                "Sara, can you share your screen?"
            ),
            "quality_score": 0.94,
        },
        {
            "name": "Unknown topic",
            "text": (
                "Ahmed, how did your assignment "
                "use Kubernetes?"
            ),
            "quality_score": 0.94,
        },
        {
            "name": "Bad audio",
            "text": (
                "Ahmed, what's the difference..."
            ),
            "quality_score": 0.30,
        },
    ]

    for test in tests:

        result = decide_with_llm(test)

        print("\n" + "=" * 60)
        print(test["name"])
        print("Text:", test["text"])
        print("Action:", result.action)
        print("Addressed to me:", result.addressed_to_me)
        print("Confidence:", result.confidence)
        print("Reason:", result.reason)
        print("Pruned:", result.pruned_branches)
        print("Remaining:", result.remaining_branches)
        print(
            "Decision LLM:",
            result.decision_llm_seconds,
            "s",
        )