from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts


OUTPUT_DIR = Path("results/audio")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


VOICE_MAP = {
    "ar": "ar-EG-SalmaNeural",
    "en": "en-US-AndrewNeural",
    "mixed": "ar-EG-SalmaNeural",
}


def speak(
    text: str,
    language: str = "mixed",
    output_name: str = "twin_reply.mp3",
) -> str:
    """
    Convert Ahmed's generated reply into speech.

    Returns:
        Path to the generated audio file.
    """

    if not text.strip():
        raise ValueError("Cannot generate speech from empty text.")

    voice = VOICE_MAP.get(language, VOICE_MAP["mixed"])

    output_path = OUTPUT_DIR / output_name

    async def _generate() -> None:
        communicator = edge_tts.Communicate(
            text=text,
            voice=voice,
        )
        await communicator.save(str(output_path))

    asyncio.run(_generate())

    return str(output_path)


if __name__ == "__main__":
    audio_path = speak(
        text="The main difference is that RAG retrieves external knowledge at inference time, while fine-tuning changes the model through additional training.",
        language="en",
        output_name="test_en.mp3",
    )

    print(f"Audio saved to: {audio_path}")
  