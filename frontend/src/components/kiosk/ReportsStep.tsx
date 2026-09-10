"use client";

import { useState } from "react";
import { Upload, X, FileText, CheckCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { API_BASE_URL, apiFetch } from "@/lib/api";

export default function ReportsStep({ language, onNext }: { language: string, onNext: () => void }) {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const isHi = language === "hi";

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    const sessionId = localStorage.getItem("sessionId");
    if (!sessionId) return onNext();

    setLoading(true);

    if (files.length > 0) {
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f));
      
      try {
        await apiFetch(`/session/${sessionId}/upload-reports`, {
          method: "POST",
          body: formData,
        }, 60000); // Wait up to 60s for large uploads + OCR
      } catch (e) {
        console.error("Upload failed", e);
      }
    }
    
    // Complete the session
    try {
      await apiFetch(`/session/${sessionId}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }, 60000); // Wait up to 60s for summary generation
    } catch (e) {
      console.error("Failed to complete session", e);
    }

    setLoading(false);
    onNext();
  };

  const variants = {
    initial: { y: 20, opacity: 0 },
    animate: { y: 0, opacity: 1 },
  };

  return (
    <div className="flex flex-col w-full h-full p-6 max-w-2xl mx-auto items-center justify-center">
      <motion.div
        variants={variants}
        initial="initial"
        animate="animate"
        className="w-full bg-[var(--color-card)] rounded-3xl p-10 shadow-xl border border-[var(--color-border)] flex flex-col items-center"
      >
        <div className="w-20 h-20 bg-[var(--color-primary)]/15 rounded-full flex items-center justify-center text-[var(--color-primary)] mb-6">
          <FileText size={40} />
        </div>
        
        <h1 className="text-3xl font-bold mb-4 text-center text-[var(--foreground)]">
          {isHi ? "पुरानी रिपोर्ट या पर्चे अपलोड करें" : "Upload Previous Reports"}
        </h1>
        <p className="text-[var(--color-muted-foreground)] text-center mb-8 text-lg">
          {isHi ? "(वैकल्पिक) कोई भी डॉक्टर का पर्चा या टेस्ट रिपोर्ट" : "(Optional) Any prescriptions or test reports"}
        </p>

        {/* Upload Area */}
        <label className="w-full border-3 border-dashed border-[var(--color-border)] hover:border-[var(--color-primary)] bg-[var(--color-background)] rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all mb-8 group">
          <input
            type="file"
            multiple
            accept="image/*,.pdf"
            className="hidden"
            onChange={handleFileChange}
          />
          <div className="w-16 h-16 bg-[var(--color-muted)] rounded-full flex items-center justify-center text-[var(--color-muted-foreground)] group-hover:bg-[var(--color-primary)]/10 group-hover:text-[var(--color-primary)] transition-colors mb-4">
            <Upload size={32} />
          </div>
          <p className="text-lg font-medium text-[var(--foreground)]">
            {isHi ? "फ़ाइल चुनने के लिए यहाँ टैप करें" : "Tap here to select files"}
          </p>
          <p className="text-sm text-[var(--color-muted-foreground)] mt-2">
            JPG, PNG, or PDF
          </p>
        </label>

        {/* File List */}
        <div className="w-full flex flex-col gap-3 mb-8">
          <AnimatePresence>
            {files.map((f, i) => (
              <motion.div
                key={i + f.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex items-center justify-between p-4 bg-[var(--color-muted)] rounded-xl border border-[var(--color-border)]"
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <CheckCircle className="text-green-500 shrink-0" size={20} />
                  <span className="text-[var(--foreground)] truncate font-medium text-sm">
                    {f.name}
                  </span>
                </div>
                <button
                  onClick={() => removeFile(i)}
                  className="p-2 text-[var(--color-muted-foreground)] hover:text-red-500 hover:bg-red-500/10 rounded-full transition-colors shrink-0"
                >
                  <X size={20} />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Action Buttons */}
        <div className="w-full flex flex-col gap-3">
          {files.length > 0 ? (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full py-5 rounded-2xl bg-[var(--color-primary)] text-white text-xl font-bold shadow-lg shadow-[var(--color-primary)]/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              {loading ? (isHi ? "अपलोड हो रहा है..." : "Uploading...") : (isHi ? "अपलोड करें और समाप्त करें" : "Upload & Finish")}
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full py-5 rounded-2xl bg-transparent border-2 border-[var(--color-primary)] text-[var(--color-primary)] text-xl font-bold hover:bg-[var(--color-primary)]/5 active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              {loading ? (isHi ? "प्रतीक्षा करें..." : "Please wait...") : (isHi ? "छोड़ें और समाप्त करें" : "Skip & Finish")}
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
