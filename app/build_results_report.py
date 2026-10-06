from __future__ import annotations

import json
from pathlib import Path


INPUT_FILE = Path("results/test_results.json")
OUTPUT_FILE = Path("results/test_results.md")


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing results file: {INPUT_FILE}"
        )

    data = json.loads(
        INPUT_FILE.read_text(encoding="utf-8")
    )

    summary = data["summary"]
    tests = data["tests"]

    lines = []

    lines.append("# Class Twin Phase 1 — Test Results")
    lines.append("")
    lines.append(
        f"**Overall:** {summary['passed']}/{summary['total_tests']} "
        f"tests passed ({summary['accuracy'] * 100:.1f}%)."
    )
    lines.append("")

    lines.append(
        "| Test | Expected | Actual | Confidence | Result |"
    )
    lines.append(
        "|---|---|---|---:|---|"
    )

    for test in tests:
        test_id = test["id"]
        name = test["name"]

        expected = test["expected"]["action"]
        actual = test["actual"]["action"]

        confidence = test["actual"]["confidence"]

        result = (
            "✅ PASS"
            if test["validation"]["passed"]
            else "❌ FAIL"
        )

        lines.append(
            f"| {test_id} — {name} "
            f"| `{expected}` "
            f"| `{actual}` "
            f"| {confidence:.2f} "
            f"| {result} |"
        )

    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")

    for test in tests:
        actual = test["actual"]

        lines.append(
            f"### {test['id']} — {test['name']}"
        )
        lines.append("")

        lines.append(
            f"**Question:** {test['input']}"
        )
        lines.append("")

        lines.append(
            f"- Expected action: `{test['expected']['action']}`"
        )
        lines.append(
            f"- Actual action: `{actual['action']}`"
        )
        lines.append(
            f"- Addressed to Ahmed: `{actual['addressed_to_me']}`"
        )
        lines.append(
            f"- Language: `{actual['language']}`"
        )
        lines.append(
            f"- Confidence: `{actual['confidence']:.2f}`"
        )
        lines.append(
            f"- Follow-up: `{actual['follow_up']}`"
        )

        lines.append("")
        lines.append("**Decision reason:**")
        lines.append("")
        lines.append(
            f"> {actual['decision_reason']}"
        )

        lines.append("")
        lines.append("**Pruned branches:**")
        lines.append("")

        for branch in actual["pruned_branches"]:
            lines.append(f"- `{branch}`")

        lines.append("")
        lines.append("**Remaining branches:**")
        lines.append("")

        for branch in actual["remaining_branches"]:
            lines.append(f"- `{branch}`")

        lines.append("")

        if actual["tools_used"]:
            lines.append("**Tools used:**")
            lines.append("")

            for tool in actual["tools_used"]:
                lines.append(f"- `{tool}`")

            lines.append("")

        if actual["sources"]:
            lines.append("**Sources:**")
            lines.append("")

            for source in actual["sources"]:
                lines.append(f"- `{source}`")

            lines.append("")

        timings = actual.get("timings", {})

        if timings:
            lines.append("**Timing:**")
            lines.append("")

            for name, value in timings.items():
                lines.append(
                    f"- {name}: `{value:.3f}s`"
                )

            lines.append("")

        lines.append("---")
        lines.append("")

    OUTPUT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print("=" * 70)
    print("RESULTS REPORT GENERATED")
    print("=" * 70)
    print(f"Tests   : {summary['total_tests']}")
    print(f"Passed  : {summary['passed']}")
    print(f"Failed  : {summary['failed']}")
    print(
        f"Accuracy: {summary['accuracy'] * 100:.1f}%"
    )
    print()
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()