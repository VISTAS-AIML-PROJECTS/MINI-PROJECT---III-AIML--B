"""
Unit Tests for EmergencyDetector
Tests emergency symptom detection and recommended actions
"""

import unittest
from app.services.emergency_detector import EmergencyDetector


class TestEmergencyDetector(unittest.TestCase):
    """Test suite for emergency detection"""

    @classmethod
    def setUpClass(cls):
        """Initialize detector once for all tests"""
        cls.detector = EmergencyDetector()

    def test_01_no_emergency_normal_message(self):
        """Test normal messages don't trigger emergency"""
        normal_messages = [
            "I'm feeling good today",
            "I had a nice breakfast",
            "The weather is lovely",
            "I spoke with my daughter"
        ]

        for msg in normal_messages:
            result = self.detector.check(msg)
            self.assertFalse(result["is_urgent"], f"False positive for: {msg}")

    def test_02_chest_pain_detection(self):
        """Test chest pain detection"""
        chest_pain_phrases = [
            "I have chest pain",
            "My chest hurts",
            "There's pain in my chest",
            "I'm experiencing chest discomfort",
            "Sharp pain in my chest"
        ]

        for phrase in chest_pain_phrases:
            result = self.detector.check(phrase)
            self.assertTrue(result["is_urgent"], f"Failed for: {phrase}")
            self.assertEqual(result["symptom_category"], "chest_pain")
            self.assertIn("emergency medical help", result["recommended_action"])

    def test_03_breathing_difficulty_detection(self):
        """Test breathing difficulty detection"""
        breathing_phrases = [
            "I can't breathe",
            "Having trouble breathing",
            "I'm short of breath",
            "Difficulty breathing",
            "Feeling breathless"
        ]

        for phrase in breathing_phrases:
            result = self.detector.check(phrase)
            self.assertTrue(result["is_urgent"], f"Failed for: {phrase}")
            self.assertEqual(result["symptom_category"], "breathing")
            self.assertIn("emergency", result["recommended_action"].lower())

    def test_04_stroke_symptoms_detection(self):
        """Test stroke symptom detection"""
        stroke_phrases = [
            "I can't move my arm",
            "My face feels numb",
            "I'm having trouble speaking",
            "Can't feel my left side",
            "Vision is blurry in one eye"
        ]

        for phrase in stroke_phrases:
            result = self.detector.check(phrase)
            self.assertTrue(result["is_urgent"], f"Failed for: {phrase}")
            self.assertIn(result["symptom_category"], ["stroke", "consciousness"])

    def test_05_severe_bleeding_detection(self):
        """Test severe bleeding detection"""
        bleeding_phrases = [
            "I'm bleeding heavily",
            "Can't stop the bleeding",
            "There's a lot of blood",
            "Severe bleeding from my arm"
        ]

        for phrase in bleeding_phrases:
            result = self.detector.check(phrase)
            self.assertTrue(result["is_urgent"], f"Failed for: {phrase}")
            self.assertEqual(result["symptom_category"], "bleeding")

    def test_06_consciousness_issues_detection(self):
        """Test consciousness-related issues"""
        consciousness_phrases = [
            "I feel like I'm going to faint",
            "I'm very dizzy",
            "Feeling lightheaded",
            "I think I might pass out",
            "Everything is spinning"
        ]

        for phrase in consciousness_phrases:
            result = self.detector.check(phrase)
            self.assertTrue(result["is_urgent"], f"Failed for: {phrase}")
            self.assertIn(result["symptom_category"], ["consciousness", "stroke"])

    def test_07_severe_pain_detection(self):
        """Test severe pain detection"""
        severe_pain_phrases = [
            "Unbearable pain in my stomach",
            "The worst headache of my life",
            "Excruciating pain",
            "Severe abdominal pain",
            "Intense pain that won't stop"
        ]

        for phrase in severe_pain_phrases:
            result = self.detector.check(phrase)
            self.assertTrue(result["is_urgent"], f"Failed for: {phrase}")
            self.assertEqual(result["symptom_category"], "severe_pain")

    def test_08_fall_detection(self):
        """Test fall detection"""
        fall_phrases = [
            "I fell down",
            "I had a fall",
            "I fell and hurt myself",
            "Fell in the bathroom",
            "I tripped and fell"
        ]

        for phrase in fall_phrases:
            result = self.detector.check(phrase)
            # Falls should be flagged as urgent
            self.assertTrue(result["is_urgent"], f"Failed for: {phrase}")

    def test_09_matched_keywords_returned(self):
        """Test that matched keywords are returned"""
        result = self.detector.check("I have severe chest pain")

        self.assertIn("matched_keywords", result)
        self.assertIsInstance(result["matched_keywords"], list)
        self.assertTrue(len(result["matched_keywords"]) > 0)

    def test_10_case_insensitive_detection(self):
        """Test detection is case-insensitive"""
        result1 = self.detector.check("CHEST PAIN")
        result2 = self.detector.check("chest pain")
        result3 = self.detector.check("Chest Pain")

        self.assertTrue(result1["is_urgent"])
        self.assertTrue(result2["is_urgent"])
        self.assertTrue(result3["is_urgent"])

    def test_11_multiple_symptoms(self):
        """Test handling of multiple symptoms"""
        result = self.detector.check(
            "I have chest pain and I'm having trouble breathing"
        )

        self.assertTrue(result["is_urgent"])
        # Should detect at least one category
        self.assertIsNotNone(result["symptom_category"])

    def test_12_mild_symptoms_not_urgent(self):
        """Test mild symptoms don't trigger emergency"""
        mild_phrases = [
            "I have a slight headache",
            "My knee is a bit sore",
            "Feeling a little tired",
            "Minor discomfort in my back"
        ]

        for phrase in mild_phrases:
            result = self.detector.check(phrase)
            # Mild symptoms should not be urgent
            self.assertFalse(result["is_urgent"], f"False positive for: {phrase}")

    def test_13_empty_message_handling(self):
        """Test handling of empty messages"""
        result = self.detector.check("")

        self.assertFalse(result["is_urgent"])
        self.assertIsNone(result["symptom_category"])

    def test_14_special_characters_handling(self):
        """Test handling of special characters"""
        result = self.detector.check("I have chest pain!!!")

        self.assertTrue(result["is_urgent"])

    def test_15_recommended_action_format(self):
        """Test recommended action is properly formatted"""
        result = self.detector.check("I have chest pain")

        self.assertIn("recommended_action", result)
        self.assertIsInstance(result["recommended_action"], str)
        self.assertTrue(len(result["recommended_action"]) > 0)

    def test_16_heart_attack_keywords(self):
        """Test heart attack related keywords"""
        heart_phrases = [
            "I think I'm having a heart attack",
            "Heart racing very fast",
            "Pressure in my chest",
            "Crushing chest pain"
        ]

        for phrase in heart_phrases:
            result = self.detector.check(phrase)
            self.assertTrue(result["is_urgent"], f"Failed for: {phrase}")

    def test_17_confusion_detection(self):
        """Test confusion/disorientation detection"""
        confusion_phrases = [
            "I don't know where I am",
            "I'm very confused",
            "Can't remember what day it is",
            "Feel disoriented"
        ]

        for phrase in confusion_phrases:
            result = self.detector.check(phrase)
            # Confusion should be flagged
            self.assertTrue(result["is_urgent"], f"Failed for: {phrase}")

    def test_18_priority_ordering(self):
        """Test that chest pain is highest priority"""
        result = self.detector.check(
            "I have a headache and chest pain"
        )

        # Chest pain should be detected as primary
        self.assertEqual(result["symptom_category"], "chest_pain")

    def test_19_regex_pattern_matching(self):
        """Test regex patterns work correctly"""
        # Test phrase variations
        result1 = self.detector.check("can't breathe well")
        result2 = self.detector.check("cannot breathe properly")

        self.assertTrue(result1["is_urgent"])
        self.assertTrue(result2["is_urgent"])

    def test_20_ambulance_recommendation(self):
        """Test that critical symptoms recommend calling ambulance"""
        critical_phrases = [
            "I have severe chest pain",
            "I can't breathe",
            "I think I'm having a stroke"
        ]

        for phrase in critical_phrases:
            result = self.detector.check(phrase)
            action = result["recommended_action"].lower()
            self.assertTrue(
                "emergency" in action or "911" in action or "ambulance" in action,
                f"No ambulance recommendation for: {phrase}"
            )


if __name__ == "__main__":
    unittest.main()
