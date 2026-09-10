"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, Home, Activity } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

// Steps
import LanguageStep from "@/components/kiosk/LanguageStep";
import PatientDetailsStep from "@/components/kiosk/PatientDetailsStep";
import QAStep from "@/components/kiosk/QAStep";
import ReportsStep from "@/components/kiosk/ReportsStep";

const MASTER_STEPS = [
  { id: "language", labelEn: "Language", labelHi: "भाषा" },
  { id: "details", labelEn: "Patient Details", labelHi: "मरीज़ का विवरण" },
  { id: "qa", labelEn: "Symptoms & Q&A", labelHi: "लक्षण और सवाल" },
  { id: "reports", labelEn: "Upload Reports", labelHi: "रिपोर्ट अपलोड" },
  { id: "done", labelEn: "Done", labelHi: "पूरा हुआ" }
];

function KioskFlow() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // currentStep index in MASTER_STEPS
  const [currentStep, setCurrentStep] = useState(0);
  const [language, setLanguage] = useState<string>("en");

  // Read URL params and init state
  useEffect(() => {
    const stepParam = searchParams.get("step");
    if (stepParam) {
      const idx = MASTER_STEPS.findIndex(s => s.id === stepParam);
      if (idx !== -1) setCurrentStep(idx);
    }
    
    const savedLang = localStorage.getItem("selectedLanguage");
    if (savedLang) setLanguage(savedLang);
  }, [searchParams]);

  const updateURL = (idx: number) => {
    const stepId = MASTER_STEPS[idx].id;
    router.push(`/kiosk?step=${stepId}`, { scroll: false });
  };

  const goToStep = (idx: number) => {
    setCurrentStep(idx);
    updateURL(idx);
  };

  const isHi = language === "hi";

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <LanguageStep 
            onNext={(lang) => {
              setLanguage(lang);
              goToStep(1);
            }} 
          />
        );
      case 1:
        return (
          <PatientDetailsStep 
            language={language}
            onNext={() => goToStep(2)}
            onBack={() => goToStep(0)}
          />
        );
      case 2:
        return (
          <QAStep 
            language={language}
            onNext={() => goToStep(3)}
          />
        );
      case 3:
        return (
          <ReportsStep 
            language={language}
            onNext={() => goToStep(4)}
          />
        );
      case 4:
        return (
          <div className="flex flex-col items-center justify-center w-full h-full p-6 text-center">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", bounce: 0.5 }}
              className="bg-[var(--color-card)] p-12 rounded-3xl shadow-xl flex flex-col items-center border border-[var(--color-border)]"
            >
              <CheckCircle size={80} className="text-green-500 mb-6" />
              <h1 className="text-4xl font-bold text-[var(--foreground)] mb-4">
                {isHi ? "आपका विवरण सबमिट हो गया है!" : "Your Details are Submitted!"}
              </h1>
              <p className="text-xl text-[var(--color-muted-foreground)] mb-10 max-w-md">
                {isHi 
                  ? "कृपया डॉक्टर के बुलाने की प्रतीक्षा करें। धन्यवाद।" 
                  : "Please wait for the doctor to call you. Thank you."}
              </p>
              
              <button 
                onClick={() => {
                  localStorage.removeItem("sessionId");
                  goToStep(0);
                }}
                className="px-8 py-4 bg-[var(--color-primary)] text-white rounded-xl text-xl font-bold shadow-lg flex items-center gap-3 hover:scale-105 transition-all"
              >
                <Home size={24} />
                {isHi ? "शुरुआत पर लौटें" : "Return to Home"}
              </button>
            </motion.div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-[var(--color-background)] flex flex-col font-sans relative overflow-hidden">
      
      {/* Top Header & Progress */}
      <header className="w-full bg-[var(--color-card)] border-b border-[var(--color-border)] px-6 py-4 flex flex-col gap-4 sticky top-0 z-50">
        
        {/* Top Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-[var(--color-primary)]">
            <Activity size={32} strokeWidth={2.5} />
            <span className="text-2xl font-bold tracking-tight text-[var(--foreground)]">MediKiosk</span>
          </div>
          
          <div className="flex items-center gap-4">
            <ThemeToggle />
            {currentStep > 0 && currentStep < 4 && (
               <button 
                 onClick={() => {
                   if(confirm(isHi ? "क्या आप पक्का रद्द करना चाहते हैं?" : "Are you sure you want to cancel?")) {
                     localStorage.removeItem("sessionId");
                     goToStep(0);
                   }
                 }}
                 className="px-4 py-2 text-sm font-medium text-red-500 bg-red-500/10 hover:bg-red-500/20 rounded-full transition-colors"
               >
                 {isHi ? "रद्द करें" : "Cancel"}
               </button>
            )}
          </div>
        </div>

        {/* Master Progress Bar */}
        <div className="flex items-center justify-between w-full max-w-4xl mx-auto px-4 relative">
          {/* Progress Line */}
          <div className="absolute top-1/2 left-8 right-8 h-1 bg-[var(--color-border)] -translate-y-1/2 z-0 rounded-full overflow-hidden">
            <motion.div 
              className="h-full bg-[var(--color-primary)]"
              initial={{ width: 0 }}
              animate={{ width: `${(currentStep / (MASTER_STEPS.length - 1)) * 100}%` }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
            />
          </div>

          {/* Steps */}
          {MASTER_STEPS.map((step, idx) => {
            const isCompleted = idx < currentStep;
            const isCurrent = idx === currentStep;
            
            return (
              <div key={step.id} className="relative z-10 flex flex-col items-center gap-2">
                <div 
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300 ${
                    isCompleted 
                      ? "bg-[var(--color-primary)] text-white shadow-lg shadow-[var(--color-primary)]/30" 
                      : isCurrent
                        ? "bg-[var(--color-primary)] text-white shadow-lg shadow-[var(--color-primary)]/40 ring-4 ring-[var(--color-primary)]/20 scale-110"
                        : "bg-[var(--color-card)] border-2 border-[var(--color-border)] text-[var(--color-muted-foreground)]"
                  }`}
                >
                  {isCompleted ? <CheckCircle size={20} /> : idx + 1}
                </div>
                <span className={`text-xs font-medium max-w-[80px] text-center transition-colors ${
                  isCurrent ? "text-[var(--color-primary)] font-bold" : "text-[var(--color-muted-foreground)]"
                }`}>
                  {isHi ? step.labelHi : step.labelEn}
                </span>
              </div>
            );
          })}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-0 w-full h-full"
          >
            {renderCurrentStep()}
          </motion.div>
        </AnimatePresence>
      </main>
      
    </div>
  );
}

export default function KioskPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center"><Activity className="w-8 h-8 animate-spin text-[var(--color-primary)]" /></div>}>
      <KioskFlow />
    </Suspense>
  );
}
