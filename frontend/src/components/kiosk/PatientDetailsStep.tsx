"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, ChevronLeft, User, Calendar, Phone, Activity, Stethoscope, Check } from "lucide-react";
import { API_BASE_URL, apiFetch } from "@/lib/api";

const STEPS = [
  { id: "name", icon: User },
  { id: "age", icon: Calendar },
  { id: "gender", icon: User },
  { id: "mobile", icon: Phone },
  { id: "abha", icon: Activity },
  { id: "doctor", icon: Stethoscope },
];

export default function PatientDetailsStep({ onNext, onBack, language }: { onNext: () => void, onBack: () => void, language: string }) {
  // Form State
  const [step, setStep] = useState(0);
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [mobile, setMobile] = useState("");
  const [abhaId, setAbhaId] = useState("");
  const [doctorId, setDoctorId] = useState("");
  
  const [doctors, setDoctors] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isHi = language === "hi";

  useEffect(() => {
    apiFetch('/doctors')
      .then((data) => setDoctors(data))
      .catch((err) => console.error("Failed to fetch doctors:", err));
  }, []);

  const handleSubmit = async () => {
    setLoading(true);
    setError("");

    try {
      const data = await apiFetch('/session', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          age: parseInt(age),
          gender,
          mobile: mobile || undefined,
          abha_id: abhaId || undefined,
          doctor_id: doctorId ? parseInt(doctorId) : undefined,
          language,
        }),
      });

      localStorage.setItem("sessionId", data.session_id);
      onNext();
    } catch (err) {
      setError(isHi ? "कुछ गलत हो गया। कृपया प्रयास करें।" : "An error occurred. Please try again.");
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (step === 0 && !name.trim()) return;
    if (step === 1 && (!age || parseInt(age) < 0 || parseInt(age) > 120)) return;
    if (step === 2 && !gender) return;

    if (step < STEPS.length - 1) {
      setStep((prev) => prev + 1);
    } else {
      handleSubmit();
    }
  };

  const prevStep = () => {
    if (step > 0) {
      setStep((prev) => prev - 1);
    } else {
      onBack();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      nextStep();
    }
  };

  const handleGenderSelect = (val: string) => {
    setGender(val);
    setTimeout(() => {
      if (step < STEPS.length - 1) setStep(step + 1);
    }, 300);
  };

  const currentStepData = STEPS[step];
  const StepIcon = currentStepData.icon;

  const variants = {
    initial: { x: 50, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: -50, opacity: 0 },
  };

  return (
    <div className="flex flex-col w-full h-full">
      {/* Sub-Progress Header */}
      <header className="w-full p-6 flex justify-between items-center max-w-4xl mx-auto">
        <div className="w-[88px]" /> {/* Spacer for centering */}
        <div className="flex gap-2">
          {STEPS.map((s, idx) => (
            <div 
              key={s.id} 
              className={`w-2.5 h-2.5 rounded-full transition-colors ${
                idx === step ? "bg-[var(--color-primary)]" : idx < step ? "bg-slate-400 dark:bg-slate-500" : "bg-[var(--color-border)]"
              }`} 
            />
          ))}
        </div>
        <div className="w-[88px]" /> {/* Spacer for centering */}
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-2xl mx-auto w-full relative">
        
        {error && (
          <div className="absolute top-0 p-4 bg-red-500/20 text-red-600 dark:text-red-400 rounded-xl w-full text-center border border-red-500/30">
            {error}
          </div>
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            variants={variants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.2 }}
            className="w-full flex flex-col items-center"
          >
            <div className="w-16 h-16 bg-[var(--color-primary)]/10 rounded-2xl flex items-center justify-center mb-8">
              <StepIcon className="w-8 h-8 text-[var(--color-primary)]" />
            </div>

            {/* Step 0: Name */}
            {step === 0 && (
              <>
                <h1 className="text-3xl font-light mb-8 text-center text-[var(--foreground)]">
                  {isHi ? "मरीज़ का पूरा नाम क्या है?" : "What is the patient's full name?"}
                </h1>
                <input
                  type="text"
                  autoFocus
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isHi ? "नाम दर्ज करें" : "Enter full name"}
                  className="w-full max-w-md bg-transparent border-b-2 border-[var(--color-border)] text-3xl pb-4 outline-none focus:border-[var(--color-primary)] transition-colors text-center text-[var(--foreground)] placeholder:text-[var(--color-muted-foreground)]"
                />
              </>
            )}

            {/* Step 1: Age */}
            {step === 1 && (
              <>
                <h1 className="text-3xl font-light mb-8 text-center text-[var(--foreground)]">
                  {isHi ? "मरीज़ की उम्र क्या है?" : "What is the patient's age?"}
                </h1>
                <input
                  type="number"
                  autoFocus
                  min="0"
                  max="120"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isHi ? "उम्र" : "Age"}
                  className="w-48 bg-transparent border-b-2 border-[var(--color-border)] text-4xl pb-4 outline-none focus:border-[var(--color-primary)] transition-colors text-center text-[var(--foreground)] placeholder:text-[var(--color-muted-foreground)]"
                />
              </>
            )}

            {/* Step 2: Gender */}
            {step === 2 && (
              <>
                <h1 className="text-3xl font-light mb-8 text-center text-[var(--foreground)]">
                  {isHi ? "मरीज़ का लिंग क्या है?" : "What is the patient's gender?"}
                </h1>
                <div className="flex flex-col gap-4 w-full max-w-md">
                  {["Male", "Female", "Other"].map((g) => (
                    <button
                      key={g}
                      onClick={() => handleGenderSelect(g)}
                      className={`p-6 rounded-2xl text-xl font-medium transition-all border ${
                        gender === g 
                          ? "bg-[var(--color-primary)] text-white border-[var(--color-primary)] shadow-lg shadow-[var(--color-primary)]/20 scale-[1.02]" 
                          : "bg-[var(--color-card)] border-[var(--color-border)] text-[var(--foreground)] hover:border-slate-400 hover:scale-[1.01]"
                      }`}
                    >
                      {g === "Male" && (isHi ? "पुरुष (Male)" : "Male")}
                      {g === "Female" && (isHi ? "महिला (Female)" : "Female")}
                      {g === "Other" && (isHi ? "अन्य (Other)" : "Other")}
                    </button>
                  ))}
                </div>
              </>
            )}

            {/* Step 3: Mobile (Optional) */}
            {step === 3 && (
              <>
                <h1 className="text-3xl font-light mb-4 text-center text-[var(--foreground)]">
                  {isHi ? "मोबाइल नंबर" : "Mobile Number"}
                </h1>
                <p className="text-[var(--color-muted-foreground)] mb-8">{isHi ? "(वैकल्पिक)" : "(Optional)"}</p>
                <input
                  type="tel"
                  autoFocus
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="e.g. 9876543210"
                  className="w-full max-w-md bg-transparent border-b-2 border-[var(--color-border)] text-3xl pb-4 outline-none focus:border-[var(--color-primary)] transition-colors text-center tracking-widest text-[var(--foreground)] placeholder:text-[var(--color-muted-foreground)]"
                />
              </>
            )}

            {/* Step 4: ABHA ID (Optional) */}
            {step === 4 && (
              <>
                <h1 className="text-3xl font-light mb-4 text-center text-[var(--foreground)]">
                  {isHi ? "ABHA ID या आधार के अंतिम 4 अंक" : "ABHA ID or Aadhaar (last 4 digits)"}
                </h1>
                <p className="text-[var(--color-muted-foreground)] mb-8">{isHi ? "(वैकल्पिक)" : "(Optional)"}</p>
                <input
                  type="text"
                  autoFocus
                  value={abhaId}
                  onChange={(e) => setAbhaId(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="e.g. 1234"
                  className="w-full max-w-md bg-transparent border-b-2 border-[var(--color-border)] text-3xl pb-4 outline-none focus:border-[var(--color-primary)] transition-colors text-center text-[var(--foreground)] placeholder:text-[var(--color-muted-foreground)]"
                />
              </>
            )}

            {/* Step 5: Choose Doctor (Optional) */}
            {step === 5 && (
              <>
                <h1 className="text-3xl font-light mb-4 text-center text-[var(--foreground)]">
                  {isHi ? "कोई डॉक्टर चुनें" : "Select a Doctor"}
                </h1>
                <p className="text-[var(--color-muted-foreground)] mb-8">{isHi ? "(वैकल्पिक)" : "(Optional)"}</p>
                
                <div className="w-full max-w-2xl grid grid-cols-1 md:grid-cols-2 gap-4 h-[40vh] overflow-y-auto pr-2 pb-8">
                  <button
                    onClick={() => {
                      setDoctorId("");
                      handleSubmit();
                    }}
                    className={`p-6 rounded-2xl border text-left transition-all flex items-center justify-between ${
                      doctorId === "" 
                        ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10" 
                        : "border-[var(--color-border)] bg-[var(--color-card)] hover:border-slate-400"
                    }`}
                  >
                    <div>
                      <h3 className="text-lg font-medium text-[var(--foreground)]">{isHi ? "कोई प्राथमिकता नहीं" : "No Preference"}</h3>
                      <p className="text-sm text-[var(--color-muted-foreground)]">{isHi ? "जो भी उपलब्ध हो" : "Anyone available"}</p>
                    </div>
                    {doctorId === "" && <Check className="text-[var(--color-primary)] w-5 h-5" />}
                  </button>
                  
                  {doctors.map((doc) => (
                    <button
                      key={doc.id}
                      onClick={() => {
                        setDoctorId(doc.id.toString());
                        // Automatically submit when a doctor is selected on the last step
                        setTimeout(() => {
                          const submitBtn = document.getElementById('submit-btn');
                          if(submitBtn) submitBtn.click();
                        }, 300);
                      }}
                      className={`p-6 rounded-2xl border text-left transition-all flex items-center justify-between ${
                        doctorId === doc.id.toString() 
                          ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10" 
                          : "border-[var(--color-border)] bg-[var(--color-card)] hover:border-slate-400"
                      }`}
                    >
                      <div>
                        <h3 className="text-lg font-medium text-[var(--foreground)]">{doc.name}</h3>
                        <p className="text-sm text-[var(--color-primary)]">{doc.specialty}</p>
                      </div>
                      {doctorId === doc.id.toString() && <Check className="text-[var(--color-primary)] w-5 h-5" />}
                    </button>
                  ))}
                </div>
              </>
            )}
          </motion.div>
        </AnimatePresence>

      </div>

      {/* Footer Navigation */}
      <footer className="w-full p-8 flex justify-center items-center gap-6 pb-12">
        <button 
          onClick={prevStep}
          disabled={loading}
          className="flex items-center gap-2 px-8 py-4 rounded-full text-xl font-medium transition-all text-[var(--foreground)] bg-[var(--color-card)] border-2 border-[var(--color-border)] hover:bg-[var(--color-muted)] active:scale-95"
        >
          <ChevronLeft className="w-6 h-6" />
          {isHi ? "पीछे" : "Back"}
        </button>
        <button
          id="submit-btn"
          onClick={nextStep}
          disabled={loading || (step === 0 && !name.trim()) || (step === 1 && !age) || (step === 2 && !gender)}
          className={`flex items-center gap-2 px-12 py-4 rounded-full text-xl font-medium transition-all transform hover:scale-105 active:scale-95 ${
            loading || (step === 0 && !name.trim()) || (step === 1 && !age) || (step === 2 && !gender)
              ? "bg-[var(--color-muted)] text-[var(--color-muted-foreground)] border border-[var(--color-border)] cursor-not-allowed"
              : "bg-[var(--color-primary)] text-white shadow-xl shadow-[var(--color-primary)]/20"
          }`}
        >
          {loading ? (
             isHi ? "प्रोसेस हो रहा है..." : "Processing..."
          ) : step === STEPS.length - 1 ? (
             isHi ? "शुरू करें" : "Start Intake"
          ) : (
             isHi ? "आगे बढ़ें" : "Next"
          )}
          {!loading && step < STEPS.length - 1 && <ChevronRight className="w-6 h-6" />}
        </button>
      </footer>
    </div>
  );
}
