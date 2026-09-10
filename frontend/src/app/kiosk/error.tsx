"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[var(--color-background)] flex flex-col justify-center items-center p-6">
      <div className="neu-card-white max-w-2xl w-full p-12 flex flex-col items-center text-center">
        <h1 className="text-3xl font-bold text-red-600 mb-6">
          Something went wrong!
        </h1>
        <p className="text-xl text-[var(--color-muted-foreground)] leading-relaxed mb-8">
          We could not load this intake screen.
        </p>
        <div className="flex gap-4">
          <button
            onClick={() => {
              localStorage.clear();
              router.push("/");
            }}
            className="px-6 py-3 border-2 border-[var(--color-primary)] text-[var(--color-primary)] rounded-lg font-bold hover:bg-[var(--color-muted)] transition-colors"
          >
            Start Again
          </button>
          <button
            onClick={() => reset()}
            className="px-6 py-3 bg-[var(--color-primary)] text-white rounded-lg font-bold hover:opacity-90 transition-opacity"
          >
            Retry
          </button>
        </div>
      </div>
    </div>
  );
}
