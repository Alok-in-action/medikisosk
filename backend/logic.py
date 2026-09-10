from sqlalchemy.orm import Session
from models import Session as DBSession, Patient, Answer, Question
from typing import Dict, Any

RED_FLAG_RULES = {
    20: {
        "trigger_values": ["yes", "haan", "y"],
        "severity": "urgent",
        "reason": "Pain waking patient at night"
    },
    43: {
        "trigger_values": ["yes", "haan", "y"],
        "severity": "emergency",
        "reason": "Blood in sputum / haemoptysis"
    },
    44: {
        "trigger_values": ["at rest"],
        "severity": "emergency",
        "reason": "Breathlessness at rest"
    },
    47: {
        "trigger_values": ["yes", "haan", "y"],
        "severity": "urgent",
        "reason": "Unintentional weight loss with respiratory complaint"
    },
    55: {
        "trigger_values": ["yes", "haan", "y"],
        "severity": "urgent",
        "reason": "Blood or mucus in stool"
    },
    59: {
        "trigger_values": ["yes", "haan", "y"],
        "severity": "urgent",
        "reason": "Jaundice symptoms"
    },
    63: {
        "trigger_values": ["yes", "haan", "y"],
        "severity": "urgent",
        "reason": "Blood in urine"
    },
    88: {
        "trigger_values": ["yes", "haan", "y"],
        "severity": "emergency",
        "reason": "Self-harm or suicidal ideation"
    },
    94: {
        "trigger_values": ["yes", "haan", "y"],
        "severity": "emergency",
        "reason": "Convulsions / fits"
    }
}

class TriageEngine:
    def __init__(self, db: Session):
        self.db = db

    def check_red_flags(self, question_id: int, answer_text: str, session_answers: list) -> Dict[str, Any]:
        ans = str(answer_text).lower().strip()
        alert = None
        
        if question_id in RED_FLAG_RULES:
            rule = RED_FLAG_RULES[question_id]
            if any(val in ans for val in rule["trigger_values"]):
                alert = {
                    "severity": rule["severity"],
                    "reason": rule["reason"]
                }
                
        # Combined Dengue warning
        # Fever + Q26=yes + Q30=yes
        if question_id in [26, 30]:
            q1_ans = next((a for a in session_answers if a.question_id == 1), None)
            is_fever = False
            if q1_ans and q1_ans.answer_raw:
                cc = q1_ans.answer_raw.lower()
                if any(kw in cc for kw in ["fever", "bukhar", "tapman", "garam", "jwar", "ज्वर", "बुखार"]):
                    is_fever = True
            
            if is_fever:
                q26_ans = next((a for a in session_answers if a.question_id == 26), None)
                q30_ans = next((a for a in session_answers if a.question_id == 30), None)
                
                # We check if the current answer makes both true, or if they are already true
                ans26 = ans if question_id == 26 else (q26_ans.answer_raw.lower() if q26_ans else "")
                ans30 = ans if question_id == 30 else (q30_ans.answer_raw.lower() if q30_ans else "")
                
                def is_yes(t):
                    return any(y in t for y in ["yes", "haan", "y"])
                
                if is_yes(ans26) and is_yes(ans30):
                    alert = {
                        "severity": "urgent",
                        "reason": "Dengue Warning: Fever with rash and eye pain"
                    }
                    
        return alert

    def get_next_question(self, session_id: int) -> Dict[str, Any]:
        """
        Determines the next question to ask based on current session state.
        This is a basic implementation of the triage flow logic.
        """
        db_session = self.db.query(DBSession).filter(DBSession.id == session_id).first()
        if not db_session:
            return {"error": "Session not found", "status": 404}

        # Get all answers for this session
        answers = self.db.query(Answer).filter(Answer.session_id == session_id).all()
        answered_q_ids = [a.question_id for a in answers]

        # 1. Chief complaint (Q1)
        if 1 not in answered_q_ids:
            next_q = self.db.query(Question).filter(Question.id == 1).first()
            return {"question": next_q, "status": 200}
            
        # 2. General Triage (Q2 - Q12, assuming these exist based on the prompt)
        for q_id in range(2, 13):
            if q_id not in answered_q_ids:
                next_q = self.db.query(Question).filter(Question.id == q_id).first()
                if next_q:
                    return {"question": next_q, "status": 200}
        
        # 3. Complaint specific block routing
        # Basic logic: look at answer for Q1 (Chief complaint) to decide routing.
        # For MVP, we will try to find questions that match the category if Q1 keyword matches.
        q1_answer = next((a for a in answers if a.question_id == 1), None)
        
        if q1_answer:
            chief_complaint = q1_answer.answer_raw.lower() if q1_answer.answer_raw else ""
            target_category = None
            
            # Expanded Hindi/Hinglish Aliases
            if any(kw in chief_complaint for kw in ["fever", "bukhar", "tapman", "garam", "jwar", "ज्वर", "बुखार"]):
                target_category = "Fever"
            elif any(kw in chief_complaint for kw in ["cough", "khansi", "saans", "breathing", "खांसी", "खाँसी"]):
                target_category = "Cough"
            elif any(kw in chief_complaint for kw in ["pain", "dard", "peeda", "ache", "दर्द", "पीड़ा"]):
                target_category = "Pain"
            elif any(kw in chief_complaint for kw in ["abdomen", "stomach", "pet", "pait", "पेट"]):
                target_category = "Abdomen"
            
            if target_category:
                # Find next unanswered question in this category
                next_cat_qs = self.db.query(Question).filter(
                    Question.category.ilike(f"%{target_category}%")
                ).order_by(Question.id).all()
                
                for next_q in next_cat_qs:
                    if next_q.id not in answered_q_ids:
                        return {"question": next_q, "status": 200}

        # 4. If no more questions, finish triage
        if db_session.status != "completed":
            db_session.status = "completed"
            self.db.commit()
            
        return {"status": "completed", "message": "Triage complete"}
