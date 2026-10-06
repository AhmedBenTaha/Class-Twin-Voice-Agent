from __future__ import annotations

import json

import gradio as gr

from app.pipeline import run_pipeline
from app.reply_generator import memory


# ================================================================
# 1. Backend logic — preserved
# ================================================================

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
# 2. UI helper functions
# ================================================================

PIPELINE_STAGES = (
    ("AUDIO", "Capture", "◉"),
    ("TRANSCRIPTION", "STT", "≣"),
    ("DECISION", "Policy", "◆"),
    ("TOOLS", "Retrieval", "⚙"),
    ("RESPONSE", "LLM", "✦"),
    ("VOICE", "Speech", "♪"),
)


def hero_html() -> str:
    return """
    <div class="hero glass-card">
      <div class="hero-grid">
        <div class="hero-copy">
          <div class="hero-kicker">Ahmed AI Twin · Phase 1</div>
          <div class="hero-title">CLASS TWIN</div>
          <div class="hero-desc">
            A tool-using voice agent that listens, reasons, retrieves knowledge,
            generates a grounded response, and speaks it.
          </div>
          <div class="hero-meta">
            <span class="status-pill">
              <span class="dot"></span>
              AI TWIN ONLINE
            </span>
            <span class="hero-chip">Voice Agent</span>
            <span class="hero-chip">Tool Use</span>
            <span class="hero-chip">Knowledge Retrieval</span>
          </div>
        </div>

        <div class="orb-wrap" aria-hidden="true">
          <div class="orb-ring"></div>
          <div class="orb-ring-2"></div>
          <div class="scanline"></div>
          <div class="orb-core"></div>
        </div>
      </div>
    </div>
    """


def pipeline_html(active: bool = False, complete: bool = False) -> str:
    classes = "pipeline"

    if active:
        classes += " is-active"

    if complete:
        classes += " is-complete"

    stages = []

    for index, (title, label, icon) in enumerate(
        PIPELINE_STAGES,
        start=1,
    ):
        stages.append(
            f"""
            <div class="stage">
              <div class="stage-index">0{index}</div>
              <div class="stage-icon">{icon}</div>
              <div class="stage-title">{title}</div>
              <div class="stage-label">{label}</div>
            </div>
            """
        )

    return f"""
    <div class="{classes}">
      <div class="pipeline-line"></div>
      {''.join(stages)}
    </div>
    """


def status_html(state: str = "idle") -> str:
    states = {
        "idle": (
            "SYSTEM READY",
            "Awaiting a class question",
            "ready",
        ),
        "processing": (
            "AI TWIN IS THINKING",
            "Listening · deciding · retrieving · responding",
            "processing",
        ),
        "success": (
            "RESPONSE GENERATED",
            "Pipeline execution complete",
            "success",
        ),
        "warning": (
            "AWAITING AUDIO",
            "Upload or record a question before running",
            "warning",
        ),
        "error": (
            "PIPELINE ERROR",
            "Check the transcription panel for details",
            "error",
        ),
    }

    title, subtitle, css_state = states.get(
        state,
        states["idle"],
    )

    waves = "".join("<i></i>" for _ in range(7))

    return f"""
    <div class="status-banner {css_state}">
      <span class="status-dot"></span>
      <div class="status-copy">
        <div class="status-title">{title}</div>
        <div class="status-sub">{subtitle}</div>
      </div>
      <div class="status-waves">{waves}</div>
    </div>
    """


def memory_html(state: str = "active") -> str:
    if state == "cleared":
        return """
        <div class="memory-pill cleared">
          <span class="dot"></span>
          MEMORY CLEARED
        </div>
        """

    return """
    <div class="memory-pill active">
      <span class="dot"></span>
      MEMORY STATUS: ACTIVE
    </div>
    """


def section_header(title: str, subtitle: str = "") -> str:
    subtitle_html = (
        f'<div class="section-sub">{subtitle}</div>'
        if subtitle
        else ""
    )

    return f"""
    <div class="section-head">
      <div class="section-title">{title}</div>
      {subtitle_html}
    </div>
    """


def card_title(title: str, subtitle: str = "") -> str:
    return f"""
    <div class="card-title-row">
      <div class="card-title">{title}</div>
      <div class="card-sub">{subtitle}</div>
    </div>
    """


