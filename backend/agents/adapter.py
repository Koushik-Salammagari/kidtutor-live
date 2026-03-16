"""
Reads kid signals (confusion, engagement) and returns emotion state for the character.
Used by the Live API agent to adapt expression (e.g. show "thinking" when kid is confused).
"""
from typing import TypedDict

# Emotion states per CURSOR_CONTEXT.md Image Command Protocol
EMOTION_STATES = ("neutral", "happy", "thinking", "surprised", "question")


class KidSignals(TypedDict, total=False):
    """Signals we can derive from the kid's input (voice, barge-in, etc.)."""
    confusion: float   # 0.0–1.0
    engagement: float  # 0.0–1.0
    asked_question: bool
    correct_answer: bool


def signals_to_emotion(signals: KidSignals) -> str:
    """
    Map kid signals to a character emotion state.
    Returns one of: neutral, happy, thinking, surprised, question.
    """
    confusion = signals.get("confusion", 0.0)
    engagement = signals.get("engagement", 0.5)
    asked_question = signals.get("asked_question", False)
    correct_answer = signals.get("correct_answer", False)

    if correct_answer:
        return "happy"
    if asked_question:
        return "question"
    if confusion > 0.6:
        return "thinking"
    if confusion > 0.3:
        return "surprised"
    if engagement > 0.7:
        return "happy"
    return "neutral"
