"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Users, Clock, AlertTriangle, ChevronRight, Stethoscope, LogOut } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

interface PatientSession {
  session_id: number;
  patient_name: string;
  status: string;
  created_at: string;
  summary: any;
}

export default function PhysicianPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<PatientSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [doctorId, setDoctorId] = useState<string | null>(null);
  const [doctorName, setDoctorName] = useState<string | null>(null);

  useEffect(() => {
    // Auth Check
    const storedDocId = localStorage.getItem("doctor_id");
    const storedDocName = localStorage.getItem("doctor_name");
    if (!storedDocId) {
      router.push("/physician/login");
      return;
    }
    setDoctorId(storedDocId);
    setDoctorName(storedDocName);
  }, [router]);

  useEffect(() => {
    if (!doctorId) return;

    fetchSessions();
    // Poll for new patients every 30s
    const interval = setInterval(fetchSessions, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doctorId]);

  const fetchSessions = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/doctor/sessions?doctor_id=${doctorId}`
      );
      if (!response.ok) throw new Error("Failed to fetch sessions");
      const data: PatientSession[] = await response.json();
      setSessions(data);
    } catch (err) {
      setError("Could not load patient list.");
    } finally {
      setLoading(false);
    }
  };

  const hasRedFlag = (summary: any) =>
    summary?.red_flags && summary.red_flags.length > 0;

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  };

  const waitingSessions = sessions.filter((s) => s.status === "completed");

  return (
    <div className="min-h-screen bg-[var(--background)] flex flex-col">
      {/* Header */}
      <header className="bg-[var(--color-card)] border-b border-[var(--color-border)] px-6 py-4 shadow-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[var(--color-primary)] rounded-xl flex items-center justify-center">
              <Stethoscope className="text-white" size={20} />
            </div>
            <div>
              <h1 className="font-bold text-[var(--foreground)] text-xl">Doctor Panel</h1>
              <p className="text-xs text-[var(--color-muted-foreground)]">
                {doctorName ? `Welcome, ${doctorName}` : "MediKiosk – Patient Queue"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 text-green-600 text-sm px-3 py-1.5 rounded-full font-medium">
              <span className="w-2 h-2 bg-green-500 rounded-full inline-block animate-pulse" />
              {sessions.length} Patients Today
            </div>
            <button
              onClick={() => {
                localStorage.removeItem("doctor_id");
                localStorage.removeItem("doctor_name");
                router.push("/physician/login");
              }}
              className="flex items-center gap-1.5 text-[var(--color-muted-foreground)] hover:text-[var(--foreground)] text-sm transition-colors font-medium"
            >
              <LogOut size={16} />
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto w-full px-6 py-8 space-y-8">
        {loading && (
          <div className="text-center py-20 text-[var(--color-muted-foreground)]">Loading patient queue…</div>
        )}

        {error && (
          <div className="text-center py-8 text-red-600 bg-red-50 rounded-xl border border-red-200">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Waiting Patients */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <Users size={20} className="text-[var(--color-primary)]" />
                <h2 className="font-bold text-[var(--foreground)] text-lg">
                  Waiting Patients ({waitingSessions.length})
                </h2>
              </div>

              {waitingSessions.length === 0 ? (
                <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-8 text-center text-[var(--color-muted-foreground)]">
                  No patients waiting right now.
                </div>
              ) : (
                <div className="space-y-3">
                  {waitingSessions.map((session) => (
                    <button
                      key={session.session_id}
                      onClick={() => router.push(`/physician/${session.session_id}`)}
                      className="w-full bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-4 flex items-center gap-4 hover:border-blue-400 hover:shadow-md transition-all text-left group"
                    >
                      <div className="w-12 h-12 bg-[var(--color-primary)] opacity-20 rounded-xl flex items-center justify-center flex-shrink-0">
                        <Users className="text-[var(--color-primary)]" size={22} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-[var(--foreground)]">
                            {session.patient_name}
                          </p>
                          {session.summary && hasRedFlag(session.summary) && (
                            <span className="flex items-center gap-1 bg-red-100 text-red-600 text-xs font-bold px-2 py-0.5 rounded-full">
                              <AlertTriangle size={11} />
                              Red Flag
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-[var(--color-muted-foreground)] mt-0.5">
                          {session.summary?.chief_complaint
                            ? `Chief complaint: ${session.summary.chief_complaint}`
                            : "Intake completed — tap to view profile"}
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-1 flex-shrink-0">
                        <div className="flex items-center gap-1 text-xs text-[var(--color-muted-foreground)]">
                          <Clock size={12} />
                          {formatTime(session.created_at)}
                        </div>
                        <ChevronRight
                          size={18}
                          className="text-[var(--color-muted-foreground)] group-hover:text-[var(--color-primary)] transition-colors"
                        />
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </section>

          </>
        )}
      </div>
    </div>
  );
}