def footer_html() -> str:
    return """
    <footer class="footer">
      <div>CLASS TWIN · AHMED AI TWIN</div>
      <div>Phase 1 · Tool-Using Voice Agent</div>
      <div class="footer-tech">
        Built with Python · Gradio · LLMs · Voice AI
      </div>
    </footer>
    """


def _line_value(text: str, prefix: str) -> str:
    if not text:
        return ""

    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()

    return ""


def _between(text: str, start: str, end: str | None = None) -> str:
    if not text or start not in text:
        return ""

    after = text.split(start, 1)[1]

    if end and end in after:
        return after.split(end, 1)[0].strip()

    return after.strip()


def _bool_badge(value: str) -> str:
    normalized = str(value).strip().lower()

    if normalized in {"true", "yes", "1"}:
        return "YES"

    if normalized in {"false", "no", "0"}:
        return "NO"

    if not normalized:
        return "—"

    return str(value).strip().upper()


def _parse_transcript_info(info: str) -> tuple[str, str, str]:
    language = "—"
    whisper_language = "—"
    quality_score = "—"

    if not info:
        return language, whisper_language, quality_score

    for line in info.splitlines():
        clean = line.strip()
        lower = clean.lower()

        if lower.startswith("language:"):
            language = clean.split(":", 1)[1].strip() or "—"

        elif lower.startswith("whisper language:"):
            whisper_language = clean.split(":", 1)[1].strip() or "—"

        elif lower.startswith("quality score:"):
            quality_score = clean.split(":", 1)[1].strip() or "—"

    return language, whisper_language, quality_score


def _parse_decision(
    decision_text: str,
) -> tuple[str, str, str, str, str, str, str]:
    action = _line_value(decision_text, "Action:") or "—"
    addressed_raw = _line_value(
        decision_text,
        "Addressed to me:",
    )
    confidence = _line_value(
        decision_text,
        "Confidence:",
    ) or "—"
    followup_raw = _line_value(
        decision_text,
        "Follow-up:",
    )

    reason = (
        _between(
            decision_text,
            "Reason:\n",
            "\n\nPruned branches:",
        )
        or _line_value(decision_text, "Reason:")
        or "—"
    )

    pruned = (
        _between(
            decision_text,
            "Pruned branches:\n",
            "\n\nRemaining branches:",
        )
        or "[]"
    )

    remaining = (
        _between(
            decision_text,
            "Remaining branches:\n",
            None,
        )
        or "[]"
    )

    if action != "—":
        action = action.upper()

    addressed = _bool_badge(addressed_raw)
    followup = _bool_badge(followup_raw)

    return (
        action,
        addressed,
        confidence,
        followup,
        reason,
        pruned,
        remaining,
    )


def _parse_timings(
    timing_text: str,
) -> tuple[str, str, str, str, str, str, str]:
    values: dict[str, str] = {}

    if not timing_text:
        return ("—", "—", "—", "—", "—", "—", "—")

    for line in timing_text.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()

    return (
        values.get("STT", "—"),
        values.get("Decision total", "—"),
        values.get("Decision LLM", "—"),
        values.get("Tools + Graph", "—"),
        values.get("Answer LLM", "—"),
        values.get("Speech", "—"),
        values.get("Total", "—"),
    )


def start_run() -> tuple[str, str]:
    return (
        status_html("processing"),
        pipeline_html(active=True),
    )


def run_twin_ui(audio_path: str | None):
    """
    UI adapter around the preserved backend function.

    This does not change the pipeline behavior. It only reformats
    the existing backend outputs for the new dashboard.
    """

    (
        transcript_text,
        transcript_info,
        decision_text,
        tool_text,
        reply_json,
        timing_text,
        final_reply,
        audio_output,
    ) = process_audio(audio_path)

    (
        language,
        whisper_language,
        quality_score,
    ) = _parse_transcript_info(transcript_info)

    (
        action,
        addressed,
        confidence,
        followup,
        decision_reason,
        pruned,
        remaining,
    ) = _parse_decision(decision_text)

    (
        stt_time,
        decision_total_time,
        decision_llm_time,
        tools_graph_time,
        answer_time,
        speech_time,
        total_time,
    ) = _parse_timings(timing_text)

    clean_transcript = transcript_text.strip()

    if clean_transcript.startswith("Pipeline error:"):
        state = "error"

    elif clean_transcript == "No audio provided.":
        state = "warning"

    else:
        state = "success"

    return (
        status_html(state),
        pipeline_html(
            active=False,
            complete=state == "success",
        ),
        final_reply,
        audio_output,
        transcript_text,
        language,
        whisper_language,
        quality_score,
        action,
        confidence,
        addressed,
        followup,
        decision_reason,
        pruned,
        remaining,
        tool_text,
        reply_json,
        stt_time,
        decision_total_time,
        decision_llm_time,
        tools_graph_time,
        answer_time,
        speech_time,
        total_time,
        transcript_info,
        decision_text,
        timing_text,
    )


