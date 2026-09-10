"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, ChevronLeft, User, Calendar, Phone, Activity, Stethoscope, Check } from "lucide-react";

const STEPS = [
  { id: "name", icon: User },
  { id: "age", icon: Calendar },
  { id: "gender", icon: User },
  { id: "mobile", icon: Phone },
  { id: "abha", icon: Activity },
  { id: "doctor", icon: Stethoscope },
];

export default function PatientDetails() {
  const router = useRouter();
  const [language, setLanguage] = useState("en");
  
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
    const lang = localStorage.getItem("selectedLanguage") || "en";
    setLanguage(lang);

    fetch("http://localhost:8000/doctors")
      .then((res) => res.json())
      .then((data) => setDoctors(data))
      .catch((err) => console.error("Failed to fetch doctors:", err));
  }, []);

  const handleSubmit = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/session", {
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

      if (!response.ok) throw new Error("Failed to create session");

      const data = await response.json();
      localStorage.setItem("sessionId", data.session_id);
      router.push("/kiosk");
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
    if (step > 0) setStep((prev) => prev - 1);
  };

  // Keyboard navigation support
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      nextStep();
    }
  };

  // Auto-advance for gender selection
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
    <main className="min-h-screen bg-[#0a0a0a] text-white flex flex-col">
      {/* Top Progress Bar */}
      <div className="w-full h-2 bg-gray-800">
        <motion.div 
          className="h-full bg-blue-500"
          initial={{ width: 0 }}
          animate={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* Header */}
      <header className="w-full p-6 flex justify-between items-center max-w-4xl mx-auto">
        <button 
          onClick={prevStep}
          disabled={step === 0 || loading}
          className={`flex items-center gap-2 px-4 py-2 rounded-full transition-colors ${
            step === 0 ? "opacity-0 pointer-events-none" : "hover:bg-gray-800"
          }`}
        >
          <ChevronLeft className="w-5 h-5" />
          {isHi ? "पीछे" : "Back"}
        </button>
        <div className="flex gap-2">
          {STEPS.map((s, idx) => (
            <div 
              key={s.id} 
              className={`w-2.5 h-2.5 rounded-full transition-colors ${
                idx === step ? "bg-blue-500" : idx < step ? "bg-gray-400" : "bg-gray-800"
              }`} 
            />
          ))}
        </div>
        <div className="w-[88px]" /> {/* Spacer for centering */}
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-2xl mx-auto w-full">
        
        {error && (
          <div className="mb-8 p-4 bg-red-500/20 text-red-400 rounded-xl w-full text-center border border-red-500/30">
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
            <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-8">
              <StepIcon className="w-8 h-8 text-blue-400" />
            </div>

            {/* Step 0: Name */}
            {step === 0 && (
              <>
                <h1 className="text-3xl font-light mb-8 text-center">
                  {isHi ? "मरीज़ का पूरा नाम क्या है?" : "What is the patient's full name?"}
                </h1>
                <input
                  type="text"
                  autoFocus
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isHi ? "नाम दर्ज करें" : "Enter full name"}
                  className="w-full max-w-md bg-transparent border-b-2 border-gray-700 text-3xl pb-4 outline-none focus:border-blue-500 transition-colors text-center"
                />
              </>
            )}

            {/* Step 1: Age */}
            {step === 1 && (
              <>
                <h1 className="text-3xl font-light mb-8 text-center">
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
                  className="w-48 bg-transparent border-b-2 border-gray-700 text-4xl pb-4 outline-none focus:border-blue-500 transition-colors text-center"
                />
              </>
            )}

            {/* Step 2: Gender */}
            {step === 2 && (
              <>
                <h1 className="text-3xl font-light mb-8 text-center">
                  {isHi ? "मरीज़ का लिंग क्या है?" : "What is the patient's gender?"}
                </h1>
                <div className="flex flex-col gap-4 w-full max-w-md">
                  {["Male", "Female", "Other"].map((g) => (
                    <button
                      key={g}
                      onClick={() => handleGenderSelect(g)}
                      className={`p-6 rounded-2xl text-xl font-medium transition-all ${
                        gender === g 
                          ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20 scale-[1.02]" 
                          : "bg-gray-800/50 text-gray-300 hover:bg-gray-800 hover:scale-[1.01]"
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
                <h1 className="text-3xl font-light mb-4 text-center">
                  {isHi ? "मोबाइल नंबर" : "Mobile Number"}
                </h1>
                <p className="text-gray-400 mb-8">{isHi ? "(वैकल्पिक)" : "(Optional)"}</p>
                <input
                  type="tel"
                  autoFocus
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="e.g. 9876543210"
                  className="w-full max-w-md bg-transparent border-b-2 border-gray-700 text-3xl pb-4 outline-none focus:border-blue-500 transition-colors text-center tracking-widest"
                />
              </>
            )}

            {/* Step 4: ABHA ID (Optional) */}
            {step === 4 && (
              <>
                <h1 className="text-3xl font-light mb-4 text-center">
                  {isHi ? "ABHA ID या आधार के अंतिम 4 अंक" : "ABHA ID or Aadhaar (last 4 digits)"}
                </h1>
                <p className="text-gray-400 mb-8">{isHi ? "(वैकल्पिक)" : "(Optional)"}</p>
                <input
                  type="text"
                  autoFocus
                  value={abhaId}
                  onChange={(e) => setAbhaId(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="e.g. 1234"
                  className="w-full max-w-md bg-transparent border-b-2 border-gray-700 text-3xl pb-4 outline-none focus:border-blue-500 transition-colors text-center"
                />
              </>
            )}

            {/* Step 5: Choose Doctor (Optional) */}
            {step === 5 && (
              <>
                <h1 className="text-3xl font-light mb-4 text-center">
                  {isHi ? "कोई डॉक्टर चुनें" : "Select a Doctor"}
                </h1>
                <p className="text-gray-400 mb-8">{isHi ? "(वैकल्पिक)" : "(Optional)"}</p>
                
                <div className="w-full max-w-2xl grid grid-cols-1 md:grid-cols-2 gap-4 h-[40vh] overflow-y-auto pr-2 pb-8">
                  <button
                    onClick={() => {
                      setDoctorId("");
                      handleSubmit();
                    }}
                    className={`p-6 rounded-2xl border text-left transition-all flex items-center justify-between ${
                      doctorId === "" 
                        ? "border-blue-500 bg-blue-500/10" 
                        : "border-gray-800 bg-gray-900/50 hover:border-gray-600"
                    }`}
                  >
                    <div>
                      <h3 className="text-lg font-medium text-white">{isHi ? "कोई प्राथमिकता नहीं" : "No Preference"}</h3>
                      <p className="text-sm text-gray-400">{isHi ? "जो भी उपलब्ध हो" : "Anyone available"}</p>
                    </div>
                    {doctorId === "" && <Check className="text-blue-500 w-5 h-5" />}
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
                          ? "border-blue-500 bg-blue-500/10" 
                          : "border-gray-800 bg-gray-900/50 hover:border-gray-600"
                      }`}
                    >
                      <div>
                        <h3 className="text-lg font-medium text-white">{doc.name}</h3>
                        <p className="text-sm text-blue-400">{doc.specialty}</p>
                      </div>
                      {doctorId === doc.id.toString() && <Check className="text-blue-500 w-5 h-5" />}
                    </button>
                  ))}
                </div>
              </>
            )}
          </motion.div>
        </AnimatePresence>

      </div>

      {/* Footer Navigation */}
      <footer className="w-full p-8 flex justify-center pb-12">
        <button
          id="submit-btn"
          onClick={nextStep}
          disabled={loading || (step === 0 && !name.trim()) || (step === 1 && !age) || (step === 2 && !gender)}
          className={`flex items-center gap-2 px-12 py-4 rounded-full text-xl font-medium transition-all transform hover:scale-105 active:scale-95 ${
            loading || (step === 0 && !name.trim()) || (step === 1 && !age) || (step === 2 && !gender)
              ? "bg-gray-800 text-gray-500 cursor-not-allowed"
              : "bg-blue-600 text-white shadow-xl shadow-blue-500/20"
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
    </main>
  );
}
