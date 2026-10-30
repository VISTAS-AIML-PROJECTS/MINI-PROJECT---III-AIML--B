"""
API Endpoint Tests
Tests REST API endpoints for Blueprint architecture
"""

import unittest
import uuid
import requests
import time


BASE_URL = "http://localhost:8000"


class TestAPIEndpoints(unittest.TestCase):
    """Test suite for API endpoints"""

    @classmethod
    def setUpClass(cls):
        """Check if server is running"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=3)
            if response.status_code != 200:
                raise Exception("Server not healthy")
        except Exception as e:
            raise unittest.SkipTest(f"Server not running: {e}")

    def setUp(self):
        """Get senior ID for tests"""
        response = requests.get(f"{BASE_URL}/api/v1/seniors")
        seniors = response.json()['data']
        if not seniors:
            raise unittest.SkipTest("No seniors in database")
        self.senior_id = seniors[0]['id']
        self.senior_name = seniors[0]['name']

    def test_01_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("database", data)

    def test_02_get_seniors(self):
        """Test getting list of seniors"""
        response = requests.get(f"{BASE_URL}/api/v1/seniors")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIsInstance(data["data"], list)

    def test_03_start_conversation(self):
        """Test starting a new conversation"""
        response = requests.post(
            f"{BASE_URL}/api/v1/conversations",
            json={"senior_id": self.senior_id}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("conversation_id", data["data"])
        self.assertIn("greeting", data["data"])
        self.assertEqual(data["data"]["current_state"], "ASKING_MOOD")
        self.assertEqual(data["data"]["status"], "active")

    def test_04_submit_message(self):
        """Test submitting a message in conversation"""
        # Start conversation
        start_response = requests.post(
            f"{BASE_URL}/api/v1/conversations",
            json={"senior_id": self.senior_id}
        )
        conversation_id = start_response.json()["data"]["conversation_id"]

        # Submit message
        message_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
            json={
                "message_id": message_id,
                "text": "I'm feeling great today"
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["intent"], "POSITIVE")
        self.assertIn("assistant_message", data["data"])
        self.assertEqual(data["data"]["sync_status"], "saved")

    def test_05_message_idempotency(self):
        """Test message idempotency with duplicate message_id"""
        # Start conversation
        start_response = requests.post(
            f"{BASE_URL}/api/v1/conversations",
            json={"senior_id": self.senior_id}
        )
        conversation_id = start_response.json()["data"]["conversation_id"]

        # Submit message
        message_id = str(uuid.uuid4())
        response1 = requests.post(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
            json={
                "message_id": message_id,
                "text": "I'm feeling good"
            }
        )

        # Submit same message_id again
        response2 = requests.post(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
            json={
                "message_id": message_id,
                "text": "I'm feeling good"
            }
        )

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        data2 = response2.json()
        self.assertEqual(data2["data"]["sync_status"], "duplicate")

    def test_06_get_conversation_details(self):
        """Test getting conversation details"""
        # Start and populate conversation
        start_response = requests.post(
            f"{BASE_URL}/api/v1/conversations",
            json={"senior_id": self.senior_id}
        )
        conversation_id = start_response.json()["data"]["conversation_id"]

        # Submit a message
        requests.post(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
            json={
                "message_id": str(uuid.uuid4()),
                "text": "I'm feeling great"
            }
        )

        # Get conversation details
        response = requests.get(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("conversation", data["data"])
        self.assertIn("messages", data["data"])
        self.assertGreater(data["data"]["message_count"], 0)

    def test_07_get_senior_conversations(self):
        """Test getting conversation history for a senior"""
        response = requests.get(
            f"{BASE_URL}/api/v1/seniors/{self.senior_id}/conversations"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("conversations", data["data"])

    def test_08_emergency_detection_via_api(self):
        """Test emergency detection through API"""
        # Start conversation
        start_response = requests.post(
            f"{BASE_URL}/api/v1/conversations",
            json={"senior_id": self.senior_id}
        )
        conversation_id = start_response.json()["data"]["conversation_id"]

        # Submit urgent message
        response = requests.post(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
            json={
                "message_id": str(uuid.uuid4()),
                "text": "I have severe chest pain"
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["intent"], "URGENT_SYMPTOM")
        self.assertEqual(data["data"]["conversation_status"], "urgent")
        self.assertTrue(data["data"]["alert_created"])

    def test_09_complete_conversation_flow(self):
        """Test complete conversation through API"""
        # Start
        start_response = requests.post(
            f"{BASE_URL}/api/v1/conversations",
            json={"senior_id": self.senior_id}
        )
        conversation_id = start_response.json()["data"]["conversation_id"]

        # Submit 5 positive responses
        responses = [
            "I'm feeling great",
            "Yes, I slept well",
            "I had a good breakfast",
            "Yes, I spoke with family",
            "No, I don't need help"
        ]

        last_response = None
        for text in responses:
            response = requests.post(
                f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
                json={
                    "message_id": str(uuid.uuid4()),
                    "text": text
                }
            )
            last_response = response.json()

        # Should be completed
        self.assertEqual(last_response["data"]["conversation_status"], "completed")

    def test_10_invalid_conversation_id(self):
        """Test handling of invalid conversation ID"""
        response = requests.post(
            f"{BASE_URL}/api/v1/conversations/invalid-id/messages",
            json={
                "message_id": str(uuid.uuid4()),
                "text": "Hello"
            }
        )

        self.assertEqual(response.status_code, 500)

    def test_11_missing_required_fields(self):
        """Test validation of required fields"""
        # Start conversation
        start_response = requests.post(
            f"{BASE_URL}/api/v1/conversations",
            json={"senior_id": self.senior_id}
        )
        conversation_id = start_response.json()["data"]["conversation_id"]

        # Submit message without text
        response = requests.post(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
            json={
                "message_id": str(uuid.uuid4())
                # Missing "text" field
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_12_dashboard_endpoint(self):
        """Test dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/v1/seniors/{self.senior_id}/dashboard"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("senior", data["data"])
        self.assertIn("latest_conversation", data["data"])

    def test_13_intent_classification_accuracy(self):
        """Test intent classification through API"""
        # Start conversation
        start_response = requests.post(
            f"{BASE_URL}/api/v1/conversations",
            json={"senior_id": self.senior_id}
        )
        conversation_id = start_response.json()["data"]["conversation_id"]

        # Test different intents
        test_cases = [
            ("I'm feeling great", "POSITIVE"),
            ("I feel lonely", "LONELY"),
            ("My knee hurts", "PHYSICAL_DISCOMFORT"),
            ("I need help", "ASSISTANCE_NEEDED")
        ]

        for text, expected_intent in test_cases:
            # Create new conversation for each test
            start_resp = requests.post(
                f"{BASE_URL}/api/v1/conversations",
                json={"senior_id": self.senior_id}
            )
            conv_id = start_resp.json()["data"]["conversation_id"]

            response = requests.post(
                f"{BASE_URL}/api/v1/conversations/{conv_id}/messages",
                json={
                    "message_id": str(uuid.uuid4()),
                    "text": text
                }
            )

            data = response.json()
            self.assertEqual(
                data["data"]["intent"],
                expected_intent,
                f"Failed for: {text}"
            )

    def test_14_concurrent_conversations(self):
        """Test handling multiple concurrent conversations"""
        # Start 3 conversations
        conversation_ids = []
        for _ in range(3):
            response = requests.post(
                f"{BASE_URL}/api/v1/conversations",
                json={"senior_id": self.senior_id}
            )
            conversation_ids.append(response.json()["data"]["conversation_id"])

        # Submit messages to each
        for conv_id in conversation_ids:
            response = requests.post(
                f"{BASE_URL}/api/v1/conversations/{conv_id}/messages",
                json={
                    "message_id": str(uuid.uuid4()),
                    "text": "Test message"
                }
            )
            self.assertEqual(response.status_code, 200)

    def test_15_response_time(self):
        """Test API response times are reasonable"""
        # Start conversation
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v1/conversations",
            json={"senior_id": self.senior_id}
        )
        elapsed = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 5.0, "Response took too long")


if __name__ == "__main__":
    unittest.main()
