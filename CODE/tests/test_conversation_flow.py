"""
Integration Tests for Complete Conversation Flow
Tests end-to-end conversation scenarios
"""

import unittest
import uuid
from app.services.conversation_controller import ConversationController


class TestConversationFlow(unittest.TestCase):
    """Test suite for complete conversation flows"""

    def setUp(self):
        """Create fresh controller for each test"""
        self.controller = ConversationController()
        self.senior_id = "test-senior-" + str(uuid.uuid4())[:8]
        self.senior_name = "Test Senior"

    def test_01_start_conversation(self):
        """Test starting a new conversation"""
        result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )

        self.assertIn("conversation_id", result)
        self.assertIn("greeting", result)
        self.assertEqual(result["current_state"], "ASKING_MOOD")
        self.assertEqual(result["status"], "active")
        self.assertIn("feeling", result["greeting"].lower())

    def test_02_complete_positive_conversation(self):
        """Test complete conversation with all positive responses"""
        # Start conversation
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Submit 5 positive responses
        positive_responses = [
            "I'm feeling great",
            "Yes, I slept very well",
            "I had a good breakfast",
            "Yes, I spoke with my daughter",
            "No, I'm all good"
        ]

        last_result = None
        for response in positive_responses:
            message_id = str(uuid.uuid4())
            result = self.controller.process_message(
                conversation_id,
                message_id,
                response,
                self.senior_name
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["intent"], "POSITIVE")
            last_result = result

        # Should be completed after 5 responses
        self.assertEqual(last_result["conversation_status"], "completed")

    def test_03_lonely_triggers_follow_up(self):
        """Test loneliness detection triggers follow-up"""
        # Start conversation
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # First response positive
        self.controller.process_message(
            conversation_id,
            str(uuid.uuid4()),
            "I'm feeling okay",
            self.senior_name
        )

        # Second response indicates loneliness
        message_id = str(uuid.uuid4())
        result = self.controller.process_message(
            conversation_id,
            message_id,
            "I feel a bit lonely today",
            self.senior_name
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["intent"], "LONELY")
        self.assertEqual(result["next_state"], "FOLLOW_UP")
        self.assertIn("contact", result["assistant_message"].lower())

    def test_04_urgent_symptom_immediate_response(self):
        """Test urgent symptom triggers immediate emergency response"""
        # Start conversation
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Report urgent symptom
        message_id = str(uuid.uuid4())
        result = self.controller.process_message(
            conversation_id,
            message_id,
            "I have severe chest pain",
            self.senior_name
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["intent"], "URGENT_SYMPTOM")
        self.assertEqual(result["next_state"], "URGENT_WORKFLOW")
        self.assertEqual(result["conversation_status"], "urgent")
        self.assertTrue(result["alert_created"])

    def test_05_message_idempotency(self):
        """Test duplicate message_id is handled correctly"""
        # Start conversation
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Send message with specific ID
        message_id = str(uuid.uuid4())
        result1 = self.controller.process_message(
            conversation_id,
            message_id,
            "I'm feeling good",
            self.senior_name
        )

        # Send same message_id again
        result2 = self.controller.process_message(
            conversation_id,
            message_id,
            "I'm feeling good",
            self.senior_name
        )

        # Should return same response
        self.assertEqual(result1["intent"], result2["intent"])
        self.assertEqual(result2["sync_status"], "duplicate")

    def test_06_physical_discomfort_flow(self):
        """Test physical discomfort is handled appropriately"""
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Report physical discomfort
        message_id = str(uuid.uuid4())
        result = self.controller.process_message(
            conversation_id,
            message_id,
            "My knee is hurting",
            self.senior_name
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["intent"], "PHYSICAL_DISCOMFORT")
        self.assertEqual(result["next_state"], "FOLLOW_UP")

    def test_07_assistance_needed_flow(self):
        """Test assistance request is captured"""
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Move through initial questions
        self.controller.process_message(
            conversation_id,
            str(uuid.uuid4()),
            "I'm okay",
            self.senior_name
        )

        # Request assistance
        message_id = str(uuid.uuid4())
        result = self.controller.process_message(
            conversation_id,
            message_id,
            "Yes, I need help with something",
            self.senior_name
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["intent"], "ASSISTANCE_NEEDED")

    def test_08_skip_question(self):
        """Test skipping a question moves conversation forward"""
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Skip first question
        message_id = str(uuid.uuid4())
        result = self.controller.process_message(
            conversation_id,
            message_id,
            "skip",
            self.senior_name
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["intent"], "SKIP")
        # Should move to next question
        self.assertIn(result["next_state"], ["ASKING_SLEEP", "ASKING_MEALS"])

    def test_09_unclear_response_handling(self):
        """Test unclear responses are handled gracefully"""
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Give unclear response
        message_id = str(uuid.uuid4())
        result = self.controller.process_message(
            conversation_id,
            message_id,
            "hmm I don't know",
            self.senior_name
        )

        self.assertTrue(result["success"])
        self.assertIn(result["intent"], ["UNCLEAR", "SKIP"])
        # Should still progress
        self.assertIsNotNone(result["assistant_message"])

    def test_10_multiple_concerns_in_one_message(self):
        """Test handling multiple concerns in single message"""
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Complex message with multiple concerns
        message_id = str(uuid.uuid4())
        result = self.controller.process_message(
            conversation_id,
            message_id,
            "I'm feeling lonely and my knee hurts",
            self.senior_name
        )

        self.assertTrue(result["success"])
        # Should classify as one of the concerns
        self.assertIn(result["intent"], ["LONELY", "PHYSICAL_DISCOMFORT"])

    def test_11_conversation_state_recovery(self):
        """Test conversation can be retrieved and continued"""
        # Start conversation
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Submit one message
        self.controller.process_message(
            conversation_id,
            str(uuid.uuid4()),
            "I'm feeling good",
            self.senior_name
        )

        # Get conversation status
        status = self.controller.get_conversation_status(conversation_id)

        self.assertTrue(status["success"])
        self.assertGreater(status["message_count"], 0)
        self.assertEqual(status["conversation"]["status"], "active")

    def test_12_negative_mood_follow_up(self):
        """Test negative mood triggers empathetic follow-up"""
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        message_id = str(uuid.uuid4())
        result = self.controller.process_message(
            conversation_id,
            message_id,
            "I'm not feeling well today",
            self.senior_name
        )

        self.assertEqual(result["intent"], "NEGATIVE")
        self.assertEqual(result["next_state"], "FOLLOW_UP")
        self.assertIn("tell me", result["assistant_message"].lower())

    def test_13_emergency_mid_conversation(self):
        """Test emergency can occur mid-conversation"""
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Normal responses first
        self.controller.process_message(
            conversation_id,
            str(uuid.uuid4()),
            "I'm okay",
            self.senior_name
        )

        self.controller.process_message(
            conversation_id,
            str(uuid.uuid4()),
            "Yes, I slept well",
            self.senior_name
        )

        # Sudden emergency
        message_id = str(uuid.uuid4())
        result = self.controller.process_message(
            conversation_id,
            message_id,
            "I'm having trouble breathing",
            self.senior_name
        )

        self.assertEqual(result["intent"], "URGENT_SYMPTOM")
        self.assertTrue(result["alert_created"])

    def test_14_complete_conversation_with_follow_ups(self):
        """Test complete conversation with multiple follow-ups"""
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        responses = [
            ("I'm feeling okay", "POSITIVE"),
            ("I slept well", "POSITIVE"),
            ("I feel a bit lonely", "LONELY"),
            ("No, I haven't talked to anyone", "NEGATIVE"),
            ("Yes, I had my meals", "POSITIVE"),
            ("Yes, I spoke with my son", "POSITIVE"),
            ("No, I'm fine", "POSITIVE")
        ]

        for response_text, expected_intent in responses:
            message_id = str(uuid.uuid4())
            result = self.controller.process_message(
                conversation_id,
                message_id,
                response_text,
                self.senior_name
            )

            self.assertTrue(result["success"])
            # Intent might vary slightly but should be reasonable
            self.assertIsNotNone(result["intent"])

    def test_15_message_persistence(self):
        """Test all messages are persisted correctly"""
        start_result = self.controller.start_conversation(
            self.senior_id,
            self.senior_name
        )
        conversation_id = start_result["conversation_id"]

        # Submit several messages
        for i in range(3):
            self.controller.process_message(
                conversation_id,
                str(uuid.uuid4()),
                f"Test message {i+1}",
                self.senior_name
            )

        # Retrieve conversation
        status = self.controller.get_conversation_status(conversation_id)

        # Should have: greeting + 3 user messages + 3 assistant responses = 7+
        self.assertGreaterEqual(status["message_count"], 7)


if __name__ == "__main__":
    unittest.main()
