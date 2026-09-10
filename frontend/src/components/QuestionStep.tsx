"use client";

import { useAudioSession } from "@/hooks/useAudioSession";
import { useState } from "react";
import { Volume2, Mic, Loader2, Check, MousePointerClick } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function QuestionStep({ question, language, preferredInputMode, onAnswer, onPreferenceChange }: any) {
  const { audioState, setAudioState, playAudio, startRecording, stopRecording, micError } = useAudioSession();
  const [transcript, setTranscript] = useState("");
  const [isTtsLoading, setIsTtsLoading] = useState(false);

  const handlePlayAudio = async () => {
    setIsTtsLoading(true);
    try {
      const textToSpeak = language === "hi" ? question.text_hi : question.text_en;
      const blob = await apiFetch("/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          language,
          question_id: question.id,
          text: textToSpeak
        })
      }, 30000, "blob");
      
      const url = URL.createObjectURL(blob);
      playAudio(url);
    } catch (error: any) {
      console.error("TTS failed:", error);
      alert("Audio guidance is temporarily unavailable. Please read from the screen.");
    } finally {
      setIsTtsLoading(false);
    }
  };

  const handleRecord = async () => {
    if (audioState === "RECORDING") {
      stopRecording();
    } else {
      await startRecording(async (blob) => {
        // Send to ASR backend
        const formData = new FormData();
        const extension = blob.type.includes("mp4") ? "mp4" : "webm";
        formData.append("audio", blob, `recording.${extension}`);
        formData.append("session_id", localStorage.getItem("session_id") || "1");
        formData.append("language", language);

        try {
          const data = await apiFetch("/asr", {
            method: "POST",
            body: formData,
          });
          
          setTranscript(data.transcript);
          setAudioState("CONFIRMING_ANSWER");
        } catch (error: any) {
          console.error("ASR failed:", error);
          alert(`Could not process audio: ${error.message}. Please type your answer.`);
          setAudioState("READY_TO_ANSWER");
        }
      });
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[600px] p-10 neu-card-white w-full mx-auto relative overflow-hidden transition-all duration-300">
      
      {/* Preference Switcher Header */}
      <div className="w-full flex justify-end mb-8">
        <div className="flex bg-[var(--color-muted)] p-1 rounded-xl border border-[var(--color-border)] shadow-inner">
          <button 
            onClick={() => onPreferenceChange("voice")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-colors ${preferredInputMode === "voice" ? "bg-[var(--color-card)] text-[var(--color-primary)] shadow-sm" : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"}`}
          >
            <Mic size={18} /> {language === "hi" ? "आवाज़" : "Voice"}
          </button>
          <button 
            onClick={() => onPreferenceChange("touch")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-colors ${preferredInputMode === "touch" ? "bg-[var(--color-card)] text-[var(--color-primary)] shadow-sm" : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"}`}
          >
            <MousePointerClick size={18} /> {language === "hi" ? "स्क्रीन" : "Screen"}
          </button>
        </div>
      </div>

      <h2 className="text-4xl font-bold mb-10 text-center text-[var(--color-foreground)] leading-tight">
        {language === "hi" ? question.text_hi : question.text_en}
      </h2>

      <div className="flex justify-between items-center w-full mb-12 px-4">
        <button 
          onClick={handlePlayAudio}
          disabled={isTtsLoading || audioState === "PLAYING_QUESTION"}
          className={`flex items-center gap-2 p-4 rounded-xl transition-all font-bold text-lg border ${preferredInputMode === 'voice' ? 'bg-[var(--color-primary)] text-white hover:bg-[#06b6d4] shadow-md border-transparent' : 'bg-[var(--color-muted)] text-[var(--color-primary)] hover:bg-[#E2E8F0] border-[var(--color-border)]'} ${isTtsLoading || audioState === 'PLAYING_QUESTION' ? 'opacity-50 cursor-not-allowed' : ''}`}
          title="Listen"
        >
          {isTtsLoading ? <Loader2 size={24} className="animate-spin" /> : <Volume2 size={24} />} 
          <span>{language === "hi" ? "सवाल सुनें" : "Listen to Question"}</span>
        </button>
      </div>

      <div className={`w-full flex flex-col gap-8 transition-opacity duration-300 items-center`}>
        
        <div className={`w-full flex flex-col gap-8 ${preferredInputMode === 'voice' ? 'opacity-70 focus-within:opacity-100 hover:opacity-100' : 'opacity-100'} transition-opacity`}>
            {question.type === "Yes/No" || question.type === "Yes/No + detail" ? (
              <div className="flex gap-6 w-full">
                <button 
                  onClick={() => onAnswer("Yes", "touch")}
                  className="flex-1 py-8 text-3xl font-bold text-[var(--color-primary)] neu-flat hover:text-[var(--color-primary)] border-2 border-transparent focus:border-[var(--color-primary)] transition-transform hover:scale-[0.98] active:scale-[0.95]"
                >
                  Yes / हाँ
                </button>
                <button 
                  onClick={() => onAnswer("No", "touch")}
                  className="flex-1 py-8 text-3xl font-bold text-[var(--color-destructive)] neu-flat hover:text-[var(--color-destructive)] border-2 border-transparent focus:border-[var(--color-destructive)] transition-transform hover:scale-[0.98] active:scale-[0.95]"
                >
                  No / नहीं
                </button>
              </div>
            ) : null}

            {question.type === "slider" && (
              <div className="w-full px-8 flex flex-col items-center bg-[var(--color-muted)] p-8 rounded-2xl border border-[var(--color-border)]">
                <input 
                  type="range" min="1" max="10" defaultValue="5"
                  className="w-full h-6 bg-[var(--color-card)] rounded-lg appearance-none cursor-pointer accent-[var(--color-primary)] mb-6 border border-gray-300"
                  onChange={(e) => setTranscript(e.target.value)}
                />
                <div className="flex justify-between w-full mt-2 text-[var(--color-foreground)] font-bold text-2xl mb-8">
                  <span>1 (Mild)</span>
                  <span>10 (Severe)</span>
                </div>
                {transcript && (
                  <button 
                    onClick={() => onAnswer(transcript, "touch")}
                    className="mt-4 px-12 py-4 bg-[var(--color-primary)] text-white rounded-xl text-2xl font-bold flex items-center gap-3 hover:opacity-90 transition-all hover:scale-[0.98]"
                  >
                    <span>Confirm {transcript}</span>
                    <Check size={28} />
                  </button>
                )}
              </div>
            )}

            {question.type === "number pad" && (
              <div className="w-full flex flex-col items-center bg-[var(--color-muted)] p-8 rounded-2xl border border-[var(--color-border)]">
                <input 
                  type="number"
                  placeholder="0"
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  className="w-64 p-6 text-5xl text-center border-4 border-white rounded-xl focus:border-[var(--color-primary)] focus:outline-none text-[var(--color-foreground)] bg-[var(--color-card)] shadow-sm"
                />
                {transcript && (
                  <button 
                    onClick={() => onAnswer(transcript, "touch")}
                    className="mt-8 px-12 py-4 bg-[var(--color-primary)] text-white rounded-xl text-2xl font-bold flex items-center gap-3 hover:opacity-90 transition-all hover:scale-[0.98]"
                  >
                    <span>Confirm</span>
                    <Check size={28} />
                  </button>
                )}
              </div>
            )}

            {question.type === "body map" && (
              <div className="w-full grid grid-cols-2 gap-6">
                {["Head", "Chest", "Abdomen", "Back", "Left Arm", "Right Arm", "Left Leg", "Right Leg"].map(part => (
                  <button
                    key={part}
                    onClick={() => onAnswer(part, "touch")}
                    className="py-6 text-2xl font-bold text-[var(--color-foreground)] neu-flat hover:text-[var(--color-primary)] transition-transform hover:scale-[0.98] active:scale-[0.95]"
                  >
                    {part}
                  </button>
                ))}
              </div>
            )}
        </div>

        {/* Universal Mic Button */}
        <div className={`mt-8 flex flex-col items-center transition-all ${preferredInputMode === 'voice' ? 'scale-110' : 'scale-100 opacity-80 hover:opacity-100'}`}>
          {micError && (
            <div className="mb-4 p-4 bg-red-50 text-red-700 font-bold rounded-xl text-center max-w-md border border-red-200">
              {micError}
            </div>
          )}
          <button
            onClick={handleRecord}
            disabled={audioState === "PROCESSING_ASR"}
            className={`p-8 rounded-full transition-all duration-300 flex items-center justify-center ${
              audioState === "RECORDING" 
                ? "bg-red-500 text-white border-transparent animate-pulse shadow-[0_0_30px_rgba(239,68,68,0.6)]" 
                : audioState === "PROCESSING_ASR"
                ? "bg-gray-100 text-[var(--color-muted-foreground)] cursor-not-allowed border-transparent"
                : "bg-[var(--color-card)] text-[var(--color-primary)] border-4 border-[var(--color-primary)] hover:bg-[var(--color-muted)] hover:scale-[1.05]"
            }`}
          >
            {audioState === "PROCESSING_ASR" ? (
              <Loader2 size={48} className="animate-spin" />
            ) : (
              <Mic size={48} />
            )}
          </button>
          
          <p className="text-xl font-bold mt-6 text-[var(--color-muted-foreground)]">
            {audioState === "RECORDING" ? "Tap to Stop" : "Tap to Speak / बोलने के लिए दबाएं"}
          </p>
        </div>

        {transcript && (
          <div className="mt-8 w-full p-6 bg-yellow-50 border border-yellow-200 rounded-2xl overflow-hidden transition-all">
            <p className="font-bold text-xl mb-4 text-yellow-800">You said / आपने कहा:</p>
            <textarea 
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              className="w-full p-4 text-2xl border border-yellow-300 rounded-xl bg-[var(--color-card)] text-gray-800 focus:outline-none focus:border-yellow-500 min-h-[100px] shadow-inner"
            />
            <div className="flex justify-end gap-4 mt-6">
              <button 
                onClick={() => setTranscript("")}
                className="px-8 py-4 bg-[var(--color-card)] text-gray-600 font-bold text-xl rounded-xl border border-gray-300 hover:bg-gray-50 transition-colors hover:scale-[0.98]"
              >
                Clear
              </button>
              <button 
                onClick={() => onAnswer(transcript, "voice")}
                className="px-8 py-4 bg-[var(--color-primary)] text-white font-bold text-xl rounded-xl flex items-center gap-2 hover:bg-[#06b6d4] transition-colors hover:scale-[0.98]"
              >
                <Check size={24} /> Confirm
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