def clear_memory_ui() -> tuple[str, str, str, str]:
    """
    UI wrapper around the preserved clear_memory backend function.
    """

    message = clear_memory()

    memory_state = (
        "cleared"
        if "clear" in message.lower()
        else "active"
    )

    return (
        memory_html(memory_state),
        message,
        status_html("idle"),
        pipeline_html(),
    )


# ================================================================
# 3. Custom CSS
# ================================================================

APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg: #040711;
  --panel: rgba(9, 14, 28, 0.66);
  --panel-2: rgba(13, 20, 38, 0.44);
  --line: rgba(148, 163, 184, 0.14);
  --cyan: #22d3ee;
  --blue: #3b82f6;
  --violet: #8b5cf6;
  --text: #e5eefb;
  --muted: #94a3b8;
  --success: #34d399;
  --warning: #fbbf24;
  --danger: #fb7185;
  --radius: 22px;
}

html,
body,
.gradio-container {
  background: #040711;
}

body {
  margin: 0;
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background:
    radial-gradient(circle at 15% 18%, rgba(34, 211, 238, 0.13), transparent 30%),
    radial-gradient(circle at 82% 12%, rgba(139, 92, 246, 0.12), transparent 24%),
    radial-gradient(circle at 78% 78%, rgba(59, 130, 246, 0.10), transparent 28%),
    linear-gradient(180deg, #040711 0%, #070b17 48%, #050810 100%);
  background-attachment: fixed;
}

.gradio-container {
  max-width: 1280px !important;
  margin: 0 auto !important;
  padding: 24px 20px 42px !important;
  position: relative;
}

.gradio-container::before {
  content: "";
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.055) 1px, transparent 1px);
  background-size: 52px 52px;
  mask-image: radial-gradient(circle at 50% 20%, black 0%, transparent 78%);
  pointer-events: none;
  z-index: 0;
}

.gradio-container > * {
  position: relative;
  z-index: 1;
}

/* Global Gradio panel cleanup */
.gradio-container .block {
  background: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
}

.gradio-container .form {
  background: rgba(3, 7, 18, 0.42) !important;
  border: 1px solid rgba(148, 163, 184, 0.12) !important;
  border-radius: 18px !important;
  box-shadow: none !important;
}

.gradio-container label,
.gradio-container label > span,
.gradio-container .label {
  color: #cbd5e1 !important;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.gradio-container textarea,
.gradio-container input,
.gradio-container select {
  background: rgba(2, 5, 13, 0.55) !important;
  color: var(--text) !important;
  border: 1px solid rgba(148, 163, 184, 0.12) !important;
  border-radius: 16px !important;
}

.gradio-container textarea {
  line-height: 1.6;
}

.gradio-container .wrap,
.gradio-container .output-class,
.gradio-container [data-testid="audio"],
.gradio-container .audio-container {
  background: rgba(2, 5, 13, 0.35) !important;
  border-radius: 18px !important;
  border: 1px solid rgba(148, 163, 184, 0.10) !important;
}

/* Glass cards */
.glass-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02)),
    var(--panel);
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: var(--radius);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.glass-card:hover {
  border-color: rgba(34, 211, 238, 0.22);
}

/* Hero */
.hero {
  position: relative;
  overflow: hidden;
  padding: 32px;
  border-radius: 32px;
  margin-bottom: 18px;
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.hero::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 80% 20%, rgba(34, 211, 238, 0.16), transparent 28%),
    radial-gradient(circle at 20% 80%, rgba(139, 92, 246, 0.14), transparent 30%);
  pointer-events: none;
}

.hero-grid {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  position: relative;
}

.hero-copy {
  max-width: 780px;
}

.hero-kicker {
  color: var(--cyan);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}

