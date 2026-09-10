import json
from sqlalchemy.orm import Session as DBSession
from models import Session as PatientSession, Answer, Question, Summary

class SummaryGenerator:
    def __init__(self, db: DBSession):
        self.db = db

    def generate_summary(self, session_id: int) -> dict:
        """
        Generates a structured clinical summary for a given session.
        Groups answers by category and highlights red flags.
        """
        session = self.db.query(PatientSession).filter(PatientSession.id == session_id).first()
        if not session:
            return {"error": "Session not found"}

        answers = self.db.query(Answer).filter(Answer.session_id == session_id).all()
        if not answers:
            return {"error": "No answers found for this session"}

        # Structure the summary
        structured_summary = {
            "patient_id": session.patient_id,
            "session_id": session.id,
            "chief_complaint": None,
            "history_of_present_illness": [],
            "red_flags": [],
            "other_categories": {}
        }

        summary_text_lines = [f"Clinical Summary for Session {session.id}"]
        summary_text_lines.append("=" * 40)

        for answer in answers:
            question = self.db.query(Question).filter(Question.id == answer.question_id).first()
            if not question:
                continue

            q_text = question.text_en
            ans_text = answer.answer_raw
            category = question.category

            # Highlight Red Flags
            if answer.red_flag_triggered:
                 structured_summary["red_flags"].append({
                    "question_id": question.id,
                    "severity": answer.red_flag_severity or "urgent",
                    "reason": answer.red_flag_reason or "Triggered by clinical triage rules",
                    "question_text": q_text,
                    "patient_answer": ans_text,
                    "created_at": answer.created_at.isoformat() if answer.created_at else None
                })

            if category == "Chief Complaint" or question.id == 1:
                structured_summary["chief_complaint"] = ans_text
                summary_text_lines.append(f"\nChief Complaint: {ans_text}")
            elif category in ["HPI", "Fever", "Cough", "Pain", "Abdomen"]:
                # Group all specific complaint paths under HPI for the basic summary
                structured_summary["history_of_present_illness"].append({
                    "question": q_text,
                    "answer": ans_text
                })
            else:
                cat = category if category else "Uncategorized"
                if cat not in structured_summary["other_categories"]:
                    structured_summary["other_categories"][cat] = []
                structured_summary["other_categories"][cat].append({
                    "question": q_text,
                    "answer": ans_text
                })

        # Build text version
        if structured_summary["history_of_present_illness"]:
            summary_text_lines.append("\nHistory of Present Illness:")
            for item in structured_summary["history_of_present_illness"]:
                summary_text_lines.append(f"- {item['question']}: {item['answer']}")

        for cat, items in structured_summary["other_categories"].items():
            summary_text_lines.append(f"\n{cat}:")
            for item in items:
                summary_text_lines.append(f"- {item['question']}: {item['answer']}")

        if structured_summary["red_flags"]:
            summary_text_lines.append("\n*** RED FLAGS ***")
            for flag in structured_summary["red_flags"]:
                 summary_text_lines.append(f"- [{flag['severity'].upper()}] {flag['question_text']}: {flag['patient_answer']} (Reason: {flag.get('reason', 'N/A')})")

        summary_text = "\n".join(summary_text_lines)

        # Save to DB
        existing_summary = self.db.query(Summary).filter(Summary.session_id == session_id).first()
        if existing_summary:
            existing_summary.summary_text = summary_text
            existing_summary.summary_json = json.dumps(structured_summary)
        else:
            new_summary = Summary(
                session_id=session_id,
                summary_text=summary_text,
                summary_json=json.dumps(structured_summary)
            )
            self.db.add(new_summary)
            
        self.db.commit()

        return {
            "status": "success",
            "summary_text": summary_text,
            "summary_json": structured_summary
        }
