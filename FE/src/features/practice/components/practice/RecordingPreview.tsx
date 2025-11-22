import React, { useEffect, useRef, useState } from "react";
import { cn } from "@/shared/utils/cn";
import type { RefObject } from "react";
import { FaceDetector, FilesetResolver } from "@mediapipe/tasks-vision";

interface RecordingPreviewProps {
  recordingState: "idle" | "recording" | "processing" | "error";

  isCameraReady: boolean;
  videoRef: RefObject<HTMLVideoElement | null>;
}

type GuidanceLevel = "idle" | "aligning" | "almost" | "ok";

const RecordingPreview: React.FC<RecordingPreviewProps> = ({
  recordingState,

  isCameraReady,
  videoRef,
}) => {
  // RecordingPreview는 라이브 카메라 미리보기만 담당합니다.
  // 녹화 결과는 RecordingResult 컴포넌트에서 처리합니다.

  const detectorRef = useRef<FaceDetector | null>(null);
  const rafRef = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // 가이드라인 상태
  const [level, setLevel] = useState<GuidanceLevel>("idle");
  const [reason, setReason] = useState<string | undefined>(undefined);

  // 녹화 중 정상/이탈 표시용
  const [inRange, setInRange] = useState<boolean>(false);

  // 가이드라인 크기 (비디오 컨테이너 크기에 비례)
  const [guideSize, setGuideSize] = useState<number>(0);

  // 임계치 (완화된 기준)
  const T = {
    centerPct: 25,     // 중앙 오차 허용 범위 (%) - 중앙에서 많이 벗어나도 OK
    scaleMin: 12,      // 최소 얼굴 크기 (화면 높이의 12%) - 매우 멀리서도 OK
    scaleMax: 75,      // 최대 얼굴 크기 (화면 높이의 75%) - 매우 가까이서도 OK
    angle: 30,         // 고개 기울임 허용 각도 (도) - 많이 기울여도 OK
    stableFrames: 3,   // 안정 상태 유지 프레임 수 - 매우 빨리 초록색으로 전환
  };

  const stableCount = useRef(0);

  // 비디오 컨테이너 크기 추적하여 가이드라인 크기 조정
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const updateGuideSize = () => {
      const width = container.offsetWidth;
      const height = container.offsetHeight;
      // 너비와 높이 중 작은 값을 기준으로 계산 (가이드라인이 넘치지 않도록)
      const minDimension = Math.min(width, height);
      // 작은 차원의 50%로 설정 (원래 md:w-56 = 224px는 450px 높이의 약 50%)
      // 얼굴이 충분히 들어갈 수 있도록 크게 설정
      const size = minDimension * 0.5;
      setGuideSize(size);
    };

    // 초기 크기 설정
    updateGuideSize();

    // ResizeObserver로 크기 변경 감지
    const resizeObserver = new ResizeObserver(() => {
      updateGuideSize();
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  // WASM + 모델 로드
  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const vision = await FilesetResolver.forVisionTasks("/wasm");
        const detector = await FaceDetector.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: "/models/blaze_face_short_range.tflite",
          },
          runningMode: "VIDEO",
        });

        if (!cancelled) {
          detectorRef.current = detector;
          console.log("✅ MediaPipe FaceDetector 로드 완료");
        }
      } catch (e) {
        console.error("❌ FaceDetection load error:", e);
      }
    })();

    return () => {
      cancelled = true;
      detectorRef.current?.close();
      detectorRef.current = null;
    };
  }, []);

  // 프레임 루프
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const tick = () => {
      try {
        const det = detectorRef.current;
        if (det && video.readyState >= 2) {
          const res = det.detectForVideo(video, performance.now());
          const faces = res?.detections ?? [];

          let nextLevel: GuidanceLevel = isCameraReady ? "aligning" : "idle";
          let nextReason: string | undefined;
          let nextInRange = false;

          if (faces.length === 1) {
            const f = faces[0];
            const bb = f.boundingBox;

            if (!bb) {
              stableCount.current = 0;
              nextLevel = isCameraReady ? "aligning" : "idle";
              nextInRange = false;
            } else {
              // 실제 비디오 스트림 해상도 사용 (MediaPipe가 반환하는 좌표 기준)
              const vw = video.videoWidth || 1;
              const vh = video.videoHeight || 1;

              const cx = (bb.originX + bb.width / 2) / vw;
              const cy = (bb.originY + bb.height / 2) / vh;
              const bboxH = bb.height / vh;

              const centerErrPct =
                (Math.hypot(cx - 0.5, cy - 0.5) / Math.SQRT1_2) * 100;
              const faceScalePct = bboxH * 100;

              // 눈 키포인트로 roll 근사
              let okAngles = true;
              const kps = f.keypoints ?? [];
              const rightEye = kps[0];
              const leftEye = kps[1];

              if (rightEye && leftEye) {
                const dy = leftEye.y - rightEye.y;
                const dx = leftEye.x - rightEye.x;
                const rollDeg = (Math.atan2(dy, dx) * 180) / Math.PI;
                okAngles = Math.abs(rollDeg) <= T.angle;
              }

              const okCenter = centerErrPct <= T.centerPct;
              const okScale =
                faceScalePct >= T.scaleMin && faceScalePct <= T.scaleMax;
              const allOk = okCenter && okScale && okAngles;

              // 녹화 중 표시용: 즉시 상태 반영
              nextInRange = allOk;

              // 녹화 전 UX용: 안정 프레임 누적
              if (allOk) {
                stableCount.current += 1;
              } else {
                stableCount.current = 0;
                nextReason = !okScale
                  ? "카메라와의 거리를 조절해주세요"
                  : !okAngles
                    ? "고개 기울임을 수평으로 맞춰주세요"
                    : !okCenter
                      ? "얼굴을 화면 중앙에 맞춰주세요"
                      : undefined;
              }

              const isStable = stableCount.current >= T.stableFrames;
              nextLevel = allOk ? (isStable ? "ok" : "almost") : "aligning";
            }
          } else if (faces.length > 1) {
            stableCount.current = 0;
            nextLevel = "aligning";
            nextReason = "한 사람만 프레임에 나오도록 해주세요";
            nextInRange = false;
          } else {
            stableCount.current = 0;
            nextLevel = isCameraReady ? "aligning" : "idle";
            nextInRange = false;
          }

          setLevel(nextLevel);
          setReason(nextReason);
          setInRange(nextInRange);
        }
      } catch (e) {
        // 탐지 실패 시: 기본 안전 상태 유지
        setInRange(false);
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [videoRef, isCameraReady]);

  // 링 스타일: 녹화 중에는 "정상=초록 / 이탈=빨강"
  // 녹화 전에는 기존 로직(흰/노랑/초록)
  const ringClass = (() => {
    if (recordingState === "recording") {
      return inRange
        ? "border-emerald-400 opacity-90 border-[6px]"
        : "border-red-500 opacity-90 border-[6px] animate-pulse";
    }

    return level === "ok"
      ? "border-emerald-400 opacity-90 border-[6px]"
      : level === "almost"
        ? "border-yellow-400 opacity-80 border-[5px]"
        : "border-white/80 opacity-60 border-4";
  })();

  // 녹화 중 상태 배지
  const recordingBadge =
    recordingState === "recording" ? (
      <div className="absolute top-3 right-3">
        {/* 작은 화면: 색상만 보이는 작은 원형 배지 */}
        <div
          className={cn(
            "sm:hidden w-4 h-4 rounded-full shadow-lg",
            inRange ? "bg-emerald-500" : "bg-red-600"
          )}
        />
        {/* 큰 화면: 텍스트 포함 배지 */}
        <div
          className={cn(
            "hidden sm:block px-3 py-1.5 rounded-full text-sm font-semibold shadow",
            inRange ? "bg-emerald-500 text-white" : "bg-red-600 text-white"
          )}
        >
          {inRange ? "정상 상태" : "가이드 이탈"}
        </div>
        {!inRange && reason && (
          <div className="mt-2 px-3 py-1.5 rounded-md bg-red-600/90 text-white text-xs shadow hidden sm:block">
            {reason}
          </div>
        )}
      </div>
    ) : null;

  // 안내 배너(녹화 전)
  const bannerMsg =
    recordingState !== "recording"
      ? level === "ok"
        ? "좋아요! 그대로 유지하세요"
        : reason ?? "얼굴을 가이드라인에 맞춰주세요"
      : null;

  return (
    <div className="flex justify-center">
      <div className="w-full max-w-[800px]">
        <div className="w-full max-w-[800px] rounded-2xl overflow-hidden">
          <div ref={containerRef} className="relative aspect-video bg-slate-900">
            {/* 라이브 비디오 */}
            <div className="absolute inset-0 overflow-hidden">
              <video
                ref={videoRef}
                className="w-full h-full object-cover"
                style={{ transform: "scaleX(-1)" }}
                muted
                playsInline
              />
            </div>

            {/* 가이드 링 */}
            <div
              aria-hidden
              className={cn(
                "pointer-events-none absolute inset-0 grid place-items-center transition-all duration-150"
              )}
            >
              <div
                className={cn(
                  "aspect-[3/4] rounded-full",
                  ringClass
                )}
                style={{
                  width: `${guideSize}px`,
                }}
              />
            </div>

            {/* 녹화 전 안내 배너 */}
            {bannerMsg && isCameraReady && (
              <div className="absolute left-1/2 -translate-x-1/2 bottom-6">
                <div className="px-6 py-3 bg-slate-900/90 rounded-full">
                  <span className="text-white text-base sm:text-lg md:text-xl font-semibold">
                    {bannerMsg}
                  </span>
                </div>
              </div>
            )}

            {/* 녹화 중 상태 배지 (정상/이탈) */}
            {recordingBadge}

          </div>
        </div>
      </div>
    </div>
  );
};

export default RecordingPreview;