.hero-title {
  margin: 10px 0 12px;
  font-size: 56px;
  line-height: 1.02;
  font-weight: 800;
  letter-spacing: -0.04em;
  background: linear-gradient(90deg, #ffffff, #93c5fd, #67e8f9);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-desc {
  max-width: 760px;
  color: var(--muted);
  font-size: 16px;
  line-height: 1.7;
  margin: 0 0 18px;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.hero-chip,
.status-pill,
.memory-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  background: rgba(255, 255, 255, 0.02);
}

.status-pill {
  border-color: rgba(52, 211, 153, 0.28);
  color: #a7f3d0;
  background: rgba(52, 211, 153, 0.08);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  background: var(--success);
  box-shadow: 0 0 12px var(--success);
  animation: pulse 2s infinite;
}

.hero-chip {
  color: #dbeafe;
}

/* Orb */
.orb-wrap {
  position: relative;
  width: 150px;
  height: 150px;
  flex: 0 0 auto;
}

.orb-core {
  position: absolute;
  inset: 26px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 30%,
      rgba(255, 255, 255, 0.72),
      rgba(34, 211, 238, 0.92) 35%,
      rgba(59, 130, 246, 0.72) 62%,
      rgba(139, 92, 246, 0.5) 100%);
  box-shadow: 0 0 50px rgba(34, 211, 238, 0.28);
  animation: breathe 5s ease-in-out infinite;
}

.orb-ring,
.orb-ring-2 {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(34, 211, 238, 0.28);
}

.orb-ring {
  inset: 0;
  animation: spin 16s linear infinite;
}

.orb-ring::before {
  content: "";
  position: absolute;
  top: -3px;
  left: 50%;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--cyan);
  box-shadow: 0 0 12px var(--cyan);
}

.orb-ring-2 {
  inset: 13px;
  border-color: rgba(139, 92, 246, 0.24);
  animation: spin 10s linear infinite reverse;
}

.scanline {
  position: absolute;
  inset: 15px;
  border-radius: 50%;
  overflow: hidden;
}

.scanline::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  height: 22px;
  background: linear-gradient(180deg, transparent, rgba(34, 211, 238, 0.12), transparent);
  animation: scan 4.5s linear infinite;
}

/* Pipeline */
.pipeline {
  position: relative;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  padding: 18px;
  border-radius: 26px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02)),
    rgba(7, 11, 24, 0.58);
  backdrop-filter: blur(18px);
  overflow: hidden;
  margin-bottom: 14px;
}

.pipeline-line {
  position: absolute;
  left: 4%;
  right: 4%;
  top: 50%;
  height: 2px;
  transform: translateY(-50%);
  background: linear-gradient(90deg,
    transparent,
    rgba(34, 211, 238, 0.22),
    rgba(59, 130, 246, 0.22),
    transparent);
  z-index: 0;
}

.pipeline.is-active .pipeline-line {
  height: 3px;
  background: linear-gradient(90deg,
    transparent,
    rgba(34, 211, 238, 0.65),
    rgba(59, 130, 246, 0.65),
    transparent);
  background-size: 200% 100%;
  animation: flow 1.4s linear infinite;
  box-shadow: 0 0 18px rgba(34, 211, 238, 0.22);
}

.stage {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 120px;
  padding: 14px 8px;
  border-radius: 18px;
  background: rgba(4, 8, 18, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.12);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.stage:hover {
  transform: translateY(-2px);
  border-color: rgba(34, 211, 238, 0.24);
}

.pipeline.is-active .stage {
  border-color: rgba(34, 211, 238, 0.25);
  box-shadow: 0 0 24px rgba(34, 211, 238, 0.05);
}

.pipeline.is-complete .stage {
  border-color: rgba(52, 211, 153, 0.22);
}

.pipeline.is-complete .stage-icon {
  border-color: rgba(52, 211, 153, 0.3);
  color: #a7f3d0;
  background: rgba(52, 211, 153, 0.08);
}

.stage-index {
  position: absolute;
  top: 10px;
  right: 12px;
  color: rgba(148, 163, 184, 0.55);
  font-size: 10px;
  letter-spacing: 0.18em;
}

.stage-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid rgba(34, 211, 238, 0.22);
  background: rgba(34, 211, 238, 0.08);
  color: var(--cyan);
  font-size: 17px;
  box-shadow: inset 0 0 18px rgba(34, 211, 238, 0.06);
}

