from __future__ import annotations

import json
from pathlib import Path

from app.reply_generator import memory, reply


RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RESULTS_DIR / "test_results.json"


TESTS = [
    {
        "id": "T01",
        "name": "English addressed question",
        "question": "Ahmed, what's the difference between RAG and fine-tuning?",
        "expected_action": "answer",
        "expected_addressed": True,
    },
    {
        "id": "T02",
        "name": "Egyptian Arabic addressed question",
        "question": "يا أحمد، إيه الفرق بين الـ RAG والـ fine-tuning؟",
        "expected_action": "answer",
        "expected_addressed": True,
    },
    {
        "id": "T03",
        "name": "Mixed language question",
        "question": "يا أحمد، ممكن تشرحلنا الـ pruning في الـ decision tree بيعمل إيه؟",
        "expected_action": "answer",
        "expected_addressed": True,
    },
    {
        "id": "T04",
        "name": "Question addressed to another person",
        "question": "Sara, can you share your screen?",
        "expected_action": "stay_silent",
        "expected_addressed": False,
    },
    {
        "id": "T05",
        "name": "Open question to the class",
        "question": "Anyone? What does a CycleError mean?",
        "expected_action": "defer",
        "expected_addressed": False,
    },
    {
        "id": "T06",
        "name": "Follow-up memory",
        "question": "Ahmed, and how is that different from what you said earlier?",
        "expected_action": "answer",
        "expected_addressed": True,
        "setup_question": (
            "Ahmed, what's the difference between RAG and fine-tuning?"
        ),
    },
    {
        "id": "T07",
        "name": "Outside knowledge",
        "question": "Ahmed, how did your assignment use Kubernetes?",
        "expected_action": "defer",
        "expected_addressed": True,
    },
    {
        "id": "T08",
        "name": "Low quality / unclear audio policy",
        "question": "[UNCLEAR AUDIO]",
        "expected_action": "ask_to_repeat",
        "expected_addressed": False,
        "quality_score": 0.30,
    },
]


def reset_memory() -> None:
    """Start every independent test with clean memory."""
    memory.clear()


def run_single_test(test: dict) -> dict:
    reset_memory()

    # ------------------------------------------------------------
    # Optional setup for follow-up memory test
    # ------------------------------------------------------------

    if test.get("setup_question"):
        setup_reply = reply(
            question=test["setup_question"],
            quality_score=1.0,
        )

        # We intentionally keep this turn in rolling memory.
        setup_memory = memory.get_context()

    else:
        setup_reply = None
        setup_memory = []

    # ------------------------------------------------------------
    # Run actual test
    # ------------------------------------------------------------

    quality_score = test.get("quality_score", 1.0)

    twin_reply = reply(
        question=test["question"],
        quality_score=quality_score,
    )

    actual_action = twin_reply.action
    actual_addressed = twin_reply.addressed_to_me

    action_pass = actual_action == test["expected_action"]
    addressed_pass = (
        actual_addressed == test["expected_addressed"]
    )

    passed = action_pass and addressed_pass

    return {
        "id": test["id"],
        "name": test["name"],
        "input": test["question"],
        "expected": {
            "action": test["expected_action"],
            "addressed_to_me": test["expected_addressed"],
        },
        "actual": {
            "action": actual_action,
            "addressed_to_me": actual_addressed,
            "language": twin_reply.language,
            "reply_text": twin_reply.reply_text,
            "confidence": twin_reply.confidence,
            "follow_up": twin_reply.follow_up,
            "tools_used": twin_reply.tools_used,
            "sources": twin_reply.sources,
            "tool_calls": twin_reply.tool_calls,
            "decision_reason": twin_reply.decision_reason,
            "pruned_branches": twin_reply.pruned_branches,
            "remaining_branches": twin_reply.remaining_branches,
            "timings": twin_reply.timings,
        },
        "validation": {
            "action_pass": action_pass,
            "addressed_pass": addressed_pass,
            "passed": passed,
        },
        "setup_memory": setup_memory,
        "setup_reply": (
            setup_reply.model_dump()
            if setup_reply
            else None
        ),
    }


def main() -> None:
    results = []

    print("=" * 80)
    print("CLASS TWIN — PHASE 1 TEST SUITE")
    print("=" * 80)

    for test in TESTS:
        print(f"\nRunning {test['id']}: {test['name']}")

        result = run_single_test(test)
        results.append(result)

        status = (
            "PASS"
            if result["validation"]["passed"]
            else "FAIL"
        )

        print(f"Expected action : {test['expected_action']}")
        print(
            f"Actual action   : "
            f"{result['actual']['action']}"
        )
        print(
            f"Expected addressed : "
            f"{test['expected_addressed']}"
        )
        print(
            f"Actual addressed   : "
            f"{result['actual']['addressed_to_me']}"
        )
        print(f"Status          : {status}")

    # ------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------

    passed = sum(
        1
        for result in results
        if result["validation"]["passed"]
    )

    failed = len(results) - passed

    summary = {
        "total_tests": len(results),
        "passed": passed,
        "failed": failed,
        "accuracy": round(
            passed / len(results),
            3,
        ),
    }

    output = {
        "summary": summary,
        "tests": results,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"Total : {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Accuracy: {summary['accuracy'] * 100:.1f}%")

    print("\nResults saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()