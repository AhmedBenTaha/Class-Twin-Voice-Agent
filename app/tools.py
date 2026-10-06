from pathlib import Path
import json

from langchain_core.tools import tool

from app.style_retriever import (
    get_style_examples as retrieve_style_examples
)
PROFILE_PATH = Path(
    "twin_data/profile.json"
)

GLOSSARY_PATH = Path(
    "twin_data/knowledge/course_glossary.json"
)


@tool
def get_profile() -> dict:
    """
    Get Ahmed's profile and communication style.

    Use this when the agent needs information about
    Ahmed's background, language preferences, tone,
    or communication style.
    """

    with PROFILE_PATH.open(
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


@tool
def get_style_examples(
    question: str,
    language: str = "mixed",
) -> list[dict]:
    """
    Retrieve examples of how Ahmed answered
    similar questions in his own style.

    Use this when generating an answer that should
    sound like Ahmed.
    """

    return retrieve_style_examples(
        question=question,
        language=language,
        k=3,
    )


@tool
def search_my_notes(
    query: str,
) -> dict:
    """
    Search Ahmed's personal course notes.

    Returns matching knowledge from the local
    course glossary for Phase 1.
    """

    if not GLOSSARY_PATH.exists():
        return {
            "found": False,
            "results": [],
            "message": "Notes are not available."
        }

    with GLOSSARY_PATH.open(
        "r",
        encoding="utf-8"
    ) as f:
        glossary = json.load(f)

    query_lower = query.lower()

    results = []

    for term, definition in glossary.items():

        if (
            query_lower in term.lower()
            or term.lower() in query_lower
            or any(
                word in definition.lower()
                for word in query_lower.split()
                if len(word) > 2
            )
        ):
            results.append(
                {
                    "term": term,
                    "definition": definition,
                }
            )

    return {
        "found": bool(results),
        "results": results,
    }


@tool
def get_course_glossary(
    term: str,
) -> dict:
    """
    Look up a specific AI/course term.
    """

    if not GLOSSARY_PATH.exists():
        return {
            "found": False,
            "term": term,
            "definition": None,
        }

    with GLOSSARY_PATH.open(
        "r",
        encoding="utf-8"
    ) as f:
        glossary = json.load(f)

    term_lower = term.lower()

    for key, definition in glossary.items():

        if key.lower() == term_lower:
            return {
                "found": True,
                "term": key,
                "definition": definition,
            }

    return {
        "found": False,
        "term": term,
        "definition": None,
    }


ALL_TOOLS = [
    search_my_notes,
    get_style_examples,
    get_profile,
    get_course_glossary,
]
