"""
Conversation State Machine
Deterministic conversation flow with state transitions based on intent
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import re


class ConversationState(Enum):
    """All possible conversation states"""
    IDLE = "IDLE"
    ASKING_MOOD = "ASKING_MOOD"
    ASKING_SLEEP = "ASKING_SLEEP"
    ASKING_MEALS = "ASKING_MEALS"
    ASKING_SOCIAL_CONNECTION = "ASKING_SOCIAL_CONNECTION"
    ASKING_ASSISTANCE = "ASKING_ASSISTANCE"
    ASKING_ANYTHING_ELSE = "ASKING_ANYTHING_ELSE"
    FOLLOW_UP = "FOLLOW_UP"
    URGENT_WORKFLOW = "URGENT_WORKFLOW"
    COMPLETED = "COMPLETED"
    ERROR_RECOVERY = "ERROR_RECOVERY"


class ConversationStateMachine:
    """
    Manages conversation state transitions
    Deterministic decision tree based on intent classification
    """

    # Base questions sequence
    BASE_QUESTIONS = {
        ConversationState.ASKING_MOOD: "How are you feeling today?",
        ConversationState.ASKING_SLEEP: "Did you sleep well last night?",
        ConversationState.ASKING_MEALS: "Have you eaten your meals today?",
        ConversationState.ASKING_SOCIAL_CONNECTION: "Have you spoken with someone today?",
        ConversationState.ASKING_ASSISTANCE: "Is there anything you need help with today?",
        ConversationState.ASKING_ANYTHING_ELSE: "Is there anything else you'd like me to share with your caregiver?"
    }

    # Follow-up questions based on intent
    FOLLOW_UP_QUESTIONS = {
        "LONELY": "Would you like me to help you contact someone?",
        "PHYSICAL_DISCOMFORT": "Would you like help contacting your caregiver about this?",
        "NEGATIVE": "Would you like to tell me what is troubling you?",
        "ASSISTANCE_NEEDED": "What kind of help do you need?"
    }

    # State sequence for normal flow
    STATE_SEQUENCE = [
        ConversationState.ASKING_MOOD,
        ConversationState.ASKING_SLEEP,
        ConversationState.ASKING_MEALS,
        ConversationState.ASKING_SOCIAL_CONNECTION,
        ConversationState.ASKING_ASSISTANCE,
        ConversationState.ASKING_ANYTHING_ELSE
    ]


    def __init__(self, conversation_id: str, senior_id: str):
        self.conversation_id = conversation_id
        self.senior_id = senior_id
        self.current_state = ConversationState.IDLE
        self.current_topic = None
        self.question_index = 0
        self.follow_up_intent = None
        self.completed_states = set()


    def start_conversation(self) -> Dict[str, Any]:
        """
        Start a new conversation
        Returns first question
        """
        self.current_state = ConversationState.ASKING_MOOD
        self.current_topic = "MOOD"
        self.question_index = 0

        return {
            "state": self.current_state.value,
            "topic": self.current_topic,
            "question": self.BASE_QUESTIONS[self.current_state]
        }


    def transition(self, intent: str, user_message: str = "") -> Dict[str, Any]:
        """
        Determine next state based on current state and intent
        Returns: {state, topic, question, action}
        """

        # URGENT_SYMPTOM always interrupts
        if intent == "URGENT_SYMPTOM":
            self.current_state = ConversationState.URGENT_WORKFLOW
            return {
                "state": self.current_state.value,
                "topic": "URGENT",
                "question": None,
                "action": "trigger_urgent_workflow"
            }

        # The last turn is a clear yes/no invitation to add a caregiver note.
        # Preserve every non-empty answer verbatim, except an explicit "nothing else".
        if self.current_state == ConversationState.ASKING_ANYTHING_ELSE:
            self.completed_states.add(self.current_state)
            self.current_state = ConversationState.COMPLETED
            has_no_more = self._is_explicit_no_more(user_message)
            return {
                "state": self.current_state.value,
                "topic": "END",
                "question": None,
                "action": "generate_summary",
                "caregiver_note": None if has_no_more else user_message.strip() or None
            }

        # Handle based on current state
        if self.current_state == ConversationState.URGENT_WORKFLOW:
            # Stay in urgent workflow
            return {
                "state": self.current_state.value,
                "topic": "URGENT",
                "question": None,
                "action": "continue_urgent_workflow"
            }

        # Handle FOLLOW_UP state
        if self.current_state == ConversationState.FOLLOW_UP:
            # After follow-up, return to normal flow
            self.current_state = self._get_next_base_state()
            self.follow_up_intent = None

            if self.current_state == ConversationState.COMPLETED:
                return {
                    "state": self.current_state.value,
                    "topic": "END",
                    "question": None,
                    "action": "generate_summary"
                }

            return {
                "state": self.current_state.value,
                "topic": self._state_to_topic(self.current_state),
                "question": self.BASE_QUESTIONS[self.current_state],
                "action": "continue"
            }

        # Check if intent requires follow-up
        if intent in ["LONELY", "PHYSICAL_DISCOMFORT", "NEGATIVE", "ASSISTANCE_NEEDED"]:
            # Mark current state as completed
            self.completed_states.add(self.current_state)

            # Go to follow-up
            self.follow_up_intent = intent
            self.current_state = ConversationState.FOLLOW_UP
            self.current_topic = intent

            return {
                "state": self.current_state.value,
                "topic": self.current_topic,
                "question": self.FOLLOW_UP_QUESTIONS.get(intent, "Could you tell me more about that?"),
                "action": "follow_up"
            }

        # Normal positive/neutral response - move to next question
        if intent in ["POSITIVE", "SKIP", "UNCLEAR", "OTHER"]:
            # Mark current state as completed
            self.completed_states.add(self.current_state)

            # Move to next state
            self.current_state = self._get_next_base_state()

            if self.current_state == ConversationState.COMPLETED:
                return {
                    "state": self.current_state.value,
                    "topic": "END",
                    "question": None,
                    "action": "generate_summary"
                }

            return {
                "state": self.current_state.value,
                "topic": self._state_to_topic(self.current_state),
                "question": self.BASE_QUESTIONS[self.current_state],
                "action": "continue"
            }

        # Fallback — still move forward so we never get stuck
        self.completed_states.add(self.current_state)
        self.current_state = self._get_next_base_state()

        if self.current_state == ConversationState.COMPLETED:
            return {
                "state": self.current_state.value,
                "topic": "END",
                "question": None,
                "action": "generate_summary"
            }

        return {
            "state": self.current_state.value,
            "topic": self._state_to_topic(self.current_state),
            "question": self.BASE_QUESTIONS[self.current_state],
            "action": "continue"
        }


    def _get_next_base_state(self) -> ConversationState:
        """Get next state in base question sequence"""

        # Find next uncompleted state
        for state in self.STATE_SEQUENCE:
            if state not in self.completed_states:
                return state

        # All states completed
        return ConversationState.COMPLETED


    @staticmethod
    def _is_explicit_no_more(user_message: str) -> bool:
        """Only treat clear, standalone no-more responses as declining a note."""
        normalized = re.sub(r"[.!?,]+", " ", user_message.lower()).strip()
        normalized = re.sub(r"\s+", " ", normalized)
        no_more_phrases = {
            "no", "nope", "nothing", "nothing else", "nothing more",
            "no thanks", "no thank you", "that's all", "that is all",
            "no nothing else", "no nothing more", "no that's all", "no that is all",
            "all good", "not really", "i'm good", "im good", "no more"
        }
        return normalized in no_more_phrases


    def _state_to_topic(self, state: ConversationState) -> str:
        """Convert state to topic string"""
        topic_map = {
            ConversationState.ASKING_MOOD: "MOOD",
            ConversationState.ASKING_SLEEP: "SLEEP",
            ConversationState.ASKING_MEALS: "MEALS",
            ConversationState.ASKING_SOCIAL_CONNECTION: "SOCIAL_CONNECTION",
            ConversationState.ASKING_ASSISTANCE: "ASSISTANCE",
            ConversationState.ASKING_ANYTHING_ELSE: "ANYTHING_ELSE"
        }
        return topic_map.get(state, "OTHER")


    def is_completed(self) -> bool:
        """Check if conversation is completed"""
        return self.current_state == ConversationState.COMPLETED


    def is_urgent(self) -> bool:
        """Check if in urgent workflow"""
        return self.current_state == ConversationState.URGENT_WORKFLOW


    def to_dict(self) -> Dict[str, Any]:
        """Export state for persistence"""
        return {
            "conversation_id": self.conversation_id,
            "senior_id": self.senior_id,
            "current_state": self.current_state.value,
            "current_topic": self.current_topic,
            "question_index": self.question_index,
            "completed_states": [s.value for s in self.completed_states],
            "follow_up_intent": self.follow_up_intent
        }


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationStateMachine':
        """Restore state machine from persistence"""
        machine = cls(data["conversation_id"], data["senior_id"])
        machine.current_state = ConversationState(data["current_state"])
        machine.current_topic = data.get("current_topic")
        machine.question_index = data.get("question_index", 0)
        machine.completed_states = {ConversationState(s) for s in data.get("completed_states", [])}
        machine.follow_up_intent = data.get("follow_up_intent")
        return machine
