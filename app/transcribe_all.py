import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is not set")

client = Groq(api_key=api_key)

AUDIO_DIR = Path("twin_data/voice/recordings")
OUTPUT_DIR = Path("results/transcripts")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

audio_files = sorted(AUDIO_DIR.glob("*.m4a"))

print(f"Found {len(audio_files)} audio files.\n")

for audio_file in audio_files:
    output_file = OUTPUT_DIR / f"{audio_file.stem}.txt"

    print(f"Transcribing: {audio_file.name}")

    with audio_file.open("rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_file.name, file.read()),
            model="whisper-large-v3-turbo",
            response_format="text",
        )

    output_file.write_text(
        str(transcription),
        encoding="utf-8",
    )

    print(f"Saved: {output_file}\n")

print("Done.")