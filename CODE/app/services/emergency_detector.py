"""
Emergency Detector Service
Rule-based urgent symptom detection - runs BEFORE intent classification
"""

from typing import Dict, Any, List
import re


class EmergencyDetector:
    """
    Detects potentially urgent medical symptoms using keyword/rule-based checks
    This runs FIRST, before LLM classification, to ensure safety
    """

    # Critical symptoms that require immediate attention
    URGENT_KEYWORDS = {
        "chest_pain": ["chest pain", "heart pain", "crushing chest", "chest hurts bad"],
        "breathing": ["can't breathe", "cannot breathe", "difficulty breathing", "gasping", "choking"],
        "stroke": ["stroke", "can't move arm", "face drooping", "slurred speech", "severe headache suddenly"],
        "bleeding": ["bleeding heavily", "blood everywhere", "won't stop bleeding"],
        "consciousness": ["passing out", "losing consciousness", "very dizzy", "fainted"],
        "severe_pain": ["severe pain", "worst pain ever", "unbearable pain", "pain 10 out of 10"]
    }

    # Emergency phrases patterns
    EMERGENCY_PATTERNS = [
        r"\b(can'?t|cannot)\s+(breathe|breath)",
        r"\b(chest|heart)\s+(pain|hurts?|ache)",
        r"\b(severe|extreme|terrible|unbearable)\s+(pain|hurt)",
        r"\b(bleed(ing)?)\s+(badly|heavily|a lot)",
        r"\b(passing|passed)\s+out\b",
        r"\bstroke\b",
        r"\bheart attack\b"
    ]


    def check(self, user_message: str) -> Dict[str, Any]:
        """
        Check if message contains urgent symptoms
        Returns: {is_urgent, category, keywords_found, recommended_action}
        """

        if not user_message or not user_message.strip():
            return {
                "is_urgent": False,
                "category": None,
                "keywords_found": [],
                "recommended_action": None
            }

        text = user_message.lower().strip()

        # Check keyword categories
        keywords_found = []
        category = None

        for cat, keywords in self.URGENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    keywords_found.append(keyword)
                    if not category:
                        category = cat

        # Check regex patterns
        for pattern in self.EMERGENCY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if not category:
                    category = "pattern_match"
                if len(keywords_found) == 0:
                    keywords_found.append(f"pattern: {pattern}")

        # Determine if urgent
        is_urgent = len(keywords_found) > 0

        if not is_urgent:
            return {
                "is_urgent": False,
                "category": None,
                "keywords_found": [],
                "recommended_action": None
            }

        # Generate recommended action based on category
        recommended_action = self._get_recommended_action(category)

        return {
            "is_urgent": True,
            "category": category,
            "keywords_found": keywords_found,
            "recommended_action": recommended_action
        }


    def _get_recommended_action(self, category: str) -> str:
        """Get appropriate safety response for each category"""

        actions = {
            "chest_pain": "Chest pain can be serious. Please seek emergency medical help immediately. Can you contact your caregiver or call emergency services?",

            "breathing": "Difficulty breathing is a medical emergency. Please seek help immediately. Can you call emergency services or contact your caregiver right away?",

            "stroke": "These symptoms could indicate a stroke, which requires immediate medical attention. Please call emergency services or have someone take you to the hospital right away.",

            "bleeding": "Heavy bleeding needs immediate attention. Please apply pressure to the wound and contact emergency services or your caregiver immediately.",

            "consciousness": "Passing out or severe dizziness can be serious. Please sit down safely and contact your caregiver or emergency services right away.",

            "severe_pain": "Severe pain needs medical attention. Please contact your caregiver or seek medical help if the pain is unbearable.",

            "pattern_match": "This sounds like it could be serious. Please contact your caregiver or seek medical help immediately."
        }

        return actions.get(category, "Please contact your caregiver or emergency services for immediate assistance.")


    def should_trigger_alert(self, detection_result: Dict[str, Any]) -> bool:
        """
        Determine if emergency alert should be triggered
        Returns True if urgent enough to alert family/caregiver immediately
        """

        if not detection_result.get("is_urgent"):
            return False

        # All urgent detections should trigger alerts
        # In production, you might add additional logic here
        return True


    def get_alert_severity(self, category: str) -> str:
        """Get severity level for alert"""

        critical_categories = ["chest_pain", "breathing", "stroke", "consciousness"]

        if category in critical_categories:
            return "critical"
        else:
            return "high"
