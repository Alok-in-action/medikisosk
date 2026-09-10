"use client";

import { useState } from "react";
import { Activity, Languages, ArrowRight } from "lucide-react";
import { motion, Variants } from "framer-motion";

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { 
    opacity: 1, 
    y: 0, 
    transition: { type: "spring", stiffness: 300, damping: 24 } 
  },
};

export default function LanguageStep({ onNext }: { onNext: (lang: string) => void }) {
  const [language, setLanguage] = useState<"en" | "hi" | null>(null);

  const startSession = () => {
    if (!language) return;
    localStorage.removeItem("sessionId");
    localStorage.setItem("selectedLanguage", language);
    onNext(language);
  };

  return (
    <div className="flex flex-col items-center justify-center w-full h-full p-6">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
        className="flex items-center gap-3 mb-10 text-[var(--color-primary)]"
      >
        <Activity size={48} strokeWidth={2.5} />
        <h1 className="text-5xl font-bold tracking-tight text-[var(--foreground)]">MediKiosk</h1>
      </motion.div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="bg-[var(--color-card)] w-full max-w-2xl p-10 flex flex-col items-center rounded-3xl shadow-xl border border-[var(--color-border)]"
      >
        <motion.div variants={itemVariants} className="flex items-center gap-3 mb-8 text-[var(--foreground)]">
          <Languages size={32} />
          <h2 className="text-3xl font-bold">Select Language / भाषा चुनें</h2>
        </motion.div>
        
        <motion.div variants={itemVariants} className="flex w-full gap-6 mb-12">
          <motion.button 
            whileTap={{ scale: 0.97 }}
            onClick={() => setLanguage("hi")}
            className={`flex-1 py-10 text-4xl font-bold transition-all rounded-2xl border ${
              language === "hi" 
                ? "bg-[var(--color-primary)] text-white border-[var(--color-primary)] shadow-lg" 
                : "bg-transparent text-[var(--color-muted-foreground)] border-[var(--color-border)] hover:text-[var(--foreground)] hover:border-slate-400"
            }`}
          >
            हिंदी
          </motion.button>
          
          <motion.button 
            whileTap={{ scale: 0.97 }}
            onClick={() => setLanguage("en")}
            className={`flex-1 py-10 text-4xl font-bold transition-all rounded-2xl border ${
              language === "en" 
                ? "bg-[var(--color-primary)] text-white border-[var(--color-primary)] shadow-lg" 
                : "bg-transparent text-[var(--color-muted-foreground)] border-[var(--color-border)] hover:text-[var(--foreground)] hover:border-slate-400"
            }`}
          >
            English
          </motion.button>
        </motion.div>

        <motion.button 
          variants={itemVariants}
          whileTap={language ? { scale: 0.97 } : {}}
          onClick={startSession}
          disabled={!language}
          className={`flex items-center justify-center gap-3 w-full py-6 text-3xl font-bold rounded-xl transition-all duration-300 ease-out ${
            language
              ? "bg-[var(--color-primary)] text-white hover:shadow-lg cursor-pointer hover:-translate-y-1"
              : "bg-[var(--color-muted)] text-[var(--color-muted-foreground)] cursor-not-allowed opacity-70 border border-[var(--color-border)]"
          }`}
        >
          <span>{language === "hi" ? "शुरू करें" : "Start Session"}</span>
          <ArrowRight size={32} />
        </motion.button>
      </motion.div>
    </div>
  );
}