.stage-title {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.stage-label {
  color: var(--muted);
  font-size: 11px;
  text-align: center;
}

/* Status banner */
.status-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(6, 10, 22, 0.62);
  backdrop-filter: blur(16px);
  margin-bottom: 22px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--cyan);
  box-shadow: 0 0 16px var(--cyan);
  animation: pulse 2s infinite;
}

.success .status-dot {
  background: var(--success);
  box-shadow: 0 0 16px var(--success);
}

.warning .status-dot {
  background: var(--warning);
  box-shadow: 0 0 16px var(--warning);
}

.error .status-dot {
  background: var(--danger);
  box-shadow: 0 0 16px var(--danger);
}

.status-title {
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

.status-sub {
  color: var(--muted);
  font-size: 13px;
  margin-top: 3px;
}

.status-waves {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
  height: 34px;
}

.status-waves i {
  width: 3px;
  height: 12px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.35);
}

.processing .status-waves i {
  background: linear-gradient(180deg, var(--cyan), var(--blue));
  animation: wave 1.2s ease-in-out infinite;
}

.processing .status-waves i:nth-child(2) { animation-delay: 0.1s; }
.processing .status-waves i:nth-child(3) { animation-delay: 0.2s; }
.processing .status-waves i:nth-child(4) { animation-delay: 0.3s; }
.processing .status-waves i:nth-child(5) { animation-delay: 0.4s; }
.processing .status-waves i:nth-child(6) { animation-delay: 0.5s; }
.processing .status-waves i:nth-child(7) { animation-delay: 0.6s; }

/* Sections */
.section-head {
  margin-bottom: 18px;
}

.section-title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.section-sub {
  color: var(--muted);
  margin-top: 6px;
  line-height: 1.5;
}

.card-title-row {
  margin-bottom: 14px;
}

.card-title {
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #dbeafe;
}

.card-sub {
  color: var(--muted);
  font-size: 12px;
  margin-top: 4px;
}

/* Ask card */
.ask-card {
  padding: 22px;
  margin-bottom: 22px;
  border: 1px solid rgba(34, 211, 238, 0.18);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.35),
    0 0 50px rgba(34, 211, 238, 0.06);
}

.controls-row {
  margin-top: 16px;
  gap: 12px;
}

