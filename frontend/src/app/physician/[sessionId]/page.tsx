"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Mic,
  MicOff,
  Download,
  AlertTriangle,
  User,
  FileText,
  Activity,
  ClipboardList,
  Loader2,
  Stethoscope,
  Pill,
  TestTube,
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

interface PatientSummary {
  chief_complaint?: string;
  history_of_present_illness?: string;
  report_extractions?: {
    diagnoses: string[];
    medications: string[];
    investigation_values: string[];
  };
  red_flags?: string[];
  qa_list?: { question: string; answer: string }[];
  patient?: {
    name: string;
    age: number;
    gender: string;
  };
}

export default function PatientProfilePage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingBlob, setRecordingBlob] = useState<Blob | null>(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [isSavingRecording, setIsSavingRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    fetchSummary();
  }, [sessionId]);

  const fetchSummary = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/session/${sessionId}/summary`);
      if (!response.ok) throw new Error("Not found");
      const data = await response.json();
      setSummary(data);
    } catch (err) {
      setError("Could not load patient profile.");
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];
      setRecordingBlob(null);
      setRecordingDuration(0);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        setRecordingBlob(blob);
        if (timerRef.current) clearInterval(timerRef.current);
      };

      recorder.start(1000);
      setIsRecording(true);

      timerRef.current = setInterval(() => {
        setRecordingDuration((d) => d + 1);
      }, 1000);
    } catch {
      alert("Could not access microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const downloadRecording = () => {
    if (!recordingBlob) return;
    const url = URL.createObjectURL(recordingBlob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `consultation_session_${sessionId}.webm`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatDuration = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, "0");
    const s = (secs % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* Header */}
      <header className="bg-[var(--color-card)] border-b border-[var(--color-border)] px-6 py-4 shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-[var(--color-muted)] rounded-xl transition-colors"
          >
            <ArrowLeft size={22} className="text-[var(--foreground)]" />
          </button>
          <div className="flex-1">
            <h1 className="font-bold text-[var(--foreground)] text-xl">
              Patient Profile
            </h1>
            <p className="text-xs text-[var(--color-muted-foreground)]">Session #{sessionId}</p>
          </div>

          {/* Recording controls */}
          <div className="flex items-center gap-3">
            {isRecording && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 px-3 py-1.5 rounded-full">
                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                <span className="text-red-600 text-sm font-medium tabular-nums">
                  {formatDuration(recordingDuration)}
                </span>
              </div>
            )}

            {recordingBlob && !isRecording && (
              <button
                onClick={downloadRecording}
                className="flex items-center gap-2 px-3 py-1.5 bg-[var(--color-primary)] text-white text-sm font-medium rounded-xl hover:bg-[var(--color-primary)] transition-colors"
              >
                <Download size={16} />
                Download Recording
              </button>
            )}

            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm transition-all ${
                isRecording
                  ? "bg-red-500 hover:bg-red-600 text-white"
                  : "bg-slate-100 hover:bg-slate-200 text-[var(--foreground)]"
              }`}
            >
              {isRecording ? (
                <>
                  <MicOff size={16} />
                  Stop Recording
                </>
              ) : (
                <>
                  <Mic size={16} />
                  Record Consultation
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={32} className="animate-spin text-[var(--color-primary)]" />
          </div>
        )}

        {error && (
          <div className="text-center py-12 text-red-600 bg-red-50 rounded-2xl border border-red-200">
            {error}
          </div>
        )}

        {!loading && summary && (
          <div className="space-y-6">
            {/* Patient Info Card */}
            {summary.patient && (
              <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-[var(--color-primary)] opacity-20 rounded-xl flex items-center justify-center">
                    <User className="text-[var(--color-primary)]" size={24} />
                  </div>
                  <div>
                    <h2 className="font-bold text-[var(--foreground)] text-2xl">
                      {summary.patient.name}
                    </h2>
                    <p className="text-[var(--color-muted-foreground)]">
                      {summary.patient.age} years • {summary.patient.gender}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Red Flags */}
            {summary.red_flags && summary.red_flags.length > 0 && (
              <div className="bg-red-50 border-2 border-red-300 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="text-red-600" size={22} />
                  <h3 className="font-bold text-red-700 text-lg">Red Flags</h3>
                </div>
                <ul className="space-y-2">
                  {summary.red_flags.map((flag: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-red-700">
                      <span className="mt-1.5 w-1.5 h-1.5 bg-red-500 rounded-full flex-shrink-0" />
                      {flag}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Chief Complaint */}
            {summary.chief_complaint && (
              <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="text-orange-500" size={20} />
                  <h3 className="font-bold text-[var(--foreground)]">Chief Complaint</h3>
                </div>
                <p className="text-[var(--foreground)] leading-relaxed">{summary.chief_complaint}</p>
              </div>
            )}

            {/* History of Present Illness */}
            {summary.history_of_present_illness && (
              <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <ClipboardList className="text-[var(--color-primary)]" size={20} />
                  <h3 className="font-bold text-[var(--foreground)]">History of Present Illness</h3>
                </div>
                <p className="text-[var(--foreground)] leading-relaxed whitespace-pre-line">
                  {summary.history_of_present_illness}
                </p>
              </div>
            )}

            {/* Session Q&A */}
            {summary.qa_list && summary.qa_list.length > 0 && (
              <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <Mic className="text-blue-500" size={20} />
                  <h3 className="font-bold text-[var(--foreground)]">Session Transcript</h3>
                </div>
                <div className="space-y-4">
                  {summary.qa_list.map((qa, i) => (
                    <div key={i} className="flex flex-col gap-1.5 p-4 bg-slate-50 rounded-xl border border-slate-100">
                      <p className="font-medium text-[var(--foreground)] text-sm">
                        <span className="text-[var(--color-primary)] font-bold mr-2">Q:</span>
                        {qa.question}
                      </p>
                      <p className="text-[var(--color-muted-foreground)] text-sm leading-relaxed">
                        <span className="text-slate-400 font-bold mr-2">A:</span>
                        {qa.answer}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Report Extractions */}
            {summary.report_extractions && (
              <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-5 shadow-sm space-y-6">
                <div className="flex items-center gap-2 border-b border-[var(--color-border)] pb-3">
                  <FileText className="text-purple-500" size={20} />
                  <h3 className="font-bold text-[var(--foreground)]">Extracted from Reports & Prescriptions</h3>
                </div>

                {summary.report_extractions.diagnoses.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Stethoscope className="text-blue-500" size={18} />
                      <h4 className="font-semibold text-[var(--foreground)] text-sm">Diagnoses</h4>
                    </div>
                    <ul className="list-disc list-inside space-y-1">
                      {summary.report_extractions.diagnoses.map((d, i) => (
                        <li key={i} className="text-[var(--foreground)] text-sm">{d}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {summary.report_extractions.medications.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Pill className="text-pink-500" size={18} />
                      <h4 className="font-semibold text-[var(--foreground)] text-sm">Medications</h4>
                    </div>
                    <ul className="list-disc list-inside space-y-1">
                      {summary.report_extractions.medications.map((m, i) => (
                        <li key={i} className="text-[var(--foreground)] text-sm">{m}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {summary.report_extractions.investigation_values.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <TestTube className="text-green-500" size={18} />
                      <h4 className="font-semibold text-[var(--foreground)] text-sm">Investigation Values</h4>
                    </div>
                    <ul className="list-disc list-inside space-y-1">
                      {summary.report_extractions.investigation_values.map((v, i) => (
                        <li key={i} className="text-[var(--foreground)] text-sm">{v}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {summary.report_extractions.raw_text && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="text-orange-500" size={18} />
                      <h4 className="font-semibold text-[var(--foreground)] text-sm">Raw Assessment</h4>
                    </div>
                    <div className="p-4 bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--foreground)] whitespace-pre-wrap">
                      {summary.report_extractions.raw_text}
                    </div>
                  </div>
                )}

                {summary.report_extractions.diagnoses.length === 0 && 
                 summary.report_extractions.medications.length === 0 && 
                 summary.report_extractions.investigation_values.length === 0 &&
                 !summary.report_extractions.raw_text && (
                  <p className="text-[var(--color-muted-foreground)] text-sm italic">
                    No extractions could be found or no reports were uploaded.
                  </p>
                )}
              </div>
            )}

            {/* Fallback: raw JSON */}
            {!summary.chief_complaint &&
              !summary.history_of_present_illness &&
              !summary.red_flags && (
                <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-5 shadow-sm">
                  <h3 className="font-bold text-[var(--foreground)] mb-3">Raw Summary</h3>
                  <pre className="text-sm text-[var(--foreground)] whitespace-pre-wrap break-all">
                    {JSON.stringify(summary, null, 2)}
                  </pre>
                </div>
              )}
          </div>
        )}
      </div>
    </div>
  );
}
