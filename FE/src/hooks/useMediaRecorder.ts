import { useRef, useState, useEffect } from 'react';

export type RecordingState = "idle" | "recording" | "processing" | "error";

interface UseMediaRecorderProps {
  preferredFps?: number;
  preferredWidth?: number;
  preferredHeight?: number;
  onSave?: (file: File, blobUrl: string) => void;
}

export const useMediaRecorder = ({
  preferredFps = 25,
  preferredWidth = 1280,
  preferredHeight = 720,
  onSave,
}: UseMediaRecorderProps) => {
  const videoRef = useRef<HTMLVideoElement>(null as any);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number>(0);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [deviceInfo, setDeviceInfo] = useState<string>("");

  // 카메라 초기화
  useEffect(() => {
    (async () => {
      try {
        const constraints: MediaStreamConstraints = {
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
          video: {
            width: { ideal: preferredWidth },
            height: { ideal: preferredHeight },
            frameRate: { ideal: preferredFps, max: preferredFps },
            facingMode: "user",
          },
        };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        mediaStreamRef.current = stream;
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.playsInline = true;
          await videoRef.current.play().catch(() => void 0);
        }

        const videoTrack = stream.getVideoTracks()[0];
        const s = videoTrack.getSettings();
        setDeviceInfo(`${s.width}x${s.height} @ ${s.frameRate ?? "?"}fps`);
      } catch (err: any) {
        setPermissionError(err?.message ?? "카메라/마이크 접근 권한을 허용해주세요.");
        setRecordingState("error");
      }
    })();

    return () => {
      stopAll();
    };
  }, [preferredFps, preferredWidth, preferredHeight]);

  const stopAll = () => {
    try {
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        recorderRef.current.stop();
      }
    } catch {}

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const startRecording = () => {
    if (!mediaStreamRef.current) return;

    try {
      setRecordingState("recording");
      setElapsed(0);
      chunksRef.current = [];

      const mimeCandidates = [
        "video/webm;codecs=vp9,opus",
        "video/webm;codecs=vp8,opus",
        "video/webm",
        "video/mp4",
      ];
      const selected = mimeCandidates.find((m) => MediaRecorder.isTypeSupported(m)) || "";

      const mr = new MediaRecorder(mediaStreamRef.current, selected ? { mimeType: selected, videoBitsPerSecond: 4_000_000 } : undefined);
      recorderRef.current = mr;

      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mr.onstop = () => {
        setRecordingState("processing");
        const blob = new Blob(chunksRef.current, { type: mr.mimeType || "video/webm" });
        const url = URL.createObjectURL(blob);
        setBlobUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return url;
        });

        const ext = mr.mimeType.includes("mp4") ? "mp4" : "webm";
        const file = new File([blob], `pronunciation_${Date.now()}.${ext}`, { type: blob.type });
        onSave?.(file, url);
        setRecordingState("idle");
      };

      mr.start(100);

      timerRef.current = window.setInterval(() => {
        setElapsed((sec) => sec + 1);
      }, 1000);
    } catch (e: any) {
      setPermissionError(e?.message ?? "녹화를 시작할 수 없습니다.");
      setRecordingState("error");
    }
  };

  const stopRecording = () => {
    try {
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        recorderRef.current.stop();
      }
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
        timerRef.current = null;
      }
    } catch (e) {
      // ignore
    }
  };

  const retake = async () => {
    setBlobUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setElapsed(0);
    setRecordingState("idle");
  };

  return {
    videoRef,
    recordingState,
    permissionError,
    elapsed,
    blobUrl,
    deviceInfo,
    startRecording,
    stopRecording,
    retake,
  };
};