.controls-row button,
.gradio-container .gr-button {
  width: 100%;
  min-height: 54px;
  border-radius: 18px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.run-btn,
.run-btn button,
button.run-btn {
  background:
    linear-gradient(90deg,
      rgba(34, 211, 238, 0.18),
      rgba(59, 130, 246, 0.22)) !important;
  border: 1px solid rgba(34, 211, 238, 0.4) !important;
  color: #ffffff !important;
  box-shadow: 0 0 30px rgba(34, 211, 238, 0.12) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.run-btn:hover,
.run-btn:hover button,
button.run-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 0 40px rgba(34, 211, 238, 0.22) !important;
  border-color: rgba(34, 211, 238, 0.6) !important;
}

.ghost-btn,
.ghost-btn button,
button.ghost-btn {
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  color: var(--muted) !important;
  transition: border-color 0.2s ease, color 0.2s ease;
}

.ghost-btn:hover,
.ghost-btn:hover button,
button.ghost-btn:hover {
  border-color: rgba(148, 163, 184, 0.42) !important;
  color: var(--text) !important;
}

.memory-pill {
  margin-top: 14px;
}

.memory-pill.active .dot {
  background: var(--cyan);
  box-shadow: 0 0 12px var(--cyan);
}

.memory-pill.cleared {
  color: #a7f3d0;
  border-color: rgba(52, 211, 153, 0.28);
  background: rgba(52, 211, 153, 0.08);
}

.memory-pill.cleared .dot {
  background: var(--success);
  box-shadow: 0 0 12px var(--success);
}

/* Results */
.results-row {
  margin-bottom: 22px;
}

.response-card,
.voice-card,
.tabs-card,
.inner-panel {
  padding: 20px;
}

.response-text textarea,
.response-text .output-class {
  font-size: 18px !important;
  line-height: 1.75 !important;
  color: #f8fbff !important;
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid rgba(34, 211, 238, 0.12) !important;
  min-height: 220px !important;
}

.metric-chip textarea,
.metric-chip .output-class {
  text-align: center;
  font-family: JetBrains Mono, ui-monospace, monospace;
  font-size: 14px;
}

.metric-card textarea,
.metric-card .output-class {
  text-align: center;
  font-family: JetBrains Mono, ui-monospace, monospace;
  font-size: 20px;
  color: #e0f2fe;
}

.metric-total textarea,
.metric-total .output-class {
  font-size: 28px;
  color: #67e8f9;
}

/* Tabs */
.tabs-card {
  margin-bottom: 22px;
}

.gradio-container .tab-nav {
  gap: 8px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 16px;
}

.gradio-container .tab-nav button {
  background: transparent !important;
  border: 1px solid transparent !important;
  color: var(--muted) !important;
  border-radius: 12px !important;
  padding: 10px 14px !important;
  text-transform: uppercase;
  font-size: 12px;
  letter-spacing: 0.14em;
}

.gradio-container .tab-nav button.selected {
  color: var(--text) !important;
  background: rgba(34, 211, 238, 0.09) !important;
  border-color: rgba(34, 211, 238, 0.24) !important;
}

/* Code panels */
.gradio-container .cm-editor {
  background: rgba(2, 5, 13, 0.6) !important;
  border: 1px solid rgba(148, 163, 184, 0.12) !important;
  border-radius: 16px !important;
}

.gradio-container .cm-editor .cm-content,
.gradio-container .cm-editor .cm-line {
  color: #d7e5ff !important;
  font-family: JetBrains Mono, ui-monospace, monospace !important;
}

.gradio-container .cm-editor .cm-gutters {
  background: transparent !important;
  border-right: 1px solid rgba(148, 163, 184, 0.08) !important;
  color: #64748b !important;
}

.code-panel .cm-scroller {
  max-height: 360px;
  overflow: auto;
}

/* Accordion */
.gradio-container .accordion,
.gradio-container [data-testid="accordion"] {
  background: rgba(2, 5, 13, 0.35) !important;
  border: 1px solid rgba(148, 163, 184, 0.12) !important;
  border-radius: 16px !important;
  margin-top: 10px;
}

/* Footer */
.footer {
  margin-top: 28px;
  padding: 22px;
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(6, 10, 22, 0.44);
  text-align: center;
  color: var(--muted);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-size: 11px;
  display: grid;
  gap: 8px;
}

.footer-tech {
  color: rgba(148, 163, 184, 0.62);
}

/* Animations */
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.72;
  }
}

