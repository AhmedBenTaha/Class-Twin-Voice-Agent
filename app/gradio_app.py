from __future__ import annotations

import json

import gradio as gr

from app.pipeline import run_pipeline
from app.reply_generator import memory


def process_audio(audio_path: str | None):
    """Run the complete Class Twin Phase 1 pipeline."""

    empty = (
        "No audio provided.",
        "",
        "",
        "[]",
        "{}",
        "",
        "",
        None,
    )

    if not audio_path:
        return empty

    try:
        # Run complete pipeline
        result = run_pipeline(audio_path)

        transcription = result.get("transcription", {})
        twin_reply = result.get("twin_reply", {})
        timings = result.get("timings", {})

        # ---------------------------------------------------------
        # 1. Transcript
        # ---------------------------------------------------------

        transcript_text = str(
            transcription.get("text", "")
        ).strip()

        transcript_info = (
            f"Language: {transcription.get('detected_language', 'unknown')}\n"
            f"Whisper language: {transcription.get('language', 'unknown')}\n"
            f"Quality score: "
            f"{float(transcription.get('quality_score', 0.0)):.3f}"
        )

        # ---------------------------------------------------------
        # 2. Decision
        # ---------------------------------------------------------

        pruned_branches = twin_reply.get(
            "pruned_branches", []
        )

        remaining_branches = twin_reply.get(
            "remaining_branches", []
        )

        pruned_json = json.dumps(
            pruned_branches,
            ensure_ascii=False,
            indent=2,
        )

        remaining_json = json.dumps(
            remaining_branches,
            ensure_ascii=False,
            indent=2,
        )

        decision_text = (
            f"Action: {twin_reply.get('action', '')}\n"
            f"Addressed to me: "
            f"{twin_reply.get('addressed_to_me', False)}\n"
            f"Confidence: "
            f"{float(twin_reply.get('confidence', 0.0)):.3f}\n"
            f"Follow-up: "
            f"{twin_reply.get('follow_up', False)}\n\n"
            f"Reason:\n"
            f"{twin_reply.get('decision_reason', '')}\n\n"
            f"Pruned branches:\n"
            f"{pruned_json}\n\n"
            f"Remaining branches:\n"
            f"{remaining_json}"
        )

        # ---------------------------------------------------------
        # 3. Tool calls
        # ---------------------------------------------------------

        tool_text = json.dumps(
            twin_reply.get("tool_calls", []),
            ensure_ascii=False,
            indent=2,
        )

        # ---------------------------------------------------------
        # 4. TwinReply JSON
        # ---------------------------------------------------------

        reply_json = json.dumps(
            twin_reply,
            ensure_ascii=False,
            indent=2,
        )

        # ---------------------------------------------------------
        # 5. Final reply
        # ---------------------------------------------------------

        final_reply = str(
            twin_reply.get("reply_text", "")
        ).strip()

        # ---------------------------------------------------------
        # 6. Timings
        # ---------------------------------------------------------

        stt_seconds = float(
            timings.get("stt_seconds", 0.0)
        )

        decision_total_seconds = float(
            timings.get(
                "decision_total_seconds",
                0.0,
            )
        )

        decision_llm_seconds = float(
            timings.get(
                "decision_llm_seconds",
                0.0,
            )
        )

        tool_and_graph_seconds = float(
            timings.get(
                "tool_and_graph_seconds",
                0.0,
            )
        )

        answer_llm_seconds = float(
            timings.get(
                "answer_llm_seconds",
                0.0,
            )
        )

        speech_seconds = float(
            timings.get(
                "speech_seconds",
                0.0,
            )
        )

        total_seconds = float(
            timings.get(
                "total_seconds",
                0.0,
            )
        )

        timing_text = "\n".join(
            [
                f"STT: {stt_seconds:.3f}s",
                (
                    "Decision total: "
                    f"{decision_total_seconds:.3f}s"
                ),
                (
                    "Decision LLM: "
                    f"{decision_llm_seconds:.3f}s"
                ),
                (
                    "Tools + Graph: "
                    f"{tool_and_graph_seconds:.3f}s"
                ),
                (
                    "Answer LLM: "
                    f"{answer_llm_seconds:.3f}s"
                ),
                (
                    "Speech: "
                    f"{speech_seconds:.3f}s"
                ),
                (
                    "Total: "
                    f"{total_seconds:.3f}s"
                ),
            ]
        )

        # ---------------------------------------------------------
        # 7. Audio
        # ---------------------------------------------------------

        audio_output = result.get("audio")

        # ---------------------------------------------------------
        # Return everything to Gradio
        # ---------------------------------------------------------

        return (
            transcript_text,
            transcript_info,
            decision_text,
            tool_text,
            reply_json,
            timing_text,
            final_reply,
            audio_output,
        )

    except Exception as exc:
        error = (
            "Pipeline error:\n"
            f"{type(exc).__name__}: {exc}"
        )

        return (
            error,
            "",
            "",
            "[]",
            "{}",
            "",
            "",
            None,
        )


