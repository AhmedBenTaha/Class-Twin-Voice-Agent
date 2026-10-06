# Class Twin Phase 1 — Test Results

**Overall: 8/8 tests passed (100.0%).**

| Test | Expected | Actual | Confidence | Result |
|---|---|---|---:|---|
| T01 — English addressed question | `answer` | `answer` | 0.98 | ✅ PASS |
| T02 — Egyptian Arabic addressed question | `answer` | `answer` | 0.99 | ✅ PASS |
| T03 — Mixed language question | `answer` | `answer` | 0.92 | ✅ PASS |
| T04 — Question addressed to another person | `stay_silent` | `stay_silent` | 0.98 | ✅ PASS |
| T05 — Open question to the class | `defer` | `defer` | 0.85 | ✅ PASS |
| T06 — Follow-up memory | `answer` | `answer` | 0.90 | ✅ PASS |
| T07 — Outside knowledge | `defer` | `defer` | 0.85 | ✅ PASS |
| T08 — Low quality / unclear audio policy | `ask_to_repeat` | `ask_to_repeat` | 0.95 | ✅ PASS |

---

## Evaluation Scope

This evaluation covers the main Phase 1 decision behaviors:

```text
English
Egyptian Arabic
Mixed Arabic/English
Addressing detection
Open-class questions
Follow-up memory
Unsupported knowledge
Low-quality audio
```

The result represents performance on this **predefined 8-case test suite**. It is not a claim of perfect real-world accuracy.

---

# Detailed Results

## T01 — English Addressed Question

**Question:**

> Ahmed, what's the difference between RAG and fine-tuning?

- Expected action: `answer`
- Actual action: `answer`
- Addressed to Ahmed: `True`
- Language: `en`
- Confidence: `0.98`
- Follow-up: `False`

**Decision reason:**

> Question passed cheap checks and the LLM selected the highest-confidence action.

**Pruned branches:**

- `defer`
- `ask_to_repeat`
- `stay_silent`

**Remaining branches:**

- `answer`

**Tools used:**

- `search_my_notes`
- `get_style_examples`
- `get_profile`

**Sources:**

- `RAG`
- `fine-tuning`

**Timing:**

- decision_total_seconds: `1.157s`
- decision_llm_seconds: `1.157s`
- tool_and_graph_seconds: `0.059s`
- answer_llm_seconds: `1.712s`

---

## T02 — Egyptian Arabic Addressed Question

**Question:**

> يا أحمد، إيه الفرق بين الـ RAG والـ fine-tuning؟

- Expected action: `answer`
- Actual action: `answer`
- Addressed to Ahmed: `True`
- Language: `mixed`
- Confidence: `0.99`
- Follow-up: `False`

**Decision reason:**

> Question passed cheap checks and the LLM selected the highest-confidence action.

**Pruned branches:**

- `defer`
- `ask_to_repeat`
- `stay_silent`

**Remaining branches:**

- `answer`

**Tools used:**

- `search_my_notes`
- `get_style_examples`
- `get_profile`

**Sources:**

- `RAG`
- `fine-tuning`

**Timing:**

- decision_total_seconds: `0.726s`
- decision_llm_seconds: `0.726s`
- tool_and_graph_seconds: `0.008s`
- answer_llm_seconds: `1.236s`

---

## T03 — Mixed Language Question

**Question:**

> يا أحمد، ممكن تشرحلنا الـ pruning في الـ decision tree بيعمل إيه؟

- Expected action: `answer`
- Actual action: `answer`
- Addressed to Ahmed: `True`
- Language: `mixed`
- Confidence: `0.92`
- Follow-up: `False`

**Decision reason:**

> Question passed cheap checks and the LLM selected the highest-confidence action.

**Pruned branches:**

- `defer`
- `ask_to_repeat`
- `stay_silent`

**Remaining branches:**

- `answer`

**Tools used:**

- `search_my_notes`
- `get_style_examples`
- `get_profile`

**Sources:**

- `decision tree pruning`

**Timing:**

- decision_total_seconds: `0.816s`
- decision_llm_seconds: `0.816s`
- tool_and_graph_seconds: `0.014s`
- answer_llm_seconds: `1.215s`

---

## T04 — Question Addressed to Another Person

**Question:**

> Sara, can you share your screen?

- Expected action: `stay_silent`
- Actual action: `stay_silent`
- Addressed to Ahmed: `False`
- Language: `en`
- Confidence: `0.98`
- Follow-up: `False`

**Decision reason:**

> The question is addressed to another person.

**Pruned branches:**

- `answer`
- `ask_to_repeat`
- `defer`

**Remaining branches:**

- `stay_silent`

**Timing:**

- decision_total_seconds: `0.000s`
- decision_llm_seconds: `0.000s`