@keyframes breathe {
  0%, 100% {
    transform: scale(0.96);
    box-shadow: 0 0 36px rgba(34, 211, 238, 0.16);
  }
  50% {
    transform: scale(1.04);
    box-shadow: 0 0 60px rgba(34, 211, 238, 0.3);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes scan {
  0% {
    transform: translateY(-120%);
  }
  100% {
    transform: translateY(420%);
  }
}

@keyframes flow {
  0% {
    background-position: 0% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

@keyframes wave {
  0%, 100% {
    transform: scaleY(0.5);
    opacity: 0.5;
  }
  50% {
    transform: scaleY(1.6);
    opacity: 1;
  }
}

/* Responsive */
@media (max-width: 1000px) {
  .hero-grid {
    flex-direction: column;
    align-items: flex-start;
  }

  .orb-wrap {
    margin-top: 12px;
  }

  .pipeline {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .pipeline-line {
    display: none;
  }
}

@media (max-width: 700px) {
  .hero-title {
    font-size: 34px;
  }

  .pipeline {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .gradio-container {
    padding: 14px 12px 28px !important;
  }
}

@media (max-width: 900px) {
  .gradio-container .row {
    flex-direction: column !important;
  }

  .gradio-container .row > div {
    min-width: 100% !important;
  }
}
"""


# ================================================================
# 4. Gradio layout
# ================================================================

with gr.Blocks(
    title="Class Twin — Ahmed AI Twin",
    css=APP_CSS,
) as demo:

    # ------------------------------------------------------------
    # Hero + pipeline + status
    # ------------------------------------------------------------

    gr.HTML(hero_html())

    pipeline_view = gr.HTML(
        pipeline_html(),
    )

    status_view = gr.HTML(
        status_html("idle"),
    )

    # ------------------------------------------------------------
    # Ask the Twin
    # ------------------------------------------------------------

    with gr.Column(
        elem_classes=["glass-card", "ask-card"],
    ):
        gr.HTML(
            section_header(
                "ASK THE TWIN",
                "Upload a class question or record one using the microphone.",
            )
        )

        audio_input = gr.Audio(
            sources=["upload", "microphone"],
            type="filepath",
            label="Class Question",
            elem_classes=["audio-input"],
        )

        with gr.Row(elem_classes=["controls-row"]):
            run_button = gr.Button(
                "▶ RUN CLASS TWIN",
                variant="primary",
                elem_classes=["run-btn"],
            )

            clear_button = gr.Button(
                "CLEAR MEMORY",
                elem_classes=["ghost-btn"],
            )

        memory_view = gr.HTML(
            memory_html("active"),
        )

        hidden_memory = gr.Textbox(
            visible=False,
            value="",
        )

    # ------------------------------------------------------------
    # Primary result
    # ------------------------------------------------------------

    with gr.Row(elem_classes=["results-row"]):
        with gr.Column(
            scale=3,
            elem_classes=["glass-card", "response-card"],
        ):
            gr.HTML(
                card_title(
                    "TWIN RESPONSE",
                    "Primary grounded answer generated by Ahmed's AI Twin.",
                )
            )

            final_reply_output = gr.Textbox(
                show_label=False,
                lines=8,
                interactive=False,
                placeholder="Run the pipeline to generate Ahmed's answer.",
                elem_classes=["response-text"],
            )

        with gr.Column(
            scale=2,
            elem_classes=["glass-card", "voice-card"],
        ):
            gr.HTML(
                card_title(
                    "GENERATED VOICE",
                    "Synthesized response audio.",
                )
            )

            audio_output = gr.Audio(
                label="Generated Response",
                type="filepath",
                interactive=False,
                show_label=False,
                elem_classes=["audio-output"],
            )

    # ------------------------------------------------------------
    # Technical dashboard
    # ------------------------------------------------------------

    with gr.Column(
        elem_classes=["glass-card", "tabs-card"],
    ):
        with gr.Tabs():

            # ----------------------------------------------------
            # Transcription + Decision
            # ----------------------------------------------------

            with gr.Tab("Transcription & Decision"):
                with gr.Row():
                    with gr.Column(
                        scale=1,
                        elem_classes=["inner-panel"],
                    ):
                        gr.HTML(
                            card_title(
                                "TRANSCRIPTION",
                                "Speech-to-text result and STT metadata.",
                            )
                        )

                        transcript_output = gr.Textbox(
                            label="Transcript",
                            lines=8,
                            interactive=False,
                            elem_classes=["transcript-text"],
                        )

                        with gr.Row():
                            stt_language_output = gr.Textbox(
                                label="Language",
                                interactive=False,
                                elem_classes=["metric-chip"],
                            )

                            stt_whisper_output = gr.Textbox(
                                label="Whisper",
                                interactive=False,
                                elem_classes=["metric-chip"],
                            )

                            stt_quality_output = gr.Textbox(
                                label="Quality",
                                interactive=False,
                                elem_classes=["metric-chip"],
                            )

                    with gr.Column(
                        scale=1,
                        elem_classes=["inner-panel"],
                    ):
                        gr.HTML(
                            card_title(
                                "DECISION ENGINE",
                                "Response policy, routing, and confidence.",
                            )
                        )

                        with gr.Row():
                            decision_action_output = gr.Textbox(
                                label="Action",
                                interactive=False,
                                elem_classes=["metric-chip"],
                            )

                            decision_confidence_output = gr.Textbox(
                                label="Confidence",
                                interactive=False,
                                elem_classes=["metric-chip"],
                            )

                        with gr.Row():
                            decision_addressed_output = gr.Textbox(
                                label="Addressed to Ahmed",
                                interactive=False,
                                elem_classes=["metric-chip"],
                            )

                            decision_followup_output = gr.Textbox(
                                label="Follow-up",
                                interactive=False,
                                elem_classes=["metric-chip"],
                            )

                        decision_reason_output = gr.Textbox(
                            label="Decision reason",
                            lines=4,
                            interactive=False,
                        )

                        with gr.Accordion(
                            "Pruned branches",
                            open=False,
                        ):
                            pruned_output = gr.Code(
                                label="Pruned branches",
                                language="json",
                                show_label=False,
                                elem_classes=["code-panel"],
                            )

                        with gr.Accordion(
                            "Remaining branches",
                            open=False,
                        ):
                            remaining_output = gr.Code(
                                label="Remaining branches",
                                language="json",
                                show_label=False,
                                elem_classes=["code-panel"],
                            )

            # ----------------------------------------------------
            # Agent console
            # ----------------------------------------------------

            with gr.Tab("Agent Console"):
                gr.HTML(
                    card_title(
                        "TOOL CALLS",
                        "Retrieval and tool execution arguments.",
                    )
                )

                tool_output = gr.Code(
                    label="Tools + JSON Arguments",
                    language="json",
                    show_label=False,
                    elem_classes=["code-panel"],
                )

                gr.HTML(
                    card_title(
                        "TWIN REPLY",
                        "Full structured TwinReply object.",
                    )
                )

                reply_json_output = gr.Code(
                    label="TwinReply JSON",
                    language="json",
                    show_label=False,
                    elem_classes=["code-panel"],
                )

            # ----------------------------------------------------
            # Performance
            # ----------------------------------------------------

            with gr.Tab("Performance"):
                gr.HTML(
                    card_title(
                        "PERFORMANCE METRICS",
                        "Actual stage timings returned by the pipeline.",
                    )
                )

                with gr.Row():
                    stt_metric = gr.Textbox(
                        label="STT",
                        interactive=False,
                        elem_classes=["metric-card"],
                    )

                    decision_total_metric = gr.Textbox(
                        label="Decision Total",
                        interactive=False,
                        elem_classes=["metric-card"],
                    )

                    decision_llm_metric = gr.Textbox(
                        label="Decision LLM",
                        interactive=False,
                        elem_classes=["metric-card"],
                    )

                with gr.Row():
                    tool_graph_metric = gr.Textbox(
                        label="Tools + Graph",
                        interactive=False,
                        elem_classes=["metric-card"],
                    )

                    answer_metric = gr.Textbox(
                        label="Answer LLM",
                        interactive=False,
                        elem_classes=["metric-card"],
                    )

                    speech_metric = gr.Textbox(
                        label="Speech",
                        interactive=False,
                        elem_classes=["metric-card"],
                    )

                total_metric = gr.Textbox(
                    label="Total Latency",
                    interactive=False,
                    elem_classes=["metric-card", "metric-total"],
                )

    # ------------------------------------------------------------
    # Responsible use
    # ------------------------------------------------------------

    with gr.Accordion(
        "Responsible Use",
        open=False,
    ):
        gr.Markdown(
            """
- Uses Ahmed's own voice samples only.
- The instructor should know that an AI twin is being used.
- Never use the twin for attendance.
- Never use it during quizzes or exams.
- Never use it to attend a meeting in Ahmed's place.
- Voice samples should not be committed to a public repository.
"""
        )

    # ------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------

    gr.HTML(footer_html())

    # ------------------------------------------------------------
    # Hidden preserved original outputs
    # ------------------------------------------------------------

    hidden_transcript_info = gr.Textbox(visible=False)
    hidden_decision = gr.Textbox(visible=False)
    hidden_timing = gr.Textbox(visible=False)

    # ------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------

    run_outputs = [
        status_view,
        pipeline_view,
        final_reply_output,
        audio_output,
        transcript_output,
        stt_language_output,
        stt_whisper_output,
        stt_quality_output,
        decision_action_output,
        decision_confidence_output,
        decision_addressed_output,
        decision_followup_output,
        decision_reason_output,
        pruned_output,
        remaining_output,
        tool_output,
        reply_json_output,
        stt_metric,
        decision_total_metric,
        decision_llm_metric,
        tool_graph_metric,
        answer_metric,
        speech_metric,
        total_metric,
        hidden_transcript_info,
        hidden_decision,
        hidden_timing,
    ]

    run_button.click(
        fn=start_run,
        inputs=[],
        outputs=[
            status_view,
            pipeline_view,
        ],
    ).then(
        fn=run_twin_ui,
        inputs=audio_input,
        outputs=run_outputs,
    )

    clear_button.click(
        fn=clear_memory_ui,
        inputs=[],
        outputs=[
            memory_view,
            hidden_memory,
            status_view,
            pipeline_view,
        ],
    )


# ================================================================
# 5. Launch
# ================================================================

if __name__ == "__main__":
    demo.queue()
    demo.launch()