def clear_memory():
    """Clear the rolling conversation memory."""

    memory.clear()

    return "Memory cleared."


# ================================================================
# Gradio UI
# ================================================================

with gr.Blocks(
    title="Class Twin — Ahmed AI Twin",
) as demo:

    # ------------------------------------------------------------
    # Header
    # ------------------------------------------------------------

    gr.Markdown(
        """
# 🎓 Class Twin — Ahmed AI Twin

### Phase 1 — Tool-Using Voice Agent

A voice agent that listens to a recorded class question,
decides whether it should respond, retrieves relevant knowledge
and style examples, generates a grounded answer, and speaks it.

**Pipeline**

`🎤 Audio → 📝 STT → 🧠 Decision → 🔧 Tools → 💬 LLM → 🔊 Voice`
"""
    )

    # ------------------------------------------------------------
    # Responsible Use
    # ------------------------------------------------------------

    gr.Markdown(
        """
### ⚠️ Responsible Use

- Uses Ahmed's own voice samples only.
- The instructor should know that an AI twin is being used.
- Never use the twin for attendance.
- Never use it during quizzes or exams.
- Never use it to attend a meeting in Ahmed's place.
- Voice samples should not be committed to a public repository.
"""
    )

    # ------------------------------------------------------------
    # Input
    # ------------------------------------------------------------

    gr.Markdown("## 🎤 Input")

    audio_input = gr.Audio(
        sources=["upload", "microphone"],
        type="filepath",
        label="Class Question",
    )

    with gr.Row():

        run_button = gr.Button(
            "▶ Run Class Twin",
            variant="primary",
        )

        clear_button = gr.Button(
            "🧹 Clear Conversation Memory",
        )

    memory_status = gr.Textbox(
        label="Memory Status",
        interactive=False,
    )

    # ------------------------------------------------------------
    # 1. Transcription
    # ------------------------------------------------------------

    gr.Markdown("## 📝 1. Transcription")

    with gr.Row():

        transcript_output = gr.Textbox(
            label="Transcript",
            lines=6,
            interactive=False,
        )

        transcript_info = gr.Textbox(
            label="STT Metadata",
            lines=6,
            interactive=False,
        )

    # ------------------------------------------------------------
    # 2. Decision Tree
    # ------------------------------------------------------------

    gr.Markdown("## 🧠 2. Decision Tree")

    decision_output = gr.Textbox(
        label="Decision",
        lines=14,
        interactive=False,
    )

    # ------------------------------------------------------------
    # 3. Tools
    # ------------------------------------------------------------

    gr.Markdown("## 🔧 3. Tool Calls")

    tool_output = gr.Code(
        label="Tools + JSON Arguments",
        language="json",
    )

    # ------------------------------------------------------------
    # 4. TwinReply
    # ------------------------------------------------------------

    gr.Markdown("## 💬 4. TwinReply")

    reply_json_output = gr.Code(
        label="TwinReply JSON",
        language="json",
    )

    final_reply_output = gr.Textbox(
        label="Final Reply",
        lines=8,
        interactive=False,
    )

    # ------------------------------------------------------------
    # 5. Voice
    # ------------------------------------------------------------

    gr.Markdown("## 🔊 5. Twin Voice")

    audio_output = gr.Audio(
        label="Generated Response",
        type="filepath",
        interactive=False,
    )

    # ------------------------------------------------------------
    # 6. Timings
    # ------------------------------------------------------------

    gr.Markdown("## ⏱️ 6. Stage Timings")

    timing_output = gr.Textbox(
        label="Performance",
        lines=8,
        interactive=False,
    )

    # ------------------------------------------------------------
    # Events
    # ------------------------------------------------------------

    run_button.click(
        fn=process_audio,
        inputs=audio_input,
        outputs=[
            transcript_output,
            transcript_info,
            decision_output,
            tool_output,
            reply_json_output,
            timing_output,
            final_reply_output,
            audio_output,
        ],
    )

    clear_button.click(
        fn=clear_memory,
        inputs=[],
        outputs=memory_status,
    )


# ================================================================
# Launch
# ================================================================

if __name__ == "__main__":
    demo.launch()