The deterministic addressing check handles this case without calling the decision LLM.

---

## T05 — Open Question to the Class

**Question:**

> Anyone? What does a CycleError mean?

- Expected action: `defer`
- Actual action: `defer`
- Addressed to Ahmed: `False`
- Language: `en`
- Confidence: `0.85`
- Follow-up: `False`

**Decision reason:**

> The topic is outside the current Phase 1 knowledge pack.

**Pruned branches:**

- `answer`
- `stay_silent`
- `ask_to_repeat`

**Remaining branches:**

- `defer`

**Timing:**

- decision_total_seconds: `0.000s`
- decision_llm_seconds: `0.000s`

The unsupported-topic check prevents unnecessary generation.

---

## T06 — Follow-up Memory

**Question:**

> Ahmed, and how is that different from what you said earlier?

- Expected action: `answer`
- Actual action: `answer`
- Addressed to Ahmed: `True`
- Language: `en`
- Confidence: `0.90`
- Follow-up: `True`

**Decision reason:**

> Question passed cheap checks and the LLM selected the highest-confidence action.

**Pruned branches:**

- `defer`
- `ask_to_repeat`
- `stay_silent`

**Remaining branches:**

- `answer`

**Tools used:**

- `search_my_notes`
- `get_style_examples`
- `get_profile`

**Sources:**

- `RAG`
- `previous conversation`

**Timing:**

- decision_total_seconds: `6.139s`
- decision_llm_seconds: `6.139s`
- tool_and_graph_seconds: `0.013s`
- answer_llm_seconds: `19.020s`

This test validates that the agent can use previous conversation context when the current question does not explicitly repeat the original topic.

---

## T07 — Outside Knowledge

**Question:**

> Ahmed, how did your assignment use Kubernetes?

- Expected action: `defer`
- Actual action: `defer`
- Addressed to Ahmed: `True`
- Language: `en`
- Confidence: `0.85`
- Follow-up: `False`

**Decision reason:**

> The topic is outside the current Phase 1 knowledge pack.

**Pruned branches:**

- `answer`
- `stay_silent`
- `ask_to_repeat`

**Remaining branches:**

- `defer`

**Timing:**

- decision_total_seconds: `0.000s`
- decision_llm_seconds: `0.000s`

This confirms that the system does not invent personal knowledge that is not present in the current knowledge pack.

---

## T08 — Low Quality / Unclear Audio

**Question:**

> `[UNCLEAR AUDIO]`

- Expected action: `ask_to_repeat`
- Actual action: `ask_to_repeat`
- Addressed to Ahmed: `False`
- Language: `en`
- Confidence: `0.95`
- Follow-up: `False`

**Decision reason:**

> Audio/transcription quality is too low.

**Pruned branches:**

- `answer`
- `defer`
- `stay_silent`

**Remaining branches:**

- `ask_to_repeat`

**Timing:**

- decision_total_seconds: `0.000s`
- decision_llm_seconds: `0.000s`

The quality check stops the pipeline before unnecessary reasoning or generation.

---

# Summary

```text
Tests     : 8
Passed    : 8
Failed    : 0
Accuracy  : 100.0%
```

## Behavior Coverage

```text
English question              ✅
Egyptian Arabic question      ✅
Mixed-language question       ✅
Addressing detection          ✅
Stay silent for another user  ✅
Open-class handling            ✅
Follow-up memory               ✅
Knowledge boundary             ✅
Low-quality audio handling     ✅
Branch pruning                 ✅
```

---

# Retrieval Configuration

The style retrieval used by the tested system is based on:

```text
FastEmbed
    ↓
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    ↓
384-dimensional embeddings
    ↓
ChromaDB
    ↓
Cosine similarity
```

The style dataset contains:

```text
17 real recorded Q&A examples
```

No synthetic recordings were added to replace missing examples.

---

# Interpretation

The evaluation demonstrates that the Phase 1 decision system correctly handles the tested scenarios while maintaining explicit safety boundaries.

The strongest demonstrated behaviors are:

1. **Selective answering** — the agent does not answer every question.
2. **Addressing awareness** — it stays silent when another person is addressed.
3. **Knowledge boundaries** — unsupported topics are deferred instead of guessed.
4. **Conversation memory** — follow-up questions can use previous context.
5. **Multilingual behavior** — English, Egyptian Arabic, and mixed technical language are supported.
6. **Quality gating** — unclear input is rejected before generation.
7. **Branch pruning** — low-confidence decision branches are removed before execution.

The `100%` result should be interpreted specifically as:

> **8 out of 8 predefined Phase 1 test scenarios passed successfully.**

It should not be interpreted as 100% accuracy across arbitrary classroom conversations.