import os
import json
import logging

logger = logging.getLogger(__name__)

# ─── Predefined Question Bank ─────────────────────────────────────────────────
# 100 clinically relevant questions, bilingual (en / hi).
# Gemini picks IDs from this bank — it never free-generates question text.

QUESTION_BANK: dict[int, dict[str, str]] = {
    # ── Onset & Duration ──────────────────────────────────────────────────────
    1:  {"en": "When did these symptoms start?",
         "hi": "ये लक्षण कब से हैं?"},
    2:  {"en": "Did the symptoms start suddenly or gradually?",
         "hi": "लक्षण अचानक आए या धीरे-धीरे?"},
    3:  {"en": "How many days have you had these symptoms?",
         "hi": "यह तकलीफ कितने दिनों से है?"},
    4:  {"en": "Have you had these symptoms before?",
         "hi": "क्या पहले भी ऐसी तकलीफ हुई है?"},
    5:  {"en": "Are the symptoms getting worse, better, or staying the same?",
         "hi": "तकलीफ बढ़ रही है, घट रही है, या वैसी ही है?"},

    # ── Fever ────────────────────────────────────────────────────────────────
    6:  {"en": "Do you have a fever?",
         "hi": "क्या आपको बुखार है?"},
    7:  {"en": "How high is the fever?",
         "hi": "बुखार कितना है?"},
    8:  {"en": "Does the fever come and go, or is it constant?",
         "hi": "बुखार आता-जाता है या लगातार है?"},
    9:  {"en": "Do you have chills or shivering with the fever?",
         "hi": "बुखार के साथ ठंड लगती है या कंपकंपी होती है?"},
    10: {"en": "Are you sweating a lot?",
         "hi": "क्या बहुत पसीना आ रहा है?"},

    # ── Pain ─────────────────────────────────────────────────────────────────
    11: {"en": "Where exactly is the pain?",
         "hi": "दर्द ठीक कहाँ हो रहा है?"},
    12: {"en": "On a scale of 1 to 10, how bad is the pain?",
         "hi": "1 से 10 में से दर्द कितना तेज़ है?"},
    13: {"en": "Is the pain constant or does it come and go?",
         "hi": "दर्द लगातार है या आता-जाता है?"},
    14: {"en": "Does the pain spread to any other part of the body?",
         "hi": "क्या दर्द शरीर के किसी और हिस्से में भी जाता है?"},
    15: {"en": "What makes the pain better?",
         "hi": "किस चीज़ से दर्द कम होता है?"},
    16: {"en": "What makes the pain worse?",
         "hi": "किस चीज़ से दर्द बढ़ता है?"},

    # ── Head & Neurological ──────────────────────────────────────────────────
    17: {"en": "Do you have a headache?",
         "hi": "क्या सिर में दर्द है?"},
    18: {"en": "Are you feeling dizzy or lightheaded?",
         "hi": "क्या चक्कर आ रहे हैं?"},
    19: {"en": "Have you had any fits or seizures?",
         "hi": "क्या दौरा या मिर्गी जैसा कुछ हुआ?"},
    20: {"en": "Is your vision blurred or have you seen flashes of light?",
         "hi": "क्या नज़र धुंधली है या रोशनी के धब्बे दिख रहे हैं?"},

    # ── Chest & Heart ─────────────────────────────────────────────────────────
    21: {"en": "Do you have chest pain or tightness?",
         "hi": "क्या सीने में दर्द या भारीपन है?"},
    22: {"en": "Are you short of breath?",
         "hi": "क्या सांस लेने में तकलीफ हो रही है?"},
    23: {"en": "Do you feel your heart beating fast or irregularly?",
         "hi": "क्या दिल तेज़ या अनियमित धड़क रहा है?"},
    24: {"en": "Do you have swelling in your feet or legs?",
         "hi": "क्या पैरों में सूजन है?"},

    # ── Stomach & Digestion ──────────────────────────────────────────────────
    25: {"en": "Do you have stomach pain or cramps?",
         "hi": "क्या पेट में दर्द या ऐंठन है?"},
    26: {"en": "Have you had vomiting?",
         "hi": "क्या उल्टी हुई है?"},
    27: {"en": "Do you have loose motions or diarrhea?",
         "hi": "क्या दस्त लग रहे हैं?"},
    28: {"en": "Are you constipated?",
         "hi": "क्या कब्ज़ है?"},
    29: {"en": "Have you noticed blood in your stool?",
         "hi": "क्या मल में खून आया है?"},
    30: {"en": "Do you have nausea (feeling like vomiting)?",
         "hi": "क्या जी मिचला रहा है?"},
    31: {"en": "Have you lost your appetite?",
         "hi": "क्या भूख कम हो गई है?"},
    32: {"en": "Have you noticed any yellowing of your skin or eyes?",
         "hi": "क्या त्वचा या आँखें पीली हो गई हैं?"},

    # ── Respiratory ──────────────────────────────────────────────────────────
    33: {"en": "Do you have a cough?",
         "hi": "क्या खांसी है?"},
    34: {"en": "Are you coughing up phlegm or blood?",
         "hi": "क्या खांसी में बलगम या खून आ रहा है?"},
    35: {"en": "Do you have a sore throat?",
         "hi": "क्या गला दर्द है?"},
    36: {"en": "Is your nose blocked or running?",
         "hi": "क्या नाक बंद है या बह रही है?"},

    # ── Urinary ──────────────────────────────────────────────────────────────
    37: {"en": "Do you have burning or pain when you urinate?",
         "hi": "क्या पेशाब करते समय जलन या दर्द होता है?"},
    38: {"en": "Are you urinating more or less than usual?",
         "hi": "क्या पेशाब सामान्य से ज़्यादा या कम आ रहा है?"},
    39: {"en": "Have you seen blood in your urine?",
         "hi": "क्या पेशाब में खून आया है?"},

    # ── Skin ─────────────────────────────────────────────────────────────────
    40: {"en": "Do you have any rash or skin changes?",
         "hi": "क्या त्वचा पर दाने या कोई बदलाव है?"},
    41: {"en": "Is there any itching?",
         "hi": "क्या खुजली हो रही है?"},
    42: {"en": "Is the rash spreading?",
         "hi": "क्या दाने फैल रहे हैं?"},

    # ── Musculoskeletal ──────────────────────────────────────────────────────
    43: {"en": "Do you have joint pain or swelling?",
         "hi": "क्या जोड़ों में दर्द या सूजन है?"},
    44: {"en": "Do you have muscle weakness or pain?",
         "hi": "क्या मांसपेशियों में कमज़ोरी या दर्द है?"},
    45: {"en": "Have you had any injuries or falls recently?",
         "hi": "क्या हाल ही में कोई चोट या गिरना हुआ है?"},

    # ── General / Constitutional ─────────────────────────────────────────────
    46: {"en": "Have you lost weight recently without trying?",
         "hi": "क्या बिना कोशिश के वज़न कम हुआ है?"},
    47: {"en": "Are you feeling very tired or weak?",
         "hi": "क्या बहुत थकान या कमज़ोरी महसूस हो रही है?"},
    48: {"en": "Have you had any fainting or blackouts?",
         "hi": "क्या बेहोशी या आँखों के आगे अंधेरा छाया है?"},
    49: {"en": "Are you sleeping well at night?",
         "hi": "क्या रात को नींद ठीक आती है?"},
    50: {"en": "Have you had a recent change in your daily routine?",
         "hi": "क्या हाल ही में दिनचर्या में कोई बदलाव हुआ है?"},

    # ── Medical History ───────────────────────────────────────────────────────
    51: {"en": "Do you have diabetes?",
         "hi": "क्या आपको मधुमेह (शुगर) है?"},
    52: {"en": "Do you have high blood pressure?",
         "hi": "क्या आपको हाई ब्लड प्रेशर है?"},
    53: {"en": "Do you have a heart condition?",
         "hi": "क्या कोई हृदय रोग है?"},
    54: {"en": "Do you have asthma or any lung disease?",
         "hi": "क्या दमा या कोई फेफड़ों की बीमारी है?"},
    55: {"en": "Do you have thyroid problems?",
         "hi": "क्या थायरॉइड की समस्या है?"},
    56: {"en": "Have you had any surgeries in the past?",
         "hi": "क्या पहले कोई ऑपरेशन हुआ है?"},
    57: {"en": "Have you been hospitalized before for any illness?",
         "hi": "क्या पहले कभी किसी बीमारी के लिए अस्पताल में भर्ती होना पड़ा है?"},

    # ── Medications & Allergies ───────────────────────────────────────────────
    58: {"en": "Are you taking any medicines right now?",
         "hi": "क्या अभी कोई दवाई ले रहे हैं?"},
    59: {"en": "Are you allergic to any medicine or food?",
         "hi": "क्या किसी दवाई या खाने से एलर्जी है?"},
    60: {"en": "Have you taken any medicine for this problem already?",
         "hi": "क्या इस तकलीफ के लिए पहले कोई दवाई ली है?"},

    # ── Women's Health ─────────────────────────────────────────────────────────
    61: {"en": "Are your periods regular?",
         "hi": "क्या माहवारी नियमित है?"},
    62: {"en": "Could you be pregnant?",
         "hi": "क्या आप गर्भवती हो सकती हैं?"},
    63: {"en": "Do you have any unusual discharge?",
         "hi": "क्या कोई असामान्य स्राव हो रहा है?"},

    # ── Eye & ENT ─────────────────────────────────────────────────────────────
    64: {"en": "Do you have ear pain or discharge from the ear?",
         "hi": "क्या कान में दर्द है या कान से कुछ आ रहा है?"},
    65: {"en": "Is there ringing in your ears?",
         "hi": "क्या कान में आवाज़ें आती हैं?"},
    66: {"en": "Do you have any eye pain or redness?",
         "hi": "क्या आँखों में दर्द या लालिमा है?"},

    # ── Mental Health ─────────────────────────────────────────────────────────
    67: {"en": "Are you feeling very anxious or stressed lately?",
         "hi": "क्या हाल ही में बहुत चिंता या तनाव हो रहा है?"},
    68: {"en": "Are you feeling very sad or low?",
         "hi": "क्या मन बहुत उदास या भारी लग रहा है?"},

    # ── Lifestyle ─────────────────────────────────────────────────────────────
    69: {"en": "Do you smoke or use tobacco?",
         "hi": "क्या आप धूम्रपान या तंबाकू लेते हैं?"},
    70: {"en": "Do you drink alcohol?",
         "hi": "क्या शराब पीते हैं?"},
    71: {"en": "What is your occupation?",
         "hi": "आपका काम क्या है?"},

    # ── Family History ─────────────────────────────────────────────────────────
    72: {"en": "Is there a family history of diabetes or heart disease?",
         "hi": "क्या परिवार में शुगर या दिल की बीमारी है?"},
    73: {"en": "Is there a family history of cancer?",
         "hi": "क्या परिवार में कैंसर का इतिहास है?"},

    # ── Food & Water ──────────────────────────────────────────────────────────
    74: {"en": "Have you eaten or drunk anything unusual recently?",
         "hi": "क्या हाल ही में कुछ बाहर का या अलग खाना खाया है?"},
    75: {"en": "Are you able to eat and drink normally?",
         "hi": "क्या खाना-पानी सामान्य रूप से ले पा रहे हैं?"},

    # ── Pediatric / Child-specific ─────────────────────────────────────────────
    76: {"en": "Is the child feeding/eating normally?",
         "hi": "क्या बच्चा सामान्य रूप से खाना-पानी ले रहा है?"},
    77: {"en": "Is the child unusually irritable or crying a lot?",
         "hi": "क्या बच्चा बहुत चिड़चिड़ा या ज़्यादा रो रहा है?"},
    78: {"en": "Has the child had vaccinations recently?",
         "hi": "क्या बच्चे को हाल ही में टीका लगा है?"},

    # ── Travel & Exposure ──────────────────────────────────────────────────────
    79: {"en": "Have you traveled anywhere recently?",
         "hi": "क्या हाल ही में कहीं यात्रा की है?"},
    80: {"en": "Have you been in contact with anyone who was ill?",
         "hi": "क्या किसी बीमार व्यक्ति के संपर्क में आए हैं?"},

    # ── Specific Red-Flag Questions ────────────────────────────────────────────
    81: {"en": "Have you had any unusual bleeding — from nose, gums, or elsewhere?",
         "hi": "क्या नाक, मसूड़ों या कहीं और से खून आया है?"},
    82: {"en": "Are you having difficulty swallowing?",
         "hi": "क्या निगलने में तकलीफ हो रही है?"},
    83: {"en": "Have you had a sudden change in your speech or difficulty speaking?",
         "hi": "क्या बोलने में अचानक बदलाव या तकलीफ हुई है?"},
    84: {"en": "Do you have weakness or numbness on one side of the body?",
         "hi": "क्या शरीर के एक तरफ कमज़ोरी या सुन्नपन है?"},
    85: {"en": "Have you had difficulty walking or balancing?",
         "hi": "क्या चलने या संतुलन बनाने में तकलीफ है?"},
    86: {"en": "Do you have a severe headache that came on suddenly like a thunderclap?",
         "hi": "क्या अचानक बहुत तेज़ सिरदर्द हुआ है?"},
    87: {"en": "Are you unable to pass urine?",
         "hi": "क्या पेशाब नहीं आ रहा है?"},
    88: {"en": "Do you have severe pain that wakes you from sleep?",
         "hi": "क्या ऐसा दर्द है जो नींद से जगा दे?"},

    # ── Follow-up & Clarification ──────────────────────────────────────────────
    89: {"en": "Is there anything else bothering you that you haven't mentioned?",
         "hi": "क्या कोई और तकलीफ है जो अभी तक नहीं बताई?"},
    90: {"en": "How is this affecting your daily activities?",
         "hi": "इस तकलीफ से रोज़मर्रा के काम कितने प्रभावित हो रहे हैं?"},
    91: {"en": "Did anything specific trigger these symptoms?",
         "hi": "क्या किसी खास वजह से ये लक्षण शुरू हुए?"},
    92: {"en": "Have you recently started or stopped any medicines?",
         "hi": "क्या हाल ही में कोई नई दवाई शुरू की है या बंद की है?"},

    # ── Dehydration / Emergency ────────────────────────────────────────────────
    93: {"en": "Are you feeling very thirsty?",
         "hi": "क्या बहुत प्यास लग रही है?"},
    94: {"en": "Are you urinating much less than usual?",
         "hi": "क्या पेशाब सामान्य से बहुत कम आ रहा है?"},
    95: {"en": "Are you feeling confused or disoriented?",
         "hi": "क्या कुछ समझ नहीं आ रहा या मन भटक रहा है?"},

    # ── Duration of chronic conditions ────────────────────────────────────────
    96: {"en": "How long have you had this chronic condition?",
         "hi": "यह पुरानी बीमारी कब से है?"},
    97: {"en": "Are you under the care of any other doctor for this?",
         "hi": "क्या इसके लिए किसी और डॉक्टर से इलाज चल रहा है?"},
    98: {"en": "Are you taking insulin or other injections?",
         "hi": "क्या इंसुलिन या कोई इंजेक्शन ले रहे हैं?"},
    99: {"en": "Do you monitor your blood sugar or blood pressure at home?",
         "hi": "क्या घर पर शुगर या बीपी नापते हैं?"},
    100:{"en": "Is there anything you are particularly worried about?",
         "hi": "क्या कोई खास चीज़ है जिसकी आपको चिंता है?"},
}

