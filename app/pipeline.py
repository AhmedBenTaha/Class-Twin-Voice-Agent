from __future__ import annotations

import time

from app.reply_generator import reply
from app.speak import speak
from app.transcribe import transcribe


def run_pipeline(audio_path: str) -> dict:
    total_start = time.perf_counter()

    # 1. Speech-to-Text
    stt_start = time.perf_counter()

    transcription = transcribe(audio_path)

    stt_seconds = round(time.perf_counter() - stt_start, 3)

    question = transcription["text"]
    language = transcription["detected_language"]
    quality_score = transcription["quality_score"]

    # 2. Decision + Reply
    reply_start = time.perf_counter()

    twin_reply = reply(
        question=question,
        quality_score=quality_score,
    )

    decision_and_reply_seconds = round(
        time.perf_counter() - reply_start,
        3,
    )

    reply_timings = twin_reply.timings

    # 3. Speech synthesis
    audio_output = None

    if twin_reply.reply_text.strip():
        speech_start = time.perf_counter()

        audio_output = speak(
            text=twin_reply.reply_text,
            language=twin_reply.language,
            output_name="twin_reply.mp3",
        )

        speech_seconds = round(
            time.perf_counter() - speech_start,
            3,
        )
    else:
        speech_seconds = 0.0

    # 4. Total
    total_seconds = round(
        time.perf_counter() - total_start,
        3,
    )

    timings = {
        "stt_seconds": stt_seconds,

        "decision_total_seconds": reply_timings.get(
            "decision_total_seconds",
            0.0,
        ),

        "decision_llm_seconds": reply_timings.get(
            "decision_llm_seconds",
            0.0,
        ),

        "tool_and_graph_seconds": reply_timings.get(
            "tool_and_graph_seconds",
            0.0,
        ),

        "answer_llm_seconds": reply_timings.get(
            "answer_llm_seconds",
            0.0,
        ),

        "speech_seconds": speech_seconds,

        "total_seconds": total_seconds,
    }

    return {
        "transcription": transcription,
        "twin_reply": twin_reply.model_dump(),
        "audio": audio_output,
        "timings": timings,
    }


if __name__ == "__main__":
    test_audio = "twin_data/voice/recordings/Q02_rag_vs_finetuning.m4a"

    result = run_pipeline(test_audio)

    print("\n" + "=" * 70)
    print("TRANSCRIPT")
    print("=" * 70)
    print(result["transcription"]["text"])

    print("\n" + "=" * 70)
    print("TWIN REPLY")
    print("=" * 70)

    twin_reply = result["twin_reply"]

    print(f"Action: {twin_reply['action']}")
    print(f"Language: {twin_reply['language']}")
    print(f"Confidence: {twin_reply['confidence']}")
    print(f"Reply: {twin_reply['reply_text']}")

    print("\n" + "=" * 70)
    print("TIMINGS")
    print("=" * 70)

    for name, seconds in result["timings"].items():
        print(f"{name}: {seconds:.3f}s")

    print("\n" + "=" * 70)
    print("AUDIO")
    print("=" * 70)
    print(result["audio"])