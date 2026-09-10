"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { Mic, Square, ArrowRight, Bot, HeartPulse, Check, Keyboard, CheckCircle2 } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

type Step = "processing" | "question" | "listening" | "confirming";

interface ChatEntry {
  question: string;
  answer: string;
}

export default function QAStep({ language, onNext }: { language: string, onNext: () => void }) {
  const [step, setStep] = useState<Step>("processing");
  const [sessionId, setSessionId] = useState<number | null>(null);
  
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [isInitial, setIsInitial] = useState(true);
  
  const [transcript, setTranscript] = useState("");
  const [typedText, setTypedText] = useState("");
  const [showKeyboard, setShowKeyboard] = useState(false);
  const [micError, setMicError] = useState("");
  
  const [history, setHistory] = useState<ChatEntry[]>([]);
  const [pulseRing, setPulseRing] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const isMountedRef = useRef(true);
  const ttsCounterRef = useRef(0);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  const isHindi = language === "hi";

  useEffect(() => {
    const sid = localStorage.getItem("sessionId");
    if (sid) {
      setSessionId(parseInt(sid));
      fetchNextQuestion(parseInt(sid));
    } else {
      onNext(); // if no session, skip
    }
  }, []);

  const fetchNextQuestion = useCallback(async (sid: number) => {
    setStep("processing");
    try {
      const res = await fetch(`${API_BASE_URL}/session/${sid}/next-question`);
      const data = await res.json();

      if (data.status === "completed") {
        onNext();
        return;
      }

      const qText = data.question?.text || "";
      setCurrentQuestion(qText);
      setIsInitial(data.question?.is_initial || false);

      setTranscript("");
      setTypedText("");
      setShowKeyboard(false);
      setStep("question");

      playTTS(qText, language);
    } catch {
      setStep("question");
      setCurrentQuestion(
        language === "hi"
          ? "माइक पर टैप करके बताएं — आपको क्या तकलीफ हो रही है?"
          : "Tap the mic and tell us — what symptoms are you feeling?"
      );
    }
  }, [language, onNext]);

  const playTTS = async (text: string, lang: string) => {
    const currentCounter = ++ttsCounterRef.current;
    try {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      const res = await fetch(`${API_BASE_URL}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language: lang, text }),
      });
      if (!res.ok) return;
      const blob = await res.blob();
      
      if (!isMountedRef.current || currentCounter !== ttsCounterRef.current) return;
      
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.play().catch(() => {});
      audio.onended = () => URL.revokeObjectURL(url);
    } catch {}
  };

  const startRecording = async () => {
    setMicError("");
    setPulseRing(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        setPulseRing(false);
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await sendAudioForTranscription(blob);
      };

      recorder.start();
      setStep("listening");
    } catch {
      setPulseRing(false);
      setMicError(
        isHindi
          ? "माइक्रोफ़ोन एक्सेस नहीं मिली — कृपया टाइप करें"
          : "Mic access denied — please type your answer"
      );
      setShowKeyboard(true);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setStep("processing");
  };

  const sendAudioForTranscription = async (blob: Blob) => {
    setStep("processing");
    const formData = new FormData();
    formData.append("audio", blob, "audio.webm");
    formData.append("language", language);

    try {
      const res = await fetch(`${API_BASE_URL}/asr`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("ASR failed");
      const data = await res.json();
      if (data.transcript?.trim()) {
        setTranscript(data.transcript);
        setStep("confirming");
      } else {
        setMicError(
          isHindi ? "आवाज़ नहीं सुनी — कृपया दोबारा बोलें या टाइप करें" : "Couldn't hear — try again or type"
        );
        setStep("question");
      }
    } catch {
      setMicError(
        isHindi ? "आवाज़ पहचान में त्रुटि — टाइप करें" : "Voice error — please type instead"
      );
      setStep("question");
    }
  };

  const submitAnswer = async (answer: string, mode: "voice" | "touch") => {
    if (!sessionId || !answer.trim()) return;
    setStep("processing");

    try {
      await fetch(`${API_BASE_URL}/session/${sessionId}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer_raw: answer, input_mode: mode }),
      });

      setHistory((h) => [...h, { question: currentQuestion, answer }]);
      await fetchNextQuestion(sessionId);
    } catch {
      setStep("question");
    }
  };

  const handleConfirm = () => submitAnswer(transcript, "voice");
  const handleTypedSubmit = () => {
    if (typedText.trim()) submitAnswer(typedText.trim(), "touch");
  };
  const handleRetry = () => {
    setTranscript("");
    setStep("question");
  };

  const variants = {
    initial: { x: 50, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: -50, opacity: 0 },
  };

  return (
    <div className="flex flex-col w-full h-full max-w-2xl mx-auto p-6 relative justify-center">
      
      {/* Sub-progress dots for questions */}
      <div className="absolute top-6 left-0 right-0 flex justify-center gap-2">
        {[0, 1, 2, 3].map((idx) => (
          <div 
            key={idx} 
            className={`w-2.5 h-2.5 rounded-full transition-colors ${
              idx === history.length ? "bg-[var(--color-primary)]" : idx < history.length ? "bg-slate-400 dark:bg-slate-500" : "bg-[var(--color-border)]"
            }`} 
          />
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          variants={variants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={{ duration: 0.2 }}
          className="w-full flex flex-col items-center gap-8 mt-12"
        >
          {step === "processing" && (
            <div className="flex flex-col items-center gap-4 text-[var(--color-primary)] py-20">
              <div className="flex gap-2">
                <div className="w-4 h-4 bg-[var(--color-primary)] rounded-full animate-bounce" />
                <div className="w-4 h-4 bg-[var(--color-primary)] rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                <div className="w-4 h-4 bg-[var(--color-primary)] rounded-full animate-bounce" style={{ animationDelay: "0.4s" }} />
              </div>
              <p className="text-xl font-medium text-[var(--foreground)]">
                {isHindi ? "समझ रहे हैं…" : "Thinking…"}
              </p>
            </div>
          )}

          {(step === "question" || step === "listening" || step === "confirming") && (
            <>
              {/* Question Card */}
              <div className="w-full bg-[var(--color-card)] border border-[var(--color-border)] rounded-3xl p-8 flex flex-col items-center gap-4 shadow-xl">
                <div className="w-16 h-16 bg-[var(--color-primary)]/15 rounded-2xl flex items-center justify-center text-[var(--color-primary)]">
                  {isInitial ? <HeartPulse size={32} /> : <Bot size={32} />}
                </div>
                <p className="text-2xl md:text-3xl font-medium text-center text-[var(--foreground)] leading-snug">
                  {currentQuestion}
                </p>
              </div>

              {micError && (
                <div className="w-full p-4 bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400 rounded-2xl text-center font-medium border border-red-200 dark:border-red-500/20">
                  {micError}
                </div>
              )}

              {/* Confirming block */}
              {step === "confirming" && (
                <div className="w-full flex flex-col items-center gap-6">
                  <p className="text-[var(--color-muted-foreground)] font-medium uppercase tracking-wider text-sm">
                    {isHindi ? "आपने कहा:" : "You said:"}
                  </p>
                  <div className="w-full bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 text-[var(--foreground)] p-6 rounded-2xl text-xl text-center font-medium shadow-sm">
                    {transcript}
                  </div>
                  <div className="grid grid-cols-2 gap-4 w-full">
                    <button onClick={handleRetry} className="py-4 rounded-xl border border-[var(--color-border)] text-[var(--foreground)] font-medium bg-[var(--color-card)] hover:bg-[var(--color-muted)] transition-colors">
                      {isHindi ? "दोबारा बोलें" : "Try Again"}
                    </button>
                    <button onClick={handleConfirm} className="py-4 rounded-xl border border-transparent bg-green-500 hover:bg-green-600 text-white font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-green-500/20">
                      {isHindi ? "हाँ, सही है" : "Confirm"}
                      <Check size={20} />
                    </button>
                  </div>
                </div>
              )}

              {/* Mic / Keyboard Input */}
              {step !== "confirming" && (
                <div className="w-full flex flex-col items-center gap-6">
                  
                  <button
                    onClick={step === "listening" ? stopRecording : startRecording}
                    className={`relative flex items-center justify-center w-32 h-32 rounded-full transition-all duration-300 shadow-xl ${
                      step === "listening" 
                        ? "bg-red-500 text-white shadow-red-500/40 scale-110" 
                        : "bg-[var(--color-primary)] text-white shadow-[var(--color-primary)]/40 hover:scale-105"
                    }`}
                  >
                    {step === "listening" && pulseRing && (
                      <div className="absolute inset-[-12px] rounded-full border-4 border-red-500/50 animate-ping" />
                    )}
                    {step === "listening" ? <Square size={40} className="fill-current" /> : <Mic size={48} />}
                  </button>

                  <p className="text-[var(--color-muted-foreground)] font-medium">
                    {step === "listening"
                      ? (isHindi ? "बोलें… रोकने के लिए दोबारा दबाएं" : "Listening… tap to stop")
                      : (isHindi ? "बोलने के लिए दबाएं" : "Tap to Speak")}
                  </p>

                  <button
                    onClick={() => { setShowKeyboard(!showKeyboard); setTimeout(() => inputRef.current?.focus(), 100); }}
                    className="flex items-center gap-2 px-6 py-3 rounded-full border border-[var(--color-border)] text-[var(--color-muted-foreground)] font-medium hover:bg-[var(--color-muted)] hover:text-[var(--foreground)] transition-colors mt-2"
                  >
                    <Keyboard size={18} />
                    {isHindi ? "टाइप करें" : "Type instead"}
                  </button>

                  {/* Keyboard Panel */}
                  <AnimatePresence>
                    {showKeyboard && (
                      <motion.div 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="w-full flex flex-col gap-4 overflow-hidden"
                      >
                        <textarea
                          ref={inputRef}
                          value={typedText}
                          onChange={(e) => setTypedText(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleTypedSubmit(); }
                          }}
                          placeholder={isHindi ? "यहाँ टाइप करें…" : "Type your answer…"}
                          className="w-full p-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--foreground)] text-lg resize-none outline-none focus:border-[var(--color-primary)] transition-colors min-h-[120px]"
                        />
                        <button
                          disabled={!typedText.trim()}
                          onClick={handleTypedSubmit}
                          className="w-full py-4 rounded-xl bg-[var(--color-primary)] text-white font-bold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                          {isHindi ? "भेजें" : "Submit"}
                          <ArrowRight size={20} />
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
