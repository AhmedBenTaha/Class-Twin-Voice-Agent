from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal


Action = Literal[
    "answer",
    "ask_to_repeat",
    "defer",
    "stay_silent",
]


@dataclass
class DecisionResult:
    action: Action
    addressed_to_me: bool
    reason: str
    confidence: float
    pruned_branches: list[str]
    remaining_branches: list[str]
    decision_llm_seconds: float = 0.0

AHMED_NAMES = [
    "ahmed",
    "ahmad",
    "أحمد",
    "طه",
    "taha"
]

OTHER_NAMES = [
    "sara",
    "sarah",
    "سارة",
]


def normalize_text(text: str) -> str:
    """Normalize text for simple rule-based checks."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def detect_addressing(text: str) -> str:
    """
    Detect whether the question is addressed to Ahmed,
    another named person, or the whole class.
    """
    normalized = normalize_text(text)

    # Someone explicitly called another person's name.
    for name in OTHER_NAMES:
        if re.search(rf"\b{re.escape(name)}\b", normalized):
            return "other"

    # Ahmed's name in English or Arabic.
    for name in AHMED_NAMES:
        if name in normalized:
            return "me"

    # No person's name -> potentially open to the class.
    return "class"


def is_low_quality(transcription: dict) -> bool:
    """Cheap audio/transcription quality check."""
    text = transcription.get("text", "").strip()
    quality = transcription.get("quality_score", 0.0)

    if not text:
        return True

    if quality < 0.55:
        return True

    return False


def has_supported_topic(text: str) -> bool:
    """
    Cheap knowledge check based on the current Phase 1 knowledge pack.

    This is intentionally conservative. It does NOT claim that the
    question is answerable; it only detects whether it matches topics
    we have examples/knowledge for.
    """
    normalized = normalize_text(text)

    known_topics = [
        "rag",
        "retrieval",
        "fine-tuning",
        "finetuning",
        "fine tuning",
        "ai agent",
        "agent",
        "workflow",
        "langgraph",
        "tool calling",
        "tool",
        "hallucination",
        "vector database",
        "vector db",
        "embedding",
        "embeddings",
        "decision tree",
        "pruning",
        "pdf",
    ]

    return any(topic in normalized for topic in known_topics)


def prune_and_select(
    candidates: dict[str, float],
    threshold: float = 0.70,
) -> tuple[str | None, list[str], list[str]]:
    """
    Keep only candidate actions whose score clears the threshold.

    Returns:
        selected_action
        pruned_branches
        remaining_branches
    """
    remaining = [
        action
        for action, score in candidates.items()
        if score >= threshold
    ]

    pruned = [
        action
        for action, score in candidates.items()
        if score < threshold
    ]

    if not remaining:
        return None, pruned, []

    selected = max(
        remaining,
        key=lambda action: candidates[action],
    )

    # Keep only the selected branch as the final branch.
    final_remaining = [selected]

    # Other branches are effectively pruned after selection.
    for action in remaining:
        if action != selected:
            pruned.append(action)

    return selected, pruned, final_remaining


def decide(
    transcription: dict,
    threshold: float = 0.70,
) -> DecisionResult:
    """
    Phase 1 decision policy.

    Order:
    1. Cheap audio quality check.
    2. Addressing check.
    3. Knowledge/topic check.
    4. Select final action.
    """

    text = transcription.get("text", "").strip()

    # ---------------------------------------------------------
    # Branch 1: bad / empty audio
    # ---------------------------------------------------------
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
            remaining_branches=["ask_to_repeat"],
        )

    # ---------------------------------------------------------
    # Branch 2: addressing
    # ---------------------------------------------------------
    addressing = detect_addressing(text)

    # Explicitly addressed to another person.
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
            remaining_branches=["stay_silent"],
        )

    # Ahmed -> explicitly addressed to Ahmed.
    # Class -> no explicit person was named.
    addressed_to_me = addressing == "me"

    # ---------------------------------------------------------
    # Branch 3: topic / knowledge check
    # ---------------------------------------------------------
    supported = has_supported_topic(text)

    if not supported:
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
            remaining_branches=["defer"],
        )

    # ---------------------------------------------------------
    # Branch 4: answerable question
    # ---------------------------------------------------------
    #
    # Important:
    # A question without "Ahmed" is NOT automatically silent.
    #
    # If it is a supported topic, we allow the agent to answer.
    #
    candidates = {
        "answer": 0.90 if addressing == "me" else 0.75,
        "defer": 0.10,
        "ask_to_repeat": 0.05,
        "stay_silent": 0.05 if addressing == "me" else 0.20,
    }

    selected, pruned, remaining = prune_and_select(
        candidates,
        threshold=threshold,
    )

    if selected is None:
        return DecisionResult(
            action="ask_to_repeat",
            addressed_to_me=addressed_to_me,
            reason=(
                "No candidate action cleared the "
                "confidence threshold."
            ),
            confidence=0.50,
            pruned_branches=list(candidates.keys()),
            remaining_branches=["ask_to_repeat"],
        )

    return DecisionResult(
        action=selected,  # type: ignore[arg-type]
        addressed_to_me=addressed_to_me,
        reason=(
            "Question matches the current knowledge pack and "
            "cleared the decision threshold."
        ),
        confidence=candidates[selected],
        pruned_branches=pruned,
        remaining_branches=remaining,
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
            "name": "Egyptian Arabic addressed",
            "text": (
                "يا أحمد، إيه الفرق بين الـ RAG "
                "والـ fine-tuning؟"
            ),
            "quality_score": 0.94,
        },
        {
            "name": "Mixed addressed",
            "text": (
                "يا أحمد، ممكن تشرحلنا الـ pruning "
                "في الـ decision tree؟"
            ),
            "quality_score": 0.94,
        },
        {
            "name": "Addressed to Sara",
            "text": "Sara, can you share your screen?",
            "quality_score": 0.94,
        },
        {
            "name": "Open to class - supported",
            "text": "Anyone? What does a CycleError mean?",
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
            "name": "Unknown topic",
            "text": (
                "Ahmed, how did your assignment "
                "use Kubernetes?"
            ),
            "quality_score": 0.94,
        },
        {
            "name": "Bad audio",
            "text": "Ahmed, what's the difference...",
            "quality_score": 0.30,
        },
    ]

    for test in tests:
        result = decide(test)

        print("\n" + "=" * 60)
        print(test["name"])
        print("Text:", test["text"])
        print("Action:", result.action)
        print("Addressed to me:", result.addressed_to_me)
        print("Confidence:", result.confidence)
        print("Reason:", result.reason)
        print("Pruned:", result.pruned_branches)
        print("Remaining:", result.remaining_branches)