from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class MemoryTurn:
    question: str
    reply: str


class RollingMemory:

    def __init__(self, max_turns: int = 5):
        self.turns = deque(maxlen=max_turns)

    def add(
        self,
        question: str,
        reply: str,
    ) -> None:

        self.turns.append(
            MemoryTurn(
                question=question,
                reply=reply,
            )
        )

    def get_context(self) -> list[dict[str, str]]:

        return [
            {
                "question": turn.question,
                "reply": turn.reply,
            }
            for turn in self.turns
        ]

    def is_empty(self) -> bool:
        return len(self.turns) == 0

    def clear(self) -> None:
        self.turns.clear()