import { useRef, useState, useEffect } from 'react';

export type RecordingState = "idle" | "recording" | "processing" | "error";

interface UseMediaRecorderProps {
  preferredFps?: number;
  preferredWidth?: number;
  preferredHeight?: number;
  onSave?: (file: File, blobUrl: string) => void;
}

export const useMediaRecorder = ({
  preferredFps = 18,
  preferredWidth = 1280,
  preferredHeight = 720,
  onSave,
}: UseMediaRecorderProps) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number>(0);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [liveStreamUrl, setLiveStreamUrl] = useState<string | null>(null);
  const [deviceInfo, setDeviceInfo] = useState<string>("");
  const [isCameraReady, setIsCameraReady] = useState<boolean>(false);

  // 카메라 초기화 함수
  const initializeCamera = async () => {
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

      // MediaStream을 Blob URL로 변환하여 ReactPlayer에서 사용할 수 있도록 함
      const mediaRecorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        setLiveStreamUrl(url);
      };

      // 짧은 시간 녹화하여 라이브 스트림 URL 생성
      mediaRecorder.start();
      setTimeout(() => {
        mediaRecorder.stop();
      }, 100);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.playsInline = true;
        await videoRef.current.play().catch(() => void 0);
      }

      const videoTrack = stream.getVideoTracks()[0];
      const s = videoTrack.getSettings();
      setDeviceInfo(`${s.width}x${s.height} @ ${s.frameRate ?? "?"}fps`);
      setIsCameraReady(true);
      setPermissionError(null);
    } catch (err: unknown) {
      console.error('카메라 초기화 실패:', err);
      const errorMessage = err instanceof Error ? err.message : "카메라/마이크 접근 권한을 허용해주세요.";
      setPermissionError(errorMessage);
      setRecordingState("error");
      setIsCameraReady(false);
    }
  };

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      stopAll();
    };
  }, []);

  const stopAll = () => {
    try {
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        recorderRef.current.stop();
      }
    } catch {
      // ignore
    }

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

  const closeCamera = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsCameraReady(false);
  };

  const startRecording = async () => {
    // 카메라가 준비되지 않았다면 먼저 초기화
    if (!isCameraReady) {
      await initializeCamera();
      // initializeCamera가 완료된 후 mediaStreamRef를 확인
      if (!mediaStreamRef.current) {
        console.error('카메라 초기화 실패');
        return;
      }
    }

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

        // 녹화 종료 후 카메라 닫기
        closeCamera();
      };

      mr.start(100);

      timerRef.current = window.setInterval(() => {
        setElapsed((sec) => sec + 1);
      }, 1000);
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "녹화를 시작할 수 없습니다.";
      setPermissionError(errorMessage);
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
    } catch {
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
    // 다시 녹화할 때는 카메라를 다시 열지 않음 (사용자가 녹화 시작 버튼을 눌러야 함)
  };

  return {
    videoRef,
    recordingState,
    permissionError,
    elapsed,
    blobUrl,
    liveStreamUrl,
    deviceInfo,
    isCameraReady,
    startRecording,
    stopRecording,
    retake,
  };
};