# Questions that are almost always relevant (if not asked via Gemini pick)
ALWAYS_ASK_FALLBACK = [3, 46, 58]  # duration, weight loss, current meds


class LLMService:
    def __init__(self):
        self.api_keys = []
        main_key = os.getenv("GOOGLE_API_KEY")
        if main_key:
            self.api_keys.append(main_key)
            
        fallback_keys_str = os.getenv("GEMINI_FALLBACK_API_KEYS")
        if fallback_keys_str:
            self.api_keys.extend([k.strip() for k in fallback_keys_str.split(",") if k.strip()])
            
        self.current_key_idx = 0
        self._init_client()

    def _init_client(self):
        if not self.api_keys:
            self.client = None
            logger.warning("No GOOGLE_API_KEY or fallback keys found.")
            return

        api_key = self.api_keys[self.current_key_idx]
        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
            self._genai = genai
            logger.info(f"Gemini client ready with key index {self.current_key_idx}.")
        except Exception as e:
            self.client = None
            logger.warning(f"Gemini init failed for key index {self.current_key_idx}: {e}")

    def _rotate_key(self):
        if not self.api_keys:
            return
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        logger.info(f"Rotating Gemini API key to index {self.current_key_idx}")
        self._init_client()

    # ─── Pick 3 question IDs from the bank based on symptoms ─────────────────
    def pick_question_ids(self, symptoms: str, language: str = "en") -> list[int]:
        """
        Ask Gemini to pick exactly 3 question IDs from the bank most relevant to
        the given symptoms. Returns a list of 3 int IDs. Falls back to heuristic
        if Gemini is unavailable or fails.
        """
        if not self.client:
            return self._heuristic_pick(symptoms)

        # Build a compact index to send to Gemini (just id + English text)
        index_lines = [f"{qid}: {q['en']}" for qid, q in QUESTION_BANK.items()]
        index_text = "\n".join(index_lines)

        prompt = f"""You are a clinical assistant helping a doctor triage a patient.

Patient's complaint (may be in Hindi or English):
"{symptoms}"

Below is a numbered list of medical history questions (1-100):
{index_text}

Task: Choose exactly 3 question IDs from the list above that are MOST RELEVANT to the patient's complaint.
Rules:
- Pick IDs that will give a doctor the most useful information for THIS specific complaint.
- Do NOT pick questions already covered by the complaint text.
- Output ONLY a JSON array of exactly 3 integers, e.g. [6, 13, 25]
- No explanation, no extra text."""

        for _ in range(max(1, len(self.api_keys))):
            try:
                response = self.client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=prompt,
                )
                text = response.text.strip()
                # Parse JSON array
                import re
                match = re.search(r'\[[\s\d,]+\]', text)
                if match:
                    ids = json.loads(match.group())
                    # Validate: must be 3 ints in range 1-100
                    ids = [int(i) for i in ids if 1 <= int(i) <= 100][:3]
                    if len(ids) == 3:
                        logger.info(f"Gemini picked question IDs: {ids}")
                        return ids
                break # If parsing fails, don't rotate key, just break and fallback
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    logger.warning(f"Rate limit hit on key index {self.current_key_idx}. Rotating key.")
                    self._rotate_key()
                    continue
                else:
                    logger.error(f"Gemini pick failed: {e}")
                    break

        return self._heuristic_pick(symptoms)

    def _heuristic_pick(self, symptoms: str) -> list[int]:
        """Simple keyword-based fallback question picker."""
        s = symptoms.lower()
        ids: list[int] = []

        keyword_map = [
            (["fever", "बुखार", "temperature"], [9, 3, 10]),
            (["headache", "सिर दर्द", "सिरदर्द"], [18, 20, 86]),
            (["cough", "खांसी", "throat", "गला"], [34, 35, 36]),
            (["stomach", "पेट", "vomit", "उल्टी", "diarrhea", "दस्त"], [26, 27, 30]),
            (["chest", "सीना", "heart", "दिल"], [22, 23, 21]),
            (["pain", "दर्द", "ache"], [12, 13, 16]),
            (["urine", "पेशाब"], [37, 38, 39]),
            (["rash", "दाने", "skin", "त्वचा"], [40, 41, 42]),
            (["weakness", "कमज़ोरी", "tired", "थकान"], [47, 3, 46]),
        ]

        for keywords, qids in keyword_map:
            if any(k in s for k in keywords) and len(ids) < 3:
                for qid in qids:
                    if qid not in ids:
                        ids.append(qid)
                    if len(ids) == 3:
                        break
            if len(ids) == 3:
                break

        # Fill remaining with generic questions
        for qid in ALWAYS_ASK_FALLBACK:
            if qid not in ids and len(ids) < 3:
                ids.append(qid)

        return ids[:3]

    def get_question_text(self, qid: int, language: str = "en") -> str:
        """Return the question text for a given ID in the given language."""
        q = QUESTION_BANK.get(qid, {})
        lang_key = "hi" if language == "hi" else "en"
        return q.get(lang_key, q.get("en", f"Question {qid}"))

    # ─── Generate final summary ───────────────────────────────────────────────
    def generate_summary(self, patient_info: dict, symptoms: str, history: list, extracted_text: str = "") -> dict:
        """Generates a structured summary for the doctor."""
        if not self.client:
            return self._fallback_summary(patient_info, symptoms, history, extracted_text)

        history_text = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in history])
        prompt = f"""Summarize the following patient case for a doctor. Output valid JSON only with these exact keys:
"chief_complaint", "history_of_present_illness", "report_extractions", "red_flags"

Patient Info: {json.dumps(patient_info)}
Initial Complaint: {symptoms}
Q&A History:
{history_text}
Uploaded Report Text: {extracted_text or "None"}

Rules:
- "report_extractions": MUST be an object with exactly three keys: "diagnoses" (list of strings), "medications" (list of strings), and "investigation_values" (list of strings like "Hb: 12 g/dL"). If no reports or nothing found, use empty lists [].
- "red_flags": list of strings, each a specific alarming finding. Empty list [] if none.
- Keep text fields concise (1-3 sentences).
- Output ONLY valid JSON, no markdown fences."""

        for _ in range(max(1, len(self.api_keys))):
            try:
                response = self.client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                return json.loads(response.text)
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    logger.warning(f"Rate limit hit on key index {self.current_key_idx}. Rotating key.")
                    self._rotate_key()
                    continue
                else:
                    logger.error(f"Summary generation failed: {e}")
                    break
        
        return self._fallback_summary(patient_info, symptoms, history, extracted_text)

    def _fallback_summary(self, patient_info: dict, symptoms: str, history: list, extracted_text: str) -> dict:
        qa_text = "; ".join([f"{qa['answer']}" for qa in history])
        fallback_inv = [extracted_text[:1000] + "... (truncated)"] if extracted_text else []
        return {
            "chief_complaint": symptoms,
            "history_of_present_illness": qa_text or "See raw answers.",
            "report_extractions": {
                "diagnoses": [],
                "medications": [],
                "investigation_values": fallback_inv
            },
            "red_flags": [],
        }


llm_service = LLMService()

