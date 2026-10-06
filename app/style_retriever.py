from pathlib import Path
import json

import chromadb
from fastembed import TextEmbedding


DATA_PATH = Path("twin_data/style_examples.jsonl")
CHROMA_PATH = Path("chroma_db")

COLLECTION_NAME = "style_examples"
EMBEDDING_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


_embedding_model = None
_collection = None


def load_style_examples() -> list[dict]:
    """Load Ahmed's style examples from JSONL."""
    examples = []

    with DATA_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            examples.append(json.loads(line))

    return examples


def get_embedding_model() -> TextEmbedding:
    """Load the embedding model lazily."""
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = TextEmbedding(EMBEDDING_MODEL)

    return _embedding_model


def get_collection():
    """Get or create the persistent ChromaDB collection."""
    global _collection

    if _collection is None:
        client = chromadb.PersistentClient(
            path=str(CHROMA_PATH)
        )

        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    return _collection


def build_style_index() -> None:
    """
    Build the ChromaDB index from Ahmed's Q&A examples.
    """
    examples = load_style_examples()

    if not examples:
        raise ValueError("No style examples found.")

    model = get_embedding_model()
    collection = get_collection()

    # Rebuild the collection from the current JSONL dataset.
    existing = collection.get()

    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    questions = [
        example["question"]
        for example in examples
    ]

    embeddings = list(
        model.embed(questions)
    )

    collection.add(
        ids=[
            example["id"]
            for example in examples
        ],
        embeddings=[
            embedding.tolist()
            for embedding in embeddings
        ],
        documents=questions,
        metadatas=[
            {
                "id": example["id"],
                "answer": example["answer"],
                "language": example["language"],
                "audio": example["audio"],
            }
            for example in examples
        ],
    )

    print("=== STYLE INDEX BUILT ===")
    print("Examples:", len(examples))
    print("Collection:", COLLECTION_NAME)
    print("Embedding model:", EMBEDDING_MODEL)
    print("Dimension:", len(embeddings[0]))


def get_style_examples(
    question: str,
    language: str | None = None,
    k: int = 3,
) -> list[dict]:
    """
    Retrieve the most semantically similar style examples
    using ChromaDB + multilingual embeddings.
    """
    examples = load_style_examples()

    if not examples:
        return []

    collection = get_collection()

    # Build the index automatically if it does not exist yet.
    if collection.count() == 0:
        build_style_index()
        collection = get_collection()

    model = get_embedding_model()

    query_embedding = list(
        model.embed([question])
    )[0].tolist()

    # Use semantic retrieval across all languages.
    #
    # The embedding model is multilingual, so we intentionally
    # do not apply a hard language filter here. This allows an
    # Arabic, English, or mixed question to retrieve the most
    # semantically relevant example regardless of its language.

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(k, collection.count()),
        "include": [
            "documents",
            "metadatas",
            "distances",
        ],
    }

    results = collection.query(**query_kwargs)

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    retrieved = []

    for item_id, document, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances,
    ):
        # Chroma cosine distance:
        # similarity = 1 - distance
        similarity = max(
            0.0,
            min(1.0, 1.0 - float(distance)),
        )

        retrieved.append(
            {
                "id": item_id,
                "question": document,
                "answer": metadata["answer"],
                "language": metadata["language"],
                "audio": metadata["audio"],
                "similarity": round(similarity, 4),
            }
        )

    return retrieved


if __name__ == "__main__":
    build_style_index()

    test_queries = [
        (
            "What's the difference between "
            "RAG and fine-tuning?",
            "en",
        ),
        (
            "يعني إيه RAG؟",
            "ar",
        ),
        (
            "يا أحمد ممكن تشرحلي الـpruning "
            "في Decision Tree؟",
            "mixed",
        ),
    ]

    for question, language in test_queries:
        print("\n" + "=" * 60)
        print("QUERY:", question)
        print("LANGUAGE:", language)

        results = get_style_examples(
            question,
            language=language,
            k=3,
        )

        for i, result in enumerate(results, start=1):
            print(f"\n--- Result {i} ---")
            print("ID:", result["id"])
            print("Similarity:", result["similarity"])
            print("Question:", result["question"])
            print("Language:", result["language"])