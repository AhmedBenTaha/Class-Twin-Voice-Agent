from pathlib import Path
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DATA_PATH = Path("twin_data/style_examples.jsonl")


def load_style_examples() -> list[dict]:
    """Load Ahmed's style examples."""

    examples = []

    with DATA_PATH.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:
            line = line.strip()

            if not line:
                continue

            examples.append(
                json.loads(line)
            )

    return examples


def get_style_examples(
    question: str,
    language: str | None = None,
    k: int = 3,
) -> list[dict]:
    """
    Retrieve the most similar examples
    from Ahmed's own Q&A dataset.
    """

    examples = load_style_examples()

    if not examples:
        return []

    # Prefer examples from the same language.
    candidates = examples

    if language in {"ar", "en", "mixed"}:

        same_language = [
            example
            for example in examples
            if example.get("language") == language
        ]

        if len(same_language) >= k:
            candidates = same_language

    questions = [
        example["question"]
        for example in candidates
    ]

    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 5),
        lowercase=True,
    )

    matrix = vectorizer.fit_transform(
        questions
    )

    query_vector = vectorizer.transform(
        [question]
    )

    similarities = cosine_similarity(
        query_vector,
        matrix
    )[0]

    ranked_indices = similarities.argsort()[::-1][:k]

    results = []

    for index in ranked_indices:

        example = candidates[int(index)]

        results.append(
            {
                "id": example["id"],
                "question": example["question"],
                "answer": example["answer"],
                "language": example["language"],
                "audio": example["audio"],
                "similarity": round(
                    float(similarities[index]),
                    4
                ),
            }
        )

    return results


if __name__ == "__main__":

    question = (
        "What's the difference between "
        "RAG and fine-tuning?"
    )

    results = get_style_examples(
        question,
        language="en",
        k=3
    )

    print("\n=== STYLE RETRIEVAL ===")

    for i, result in enumerate(
        results,
        start=1
    ):
        print(f"\n--- Result {i} ---")
        print("ID:", result["id"])
        print("Question:", result["question"])
        print("Language:", result["language"])
        print("Similarity:", result["similarity"])
        print("Answer:", result["answer"])
