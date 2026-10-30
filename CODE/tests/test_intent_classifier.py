"""
Unit Tests for IntentClassifier
Tests intent classification accuracy and fallback mechanisms
"""

import unittest
from app.services.intent_classifier import IntentClassifier


class TestIntentClassifier(unittest.TestCase):
    """Test suite for intent classification"""

    @classmethod
    def setUpClass(cls):
        """Initialize classifier once for all tests"""
        cls.classifier = IntentClassifier()

    def test_01_positive_responses(self):
        """Test classification of positive responses"""
        positive_phrases = [
            "I'm feeling great",
            "Yes, I slept very well",
            "Everything is good",
            "I'm doing fine",
            "Feeling wonderful today"
        ]

        for phrase in positive_phrases:
            result = self.classifier.classify(phrase)
            self.assertEqual(result["intent"], "POSITIVE",
                           f"Failed for: {phrase}")

    def test_02_negative_responses(self):
        """Test classification of negative responses"""
        negative_phrases = [
            "I'm feeling bad",
            "Not good at all",
            "I'm having a terrible day",
            "Things are not well",
            "I feel awful"
        ]

        for phrase in negative_phrases:
            result = self.classifier.classify(phrase)
            self.assertEqual(result["intent"], "NEGATIVE",
                           f"Failed for: {phrase}")

    def test_03_lonely_detection(self):
        """Test classification of loneliness expressions"""
        lonely_phrases = [
            "I feel lonely",
            "Nobody visited me today",
            "I miss my family",
            "I haven't talked to anyone",
            "I'm feeling isolated"
        ]

        for phrase in lonely_phrases:
            result = self.classifier.classify(phrase)
            self.assertEqual(result["intent"], "LONELY",
                           f"Failed for: {phrase}")

    def test_04_physical_discomfort_detection(self):
        """Test classification of physical discomfort"""
        discomfort_phrases = [
            "My knee hurts",
            "I have a headache",
            "My back is sore",
            "I feel dizzy",
            "I'm feeling weak"
        ]

        for phrase in discomfort_phrases:
            result = self.classifier.classify(phrase)
            self.assertEqual(result["intent"], "PHYSICAL_DISCOMFORT",
                           f"Failed for: {phrase}")

    def test_05_assistance_needed_detection(self):
        """Test classification of assistance requests"""
        assistance_phrases = [
            "I need help with something",
            "Can you help me",
            "I need assistance",
            "Could someone help me",
            "I require some help"
        ]

        for phrase in assistance_phrases:
            result = self.classifier.classify(phrase)
            self.assertEqual(result["intent"], "ASSISTANCE_NEEDED",
                           f"Failed for: {phrase}")

    def test_06_skip_intent(self):
        """Test classification of skip/pass responses"""
        skip_phrases = [
            "skip",
            "pass",
            "next question",
            "I don't want to answer",
            "let's move on"
        ]

        for phrase in skip_phrases:
            result = self.classifier.classify(phrase)
            self.assertEqual(result["intent"], "SKIP",
                           f"Failed for: {phrase}")

    def test_07_unclear_responses(self):
        """Test classification of unclear responses"""
        unclear_phrases = [
            "hmm",
            "uh",
            "I don't know",
            "maybe",
            "sort of"
        ]

        for phrase in unclear_phrases:
            result = self.classifier.classify(phrase)
            self.assertIn(result["intent"], ["UNCLEAR", "OTHER"],
                         f"Failed for: {phrase}")

    def test_08_confidence_scores(self):
        """Test that confidence scores are reasonable"""
        result = self.classifier.classify("I'm feeling great today")

        self.assertIn("confidence", result)
        self.assertIsInstance(result["confidence"], (int, float))
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)

    def test_09_evidence_field(self):
        """Test that evidence field is populated"""
        result = self.classifier.classify("I feel lonely")

        self.assertIn("evidence", result)
        if result["evidence"]:
            self.assertIsInstance(result["evidence"], str)

    def test_10_needs_assistance_flag(self):
        """Test needs_assistance flag is set correctly"""
        result = self.classifier.classify("I need help")

        self.assertIn("needs_assistance", result)
        self.assertTrue(result["needs_assistance"])

    def test_11_urgent_flag(self):
        """Test urgent flag for serious concerns"""
        result = self.classifier.classify("I'm having trouble breathing")

        self.assertIn("urgent", result)
        # Should be flagged as potentially urgent
        self.assertIsInstance(result["urgent"], bool)

    def test_12_fallback_keyword_classification(self):
        """Test fallback keyword-based classification works"""
        # Simulate LLM failure by testing with classifier in offline mode
        result = self.classifier._fallback_classify("I feel lonely")

        self.assertEqual(result["intent"], "LONELY")
        self.assertEqual(result["confidence"], 0.6)

    def test_13_empty_input_handling(self):
        """Test handling of empty input"""
        result = self.classifier.classify("")

        self.assertEqual(result["intent"], "UNCLEAR")
        self.assertLess(result["confidence"], 0.5)

    def test_14_very_long_input(self):
        """Test handling of very long input"""
        long_text = "I'm feeling okay today. " * 100

        result = self.classifier.classify(long_text)

        self.assertIn(result["intent"], [
            "POSITIVE", "NEGATIVE", "LONELY", "PHYSICAL_DISCOMFORT",
            "ASSISTANCE_NEEDED", "URGENT_SYMPTOM", "UNCLEAR", "SKIP", "OTHER"
        ])

    def test_15_mixed_sentiment(self):
        """Test classification of mixed sentiment"""
        result = self.classifier.classify(
            "I slept well but my knee is hurting"
        )

        # Should detect the physical discomfort as primary concern
        self.assertIn(result["intent"], ["PHYSICAL_DISCOMFORT", "NEGATIVE"])

    def test_16_multiple_concerns_prioritization(self):
        """Test that urgent concerns are prioritized"""
        result = self.classifier.classify(
            "I feel lonely and also having chest pain"
        )

        # Physical symptom should be prioritized
        self.assertIn(result["intent"], ["PHYSICAL_DISCOMFORT", "URGENT_SYMPTOM"])

    def test_17_case_insensitivity(self):
        """Test classification is case-insensitive"""
        result1 = self.classifier.classify("I FEEL LONELY")
        result2 = self.classifier.classify("i feel lonely")
        result3 = self.classifier.classify("I Feel Lonely")

        self.assertEqual(result1["intent"], "LONELY")
        self.assertEqual(result2["intent"], "LONELY")
        self.assertEqual(result3["intent"], "LONELY")

    def test_18_special_characters_handling(self):
        """Test handling of special characters"""
        result = self.classifier.classify("I'm feeling good!!!")

        self.assertEqual(result["intent"], "POSITIVE")

    def test_19_numeric_responses(self):
        """Test handling of numeric responses"""
        result = self.classifier.classify("7 out of 10")

        # Should be classified as something reasonable
        self.assertIsNotNone(result["intent"])

    def test_20_yes_no_responses(self):
        """Test simple yes/no responses"""
        yes_result = self.classifier.classify("yes")
        no_result = self.classifier.classify("no")

        self.assertEqual(yes_result["intent"], "POSITIVE")
        self.assertIn(no_result["intent"], ["NEGATIVE", "SKIP"])


if __name__ == "__main__":
    unittest.main()
