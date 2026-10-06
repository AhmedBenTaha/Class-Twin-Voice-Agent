# Class Twin Phase 1 — Test Results

**Overall:** 8/8 tests passed (100.0%).

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

## Detailed Results

### T01 — English addressed question

**Question:** Ahmed, what's the difference between RAG and fine-tuning?

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

### T02 — Egyptian Arabic addressed question

**Question:** يا أحمد، إيه الفرق بين الـ RAG والـ fine-tuning؟

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

### T03 — Mixed language question

**Question:** يا أحمد، ممكن تشرحلنا الـ pruning في الـ decision tree بيعمل إيه؟

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

### T04 — Question addressed to another person

**Question:** Sara, can you share your screen?

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

---

### T05 — Open question to the class

**Question:** Anyone? What does a CycleError mean?

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

---

### T06 — Follow-up memory

**Question:** Ahmed, and how is that different from what you said earlier?

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

---

### T07 — Outside knowledge

**Question:** Ahmed, how did your assignment use Kubernetes?

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

---

### T08 — Low quality / unclear audio policy

**Question:** [UNCLEAR AUDIO]

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

---
