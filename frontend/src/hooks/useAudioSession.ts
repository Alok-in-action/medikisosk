"use client";

import { useState, useRef, useCallback } from "react";

export type AudioState = "IDLE" | "PLAYING_QUESTION" | "READY_TO_ANSWER" | "RECORDING" | "PROCESSING_ASR" | "CONFIRMING_ANSWER";

export function useAudioSession() {
  const [audioState, setAudioState] = useState<AudioState>("IDLE");
  const [micError, setMicError] = useState<string>("");
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  const initMicrophone = useCallback(async () => {
    setMicError("");
    if (!mediaStreamRef.current) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaStreamRef.current = stream;
        
        // Initialize AudioContext if needed for visualizers
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        audioContextRef.current = new AudioContext();
        
      } catch (err: any) {
        console.error("Microphone access denied:", err);
        setMicError("Microphone access is required to use voice input. Please allow microphone access in your browser settings.");
        return false;
      }
    }
    return true;
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && audioState === "RECORDING") {
      mediaRecorderRef.current.stop();
    }
  }, [audioState]);

  const playAudio = useCallback((url: string, onEnded?: () => void) => {
    // Strict overlap prevention
    if (audioState === "RECORDING") {
      stopRecording();
    }
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
    }

    setAudioState("PLAYING_QUESTION");
    const audio = new Audio(url);
    currentAudioRef.current = audio;

    audio.onended = () => {
      setAudioState("READY_TO_ANSWER");
      if (onEnded) onEnded();
    };

    audio.play().catch(e => {
      console.warn("Autoplay prevented:", e);
      setAudioState("READY_TO_ANSWER");
    });
  }, [audioState, stopRecording]);

  const startRecording = useCallback(async (onDataAvailable: (blob: Blob) => void) => {
    if (audioState === "PLAYING_QUESTION" && currentAudioRef.current) {
      currentAudioRef.current.pause();
    }

    const hasMic = await initMicrophone();
    if (!hasMic || !mediaStreamRef.current) return;

    setAudioState("RECORDING");
    let mimeType = "audio/webm";
    if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
      mimeType = "audio/webm;codecs=opus";
    } else if (MediaRecorder.isTypeSupported("audio/webm")) {
      mimeType = "audio/webm";
    } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
      mimeType = "audio/mp4";
    }
    
    const mediaRecorder = new MediaRecorder(mediaStreamRef.current, { mimeType });
    
    const chunks: BlobPart[] = [];
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: mimeType });
      setAudioState("PROCESSING_ASR");
      onDataAvailable(blob);
    };

    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start();

    // Safety auto-stop after 20 seconds
    setTimeout(() => {
      if (mediaRecorder.state === "recording") {
        mediaRecorder.stop();
      }
    }, 20000);
  }, [audioState, initMicrophone]);

  return {
    audioState,
    setAudioState,
    playAudio,
    startRecording,
    stopRecording,
    initMicrophone,
    micError
  };
}
