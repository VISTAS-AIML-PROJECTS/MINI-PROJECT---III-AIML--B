"""
Conversation Controller
Orchestrates all services to handle conversation flow
"""

import uuid
import json
from typing import Dict, Any
from datetime import datetime

from .conversation_service import ConversationService
from .state_machine import ConversationStateMachine, ConversationState
from .intent_classifier import IntentClassifier
from .emergency_detector import EmergencyDetector
from .response_generator import ResponseGenerator
from .summary_generator import SummaryGenerator


class ConversationController:
    """
    Main controller that orchestrates:
    1. Emergency detection
    2. Intent classification
    3. State machine transitions
    4. Message persistence
    5. Response generation
    """

    def __init__(self, db_path: str = 'genvoice.db'):
        self.conv_service = ConversationService(db_path)
        self.intent_classifier = IntentClassifier()
        self.emergency_detector = EmergencyDetector()
        self.response_generator = ResponseGenerator()
        self.summary_generator = SummaryGenerator(db_path)


    def start_conversation(self, senior_id: str, senior_name: str) -> Dict[str, Any]:
        """
        Start a new conversation
        Returns: {conversation_id, greeting, state, status}
        """

        # Create conversation record
        conversation = self.conv_service.create_conversation(senior_id)
        conversation_id = conversation["conversation_id"]

        # Initialize state machine
        state_machine = ConversationStateMachine(conversation_id, senior_id)
        start_result = state_machine.start_conversation()

        # Serialize state machine for persistence
        state_dict = state_machine.to_dict()
        state_data_json = json.dumps(state_dict)
        completed_states_json = json.dumps([s.value for s in state_machine.completed_states])

        # Update conversation state
        self.conv_service.update_conversation_state(
            conversation_id,
            start_result["state"],
            start_result["topic"],
            None,  # status
            state_data_json,
            completed_states_json
        )

        # Generate greeting
        current_hour = datetime.now().hour
        if current_hour < 12:
            time_of_day = "morning"
        elif current_hour < 18:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"

        greeting = self.response_generator.generate_greeting(senior_name, time_of_day)

        # Save greeting as assistant message
        greeting_message_id = str(uuid.uuid4())
        self.conv_service.save_message(
            conversation_id,
            greeting_message_id,
            "assistant",
            greeting
        )

        return {
            "conversation_id": conversation_id,
            "greeting": greeting,
            "current_state": start_result["state"],
            "current_topic": start_result["topic"],
            "status": "active"
        }


    def process_message(self,
                        conversation_id: str,
                        message_id: str,
                        user_message: str,
                        senior_name: str) -> Dict[str, Any]:
        """
        Process user message through full pipeline
        Returns: {
            accepted, intent, assistant_message, next_state,
            conversation_status, sync_status, alert_created
        }
        """

        # 1. Get conversation state
        conversation = self.conv_service.get_conversation(conversation_id)
        if not conversation:
            return {
                "success": False,
                "error": "Conversation not found",
                "sync_status": "failed"
            }

        # 2. Check if conversation already completed
        if conversation["status"] == "completed":
            return {
                "success": False,
                "error": "Conversation already completed",
                "sync_status": "rejected"
            }

        # 3. EMERGENCY DETECTION FIRST (before everything else)
        emergency_result = self.emergency_detector.check(user_message)

        if emergency_result["is_urgent"]:
            # Save urgent message
            save_result = self.conv_service.save_message(
                conversation_id,
                message_id,
                "user",
                user_message,
                "URGENT_SYMPTOM",
                1.0
            )

            # Restore state machine and transition to URGENT_WORKFLOW
            if conversation.get("state_data"):
                try:
                    state_dict = json.loads(conversation["state_data"])
                    state_machine = ConversationStateMachine.from_dict(state_dict)
                except (json.JSONDecodeError, KeyError):
                    state_machine = ConversationStateMachine(conversation_id, conversation["senior_id"])
                    state_machine.current_state = ConversationState(conversation["current_state"])
            else:
                state_machine = ConversationStateMachine(conversation_id, conversation["senior_id"])
                state_machine.current_state = ConversationState(conversation["current_state"])

            # Transition to URGENT_WORKFLOW
            state_machine.transition("URGENT_SYMPTOM")

            # Serialize and save state
            state_dict = state_machine.to_dict()
            state_data_json = json.dumps(state_dict)
            completed_states_json = json.dumps([s.value for s in state_machine.completed_states])

            # Update state to URGENT_WORKFLOW
            self.conv_service.update_conversation_state(
                conversation_id,
                "URGENT_WORKFLOW",
                "URGENT",
                None,  # status
                state_data_json,
                completed_states_json
            )

            # Generate urgent response
            urgent_response = emergency_result["recommended_action"]

            # Save assistant response
            response_message_id = str(uuid.uuid4())
            self.conv_service.save_message(
                conversation_id,
                response_message_id,
                "assistant",
                urgent_response
            )

            return {
                "success": True,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "accepted": True,
                "intent": "URGENT_SYMPTOM",
                "confidence": 1.0,
                "assistant_message": urgent_response,
                "next_state": "URGENT_WORKFLOW",
                "conversation_status": "urgent",
                "sync_status": "saved",
                "alert_created": True,  # Controller should trigger alert
                "emergency_details": emergency_result
            }

        # 4. INTENT CLASSIFICATION
        intent_result = self.intent_classifier.classify(user_message)
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]

        # 5. SAVE USER MESSAGE (with idempotency)
        save_result = self.conv_service.save_message(
            conversation_id,
            message_id,
            "user",
            user_message,
            intent,
            confidence
        )

        if not save_result["success"]:
            return {
                "success": False,
                "error": save_result["message"],
                "sync_status": "failed"
            }

        # If duplicate, return success but indicate it was already processed
        if save_result["duplicate"]:
            # Get existing response (last assistant message)
            messages = self.conv_service.get_messages(conversation_id)
            last_assistant_msg = None
            for msg in reversed(messages):
                if msg["speaker"] == "assistant":
                    last_assistant_msg = msg
                    break

            return {
                "success": True,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "accepted": True,
                "intent": intent,
                "confidence": confidence,
                "assistant_message": last_assistant_msg["content"] if last_assistant_msg else "Message already processed",
                "next_state": conversation["current_state"],
                "conversation_status": conversation["status"],
                "sync_status": "duplicate",
                "alert_created": False
            }

        # 6. STATE MACHINE TRANSITION
        # Restore state machine from persisted state_data
        if conversation.get("state_data"):
            try:
                state_dict = json.loads(conversation["state_data"])
                state_machine = ConversationStateMachine.from_dict(state_dict)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[WARNING] Failed to restore state_data, creating fresh: {e}")
                state_machine = ConversationStateMachine(conversation_id, conversation["senior_id"])
                state_machine.current_state = ConversationState(conversation["current_state"])
        else:
            # No state_data yet - create fresh state machine
            state_machine = ConversationStateMachine(conversation_id, conversation["senior_id"])
            state_machine.current_state = ConversationState(conversation["current_state"])

        transition_result = state_machine.transition(intent, user_message=user_message)

        # 7. UPDATE CONVERSATION STATE
        new_state = transition_result["state"]
        new_topic = transition_result["topic"]
        new_status = "completed" if transition_result.get("action") == "generate_summary" else "active"

        # Serialize state machine for persistence
        state_dict = state_machine.to_dict()
        state_data_json = json.dumps(state_dict)
        completed_states_json = json.dumps([s.value for s in state_machine.completed_states])

        self.conv_service.update_conversation_state(
            conversation_id,
            new_state,
            new_topic,
            new_status,
            state_data_json,
            completed_states_json
        )

        # 8. GENERATE ASSISTANT RESPONSE
        summary_data = None
        if transition_result.get("action") == "generate_summary":
            # Generate summary before closing
            try:
                caregiver_note = transition_result.get("caregiver_note")
                summary_result = self.summary_generator.generate_summary(
                    conversation_id,
                    caregiver_note=caregiver_note
                )
                if summary_result.get("success"):
                    summary_data = summary_result["summary_data"]
                    wellness = summary_data.get("overall_wellness", "fair")
                else:
                    wellness = "fair"
            except Exception as e:
                print(f"[ERROR] Summary generation failed: {e}")
                wellness = "fair"

            assistant_message = self.response_generator.generate_closing(
                senior_name,
                wellness,
                note_shared=bool(transition_result.get("caregiver_note"))
            )
        elif transition_result.get("question"):
            assistant_message = self.response_generator.generate(
                user_message,
                intent,
                f"Asking about {new_topic}",
                transition_result["question"]
            )
        else:
            assistant_message = self.response_generator.generate(
                user_message,
                intent
            )

        # 9. SAVE ASSISTANT MESSAGE
        response_message_id = str(uuid.uuid4())
        self.conv_service.save_message(
            conversation_id,
            response_message_id,
            "assistant",
            assistant_message
        )

        # 10. RETURN RESULT
        result = {
            "success": True,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "accepted": True,
            "intent": intent,
            "confidence": confidence,
            "assistant_message": assistant_message,
            "next_state": new_state,
            "next_topic": new_topic,
            "conversation_status": new_status,
            "sync_status": "saved",
            "alert_created": False
        }

        if summary_data:
            result["summary"] = summary_data

        return result


    def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """Get current conversation status"""

        conversation = self.conv_service.get_conversation(conversation_id)
        if not conversation:
            return {
                "success": False,
                "error": "Conversation not found"
            }

        messages = self.conv_service.get_messages(conversation_id)

        return {
            "success": True,
            "conversation": conversation,
            "message_count": len(messages),
            "messages": messages
        }
