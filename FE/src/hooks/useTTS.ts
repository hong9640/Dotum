import { useState, useEffect, useCallback } from "react";

interface TTSOptions {
  rate?: number;
  pitch?: number;
  volume?: number;
}

export function useTTS(lang: string = "ko-KR") {
  const [supported, setSupported] = useState(false);
  const [ready, setReady] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    // Check if speechSynthesis is supported
    if ("speechSynthesis" in window) {
      setSupported(true);
      setReady(true);
    }
  }, []);

  const speak = useCallback(
    (text: string, options: TTSOptions = {}) => {
      if (!supported) {
        console.warn("Speech synthesis not supported");
        return;
      }

      // Cancel any ongoing speech
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      utterance.rate = options.rate ?? 1;
      utterance.pitch = options.pitch ?? 1;
      utterance.volume = options.volume ?? 1;

      utterance.onstart = () => setSpeaking(true);
      utterance.onend = () => setSpeaking(false);
      utterance.onerror = () => setSpeaking(false);

      window.speechSynthesis.speak(utterance);
    },
    [supported, lang]
  );

  const cancel = useCallback(() => {
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  return {
    supported,
    ready,
    speaking,
    speak,
    cancel,
  };
}

