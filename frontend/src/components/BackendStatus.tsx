"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Server, ServerOff, Loader2 } from "lucide-react";

type Status = "CHECKING" | "ONLINE" | "OFFLINE";

export default function BackendStatus() {
  const [status, setStatus] = useState<Status>("CHECKING");
  const [failures, setFailures] = useState(0);

  useEffect(() => {
    let mounted = true;

    const checkHealth = async () => {
      try {
        await apiFetch("/health", {}, 5000); // 5s timeout
        if (mounted) {
          setStatus("ONLINE");
          setFailures(0);
        }
      } catch (err) {
        if (mounted) {
          setFailures((prev) => {
            const next = prev + 1;
            if (next >= 2) {
              setStatus("OFFLINE");
            }
            return next;
          });
        }
      }
    };

    // Initial check
    checkHealth();

    // Poll every 30 seconds
    const intervalId = setInterval(checkHealth, 30000);

    return () => {
      mounted = false;
      clearInterval(intervalId);
    };
  }, []);

  if (status === "CHECKING") {
    return (
      <div className="fixed bottom-4 right-4 flex items-center gap-2 bg-[var(--color-card)] px-3 py-1.5 rounded-full shadow border border-gray-200 text-sm text-gray-500 z-50">
        <Loader2 size={14} className="animate-spin" />
        <span>Checking system...</span>
      </div>
    );
  }

  if (status === "OFFLINE") {
    return (
      <div className="fixed bottom-4 right-4 flex items-center gap-2 bg-red-50 px-3 py-1.5 rounded-full shadow border border-red-200 text-sm text-red-600 font-medium z-50 animate-pulse">
        <ServerOff size={14} />
        <span>System Offline</span>
      </div>
    );
  }

  // ONLINE state (can be hidden or subtle)
  return (
    <div className="fixed bottom-4 right-4 flex items-center gap-2 bg-green-50 px-3 py-1.5 rounded-full shadow border border-green-200 text-sm text-green-600 font-medium z-50 opacity-50 hover:opacity-100 transition-opacity">
      <Server size={14} />
      <span>System Online</span>
    </div>
  );
}
