from pathlib import Path
from typing import Any
import json
import re

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

client = Groq()


def _get_value(obj: Any, key: str, default=None):
    """Read a field from either a dict or an object."""
    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _calculate_quality(segments: list[Any]) -> float:
    """Calculate a simple STT quality score between 0 and 1."""

    if not segments:
        return 0.0

    scores = []

    for segment in segments:
        avg_logprob = _get_value(segment, "avg_logprob")
        no_speech_prob = _get_value(segment, "no_speech_prob")

        if avg_logprob is None:
            continue

        confidence = max(
            0.0,
            min(1.0, 1.0 + (float(avg_logprob) / 5.0))
        )

        if no_speech_prob is not None:
            no_speech_prob = float(no_speech_prob)

            confidence *= (
                1.0 - min(1.0, max(0.0, no_speech_prob))
            )

        scores.append(confidence)

    if not scores:
        return 0.0

    return round(sum(scores) / len(scores), 3)


def detect_language(text: str) -> str:
    """
    Detect whether the transcript is Arabic, English, or mixed.

    This is intentionally simple and deterministic.
    Whisper's language label alone is not enough for code-switching.
    """

    if not text.strip():
        return "unknown"

    arabic_chars = len(
        re.findall(r"[\u0600-\u06FF]", text)
    )

    latin_chars = len(
        re.findall(r"[A-Za-z]", text)
    )

    total = arabic_chars + latin_chars

    if total == 0:
        return "unknown"

    arabic_ratio = arabic_chars / total
    english_ratio = latin_chars / total

    if arabic_ratio >= 0.70:
        return "ar"

    if english_ratio >= 0.70:
        return "en"

    return "mixed"


def transcribe(audio_path: str | Path) -> dict:
    """
    Transcribe an audio file using Groq Whisper.

    Returns:
        {
            "text": str,
            "language": str | None,
            "detected_language": str,
            "quality_score": float,
            "segments": list
        }
    """

    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    with audio_path.open("rb") as audio_file:
        result = client.audio.transcriptions.create(
            file=(
                audio_path.name,
                audio_file.read()
            ),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
        )

    text = _get_value(result, "text", "") or ""

    whisper_language = _get_value(
        result,
        "language"
    )

    raw_segments = _get_value(
        result,
        "segments",
        []
    ) or []

    quality_score = _calculate_quality(
        raw_segments
    )

    detected_language = detect_language(text)

    segments = []

    for segment in raw_segments:
        segments.append(
            {
                "start": _get_value(
                    segment,
                    "start"
                ),
                "end": _get_value(
                    segment,
                    "end"
                ),
                "text": _get_value(
                    segment,
                    "text",
                    ""
                ) or "",
                "avg_logprob": _get_value(
                    segment,
                    "avg_logprob"
                ),
                "no_speech_prob": _get_value(
                    segment,
                    "no_speech_prob"
                ),
            }
        )

    return {
        "text": text,
        "language": whisper_language,
        "detected_language": detected_language,
        "quality_score": quality_score,
        "segments": segments,
    }


def save_transcription(
    audio_path: str | Path,
    result: dict
) -> Path:
    """Save transcription result as JSON."""

    audio_path = Path(audio_path)

    output_dir = Path(
        "results/transcriptions"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        output_dir /
        f"{audio_path.stem}.json"
    )

    data = {
        "audio": str(audio_path),
        **result,
    }

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    return output_path


if __name__ == "__main__":

    audio = Path(
        "twin_data/voice/recordings/Q01_rag.m4a"
    )

    result = transcribe(audio)

    output_path = save_transcription(
        audio,
        result
    )

    print("\n=== TRANSCRIPTION ===")
    print(result["text"])

    print("\n=== WHISPER LANGUAGE ===")
    print(result["language"])

    print("\n=== DETECTED LANGUAGE ===")
    print(result["detected_language"])

    print("\n=== QUALITY SCORE ===")
    print(result["quality_score"])

    print("\n=== SEGMENTS ===")

    for segment in result["segments"]:

        start = segment["start"]
        end = segment["end"]

        if start is not None and end is not None:
            time_info = (
                f"[{float(start):.2f}s - "
                f"{float(end):.2f}s]"
            )
        else:
            time_info = "[time unavailable]"

        print(
            f"{time_info} "
            f"{segment['text']}"
        )

    print("\n=== SAVED ===")
    print(output_path)
