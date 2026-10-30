"""
Unit Tests for ConversationStateMachine
Tests state transitions, question generation, and flow logic
"""

import unittest
from app.services.state_machine import ConversationStateMachine, ConversationState


class TestConversationStateMachine(unittest.TestCase):
    """Test suite for state machine logic"""

    def setUp(self):
        """Create a fresh state machine for each test"""
        self.machine = ConversationStateMachine("test-conv-id", "test-senior-id")

    def test_01_initialization(self):
        """Test state machine initializes to IDLE"""
        self.assertEqual(self.machine.current_state, ConversationState.IDLE)
        self.assertIsNone(self.machine.current_topic)
        self.assertEqual(self.machine.question_index, 0)
        self.assertEqual(len(self.machine.completed_states), 0)

    def test_02_start_conversation(self):
        """Test starting a conversation moves to ASKING_MOOD"""
        result = self.machine.start_conversation()

        self.assertEqual(self.machine.current_state, ConversationState.ASKING_MOOD)
        self.assertEqual(result["state"], "ASKING_MOOD")
        self.assertEqual(result["topic"], "MOOD")
        self.assertIn("How are you feeling", result["question"])

    def test_03_positive_flow_complete_sequence(self):
        """Test complete conversation with all POSITIVE responses"""
        self.machine.start_conversation()

        # Sequence: MOOD -> SLEEP -> MEALS -> SOCIAL -> ASSISTANCE -> COMPLETED
        expected_sequence = [
            ("POSITIVE", "ASKING_SLEEP"),
            ("POSITIVE", "ASKING_MEALS"),
            ("POSITIVE", "ASKING_SOCIAL_CONNECTION"),
            ("POSITIVE", "ASKING_ASSISTANCE"),
            ("POSITIVE", "COMPLETED")
        ]

        for intent, expected_state in expected_sequence:
            result = self.machine.transition(intent)
            self.assertEqual(result["state"], expected_state)

        self.assertTrue(self.machine.is_completed())

    def test_04_lonely_intent_triggers_follow_up(self):
        """Test LONELY intent triggers follow-up question"""
        self.machine.start_conversation()

        result = self.machine.transition("LONELY")

        self.assertEqual(result["state"], "FOLLOW_UP")
        self.assertEqual(result["topic"], "LONELY")
        self.assertIn("contact someone", result["question"])
        self.assertEqual(result["action"], "follow_up")

    def test_05_follow_up_returns_to_normal_flow(self):
        """Test follow-up returns to next base question"""
        self.machine.start_conversation()

        # Trigger follow-up
        self.machine.transition("LONELY")

        # Answer follow-up, should go to ASKING_SLEEP
        result = self.machine.transition("POSITIVE")
        self.assertEqual(result["state"], "ASKING_SLEEP")

    def test_06_physical_discomfort_flow(self):
        """Test PHYSICAL_DISCOMFORT triggers follow-up"""
        self.machine.start_conversation()

        result = self.machine.transition("PHYSICAL_DISCOMFORT")

        self.assertEqual(result["state"], "FOLLOW_UP")
        self.assertEqual(result["topic"], "PHYSICAL_DISCOMFORT")
        self.assertIn("caregiver", result["question"])

    def test_07_urgent_symptom_interrupts(self):
        """Test URGENT_SYMPTOM always interrupts current flow"""
        self.machine.start_conversation()
        self.machine.transition("POSITIVE")  # Move to ASKING_SLEEP

        # Urgent symptom at any point
        result = self.machine.transition("URGENT_SYMPTOM")

        self.assertEqual(result["state"], "URGENT_WORKFLOW")
        self.assertEqual(result["action"], "trigger_urgent_workflow")
        self.assertTrue(self.machine.is_urgent())

    def test_08_urgent_stays_in_urgent(self):
        """Test URGENT_WORKFLOW state stays urgent"""
        self.machine.start_conversation()
        self.machine.transition("URGENT_SYMPTOM")

        # Any response while in urgent stays urgent
        result = self.machine.transition("POSITIVE")
        self.assertEqual(result["state"], "URGENT_WORKFLOW")

    def test_09_skip_intent_progresses(self):
        """Test SKIP intent moves to next question"""
        self.machine.start_conversation()

        result = self.machine.transition("SKIP")
        self.assertEqual(result["state"], "ASKING_SLEEP")

    def test_10_unclear_intent_progresses(self):
        """Test UNCLEAR intent still progresses conversation"""
        self.machine.start_conversation()

        result = self.machine.transition("UNCLEAR")
        self.assertEqual(result["state"], "ASKING_SLEEP")

    def test_11_completed_states_tracking(self):
        """Test completed states are tracked correctly"""
        self.machine.start_conversation()

        self.machine.transition("POSITIVE")  # Complete ASKING_MOOD
        self.assertIn(ConversationState.ASKING_MOOD, self.machine.completed_states)

        self.machine.transition("POSITIVE")  # Complete ASKING_SLEEP
        self.assertIn(ConversationState.ASKING_SLEEP, self.machine.completed_states)

    def test_12_state_persistence(self):
        """Test state can be serialized and restored"""
        self.machine.start_conversation()
        self.machine.transition("LONELY")

        # Export state
        state_dict = self.machine.to_dict()

        # Create new machine from state
        restored = ConversationStateMachine.from_dict(state_dict)

        self.assertEqual(restored.current_state, self.machine.current_state)
        self.assertEqual(restored.current_topic, self.machine.current_topic)
        self.assertEqual(restored.completed_states, self.machine.completed_states)

    def test_13_negative_intent_follow_up(self):
        """Test NEGATIVE intent triggers empathetic follow-up"""
        self.machine.start_conversation()

        result = self.machine.transition("NEGATIVE")

        self.assertEqual(result["state"], "FOLLOW_UP")
        self.assertIn("troubling", result["question"])

    def test_14_assistance_needed_follow_up(self):
        """Test ASSISTANCE_NEEDED triggers specific follow-up"""
        self.machine.start_conversation()

        result = self.machine.transition("ASSISTANCE_NEEDED")

        self.assertEqual(result["state"], "FOLLOW_UP")
        self.assertIn("help", result["question"])

    def test_15_multiple_follow_ups_in_sequence(self):
        """Test multiple follow-ups are handled correctly"""
        self.machine.start_conversation()

        # First follow-up
        self.machine.transition("LONELY")
        self.machine.transition("POSITIVE")  # Complete follow-up

        # Should be at ASKING_SLEEP now
        self.assertEqual(self.machine.current_state, ConversationState.ASKING_SLEEP)

        # Second follow-up
        result = self.machine.transition("PHYSICAL_DISCOMFORT")
        self.assertEqual(result["state"], "FOLLOW_UP")

    def test_16_all_questions_asked_before_completion(self):
        """Test all 5 base questions are asked before completion"""
        self.machine.start_conversation()

        # Answer all with POSITIVE
        for _ in range(5):
            result = self.machine.transition("POSITIVE")

        # Should be completed after 5 positive responses
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(len(self.machine.completed_states), 5)

    def test_17_state_recovery_mid_conversation(self):
        """Test state machine can recover from serialized state mid-conversation"""
        self.machine.start_conversation()
        self.machine.transition("POSITIVE")
        self.machine.transition("LONELY")

        # Simulate server restart
        state_dict = self.machine.to_dict()
        new_machine = ConversationStateMachine.from_dict(state_dict)

        # Should be able to continue
        result = new_machine.transition("POSITIVE")
        self.assertEqual(result["state"], "ASKING_SLEEP")


if __name__ == "__main__":
    unittest.main()
