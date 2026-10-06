from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from graphlib import TopologicalSorter
from typing import Any

from app.tools import (
    search_my_notes,
    get_style_examples,
    get_profile,
)


def build_reply_plan(
    question: str,
    language: str = "mixed",
) -> dict[str, Any]:
    """
    Build the dependency graph for generating an Ahmed-style reply.

    Independent branches:
        search_my_notes
        get_style_examples
        get_profile

    Final reply generation depends on all retrieved context.
    """

    graph = {
        "prepare": set(),
        "search_notes": {"prepare"},
        "style_examples": {"prepare"},
        "profile": {"prepare"},
        "compose_context": {
            "search_notes",
            "style_examples",
            "profile",
        },
    }

    sorter = TopologicalSorter(graph)
    sorter.prepare()

    results: dict[str, Any] = {
        "question": question,
        "language": language,
        "execution_order": [],
        "tool_results": {},
    }

    while sorter.is_active():

        ready_nodes = list(sorter.get_ready())

        if not ready_nodes:
            raise RuntimeError("Dependency graph has no executable nodes.")

        results["execution_order"].append(ready_nodes)

        with ThreadPoolExecutor(
            max_workers=len(ready_nodes)
        ) as executor:

            futures = {}

            for node in ready_nodes:

                if node == "prepare":
                    futures[node] = executor.submit(
                        lambda: {
                            "status": "prepared",
                            "question": question,
                            "language": language,
                        }
                    )

                elif node == "search_notes":
                    futures[node] = executor.submit(
                        search_my_notes.invoke,
                        {"query": question},
                    )

                elif node == "style_examples":
                    futures[node] = executor.submit(
                        get_style_examples.invoke,
                        {
                            "question": question,
                            "language": language,
                        },
                    )

                elif node == "profile":
                    futures[node] = executor.submit(
                        get_profile.invoke,
                        {},
                    )

                elif node == "compose_context":
                    futures[node] = executor.submit(
                        lambda: {
                            "notes": results["tool_results"].get(
                                "search_notes"
                            ),
                            "style_examples": results["tool_results"].get(
                                "style_examples"
                            ),
                            "profile": results["tool_results"].get(
                                "profile"
                            ),
                        }
                    )

                else:
                    raise ValueError(f"Unknown graph node: {node}")

        for node, future in futures.items():
            results["tool_results"][node] = future.result()
            sorter.done(node)

    return results


def print_plan(result: dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print("DEPENDENCY GRAPH")
    print("=" * 70)

    print("\nExecution batches:")

    for index, batch in enumerate(
        result["execution_order"],
        start=1,
    ):
        print(f"  Batch {index}: {batch}")

    print("\nTool results:")

    for name, value in result["tool_results"].items():

        if name == "compose_context":
            continue

        print(f"\n--- {name} ---")
        print(value)

    print("\n--- composed context ---")
    print(result["tool_results"]["compose_context"])


if __name__ == "__main__":

    question = (
        "Ahmed, what's the difference between "
        "RAG and fine-tuning?"
    )

    result = build_reply_plan(
        question=question,
        language="mixed",
    )

    print_plan(result)