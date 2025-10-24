import React from "react";
import { cn } from "@/lib/utils";

interface RecordingPreviewProps {
  videoRef: React.RefObject<HTMLVideoElement>;
  recordingState: "idle" | "recording" | "processing" | "error";
  elapsed: number;
  blobUrl: string | null;
}

const RecordingPreview: React.FC<RecordingPreviewProps> = ({
  videoRef,
  recordingState,
  elapsed,
  blobUrl,
}) => {
  return (
    <div className="flex justify-center">
      <div className="w-full max-w-[800px]">
        <div className="w-full max-w-[800px] rounded-2xl overflow-hidden">
          <div className="relative aspect-video bg-slate-900">
              {/* Live video */}
              {!blobUrl ? (
                <video
                  ref={videoRef}
                  className="absolute inset-0 size-full object-cover"
                  muted
                  playsInline
                  autoPlay
                />
              ) : (
                <video
                  className="absolute inset-0 size-full object-cover"
                  src={blobUrl}
                  controls
                />
              )}

              {/* Guide ring */}
              <div
                aria-hidden
                className={cn(
                  "pointer-events-none absolute inset-0 grid place-items-center transition-opacity",
                  recordingState === "recording" ? "opacity-0" : "opacity-100"
                )}
              >
                <div className="w-64 sm:w-72 md:w-80 aspect-[3/4] rounded-full border-4 border-white/80 opacity-60" />
              </div>

              {/* 안내 배너 */}
              {recordingState !== "recording" && !blobUrl && (
                <div className="absolute left-1/2 -translate-x-1/2 bottom-6">
                  <div className="px-6 py-3 bg-slate-900/90 rounded-full">
                    <span className="text-white text-base sm:text-lg md:text-xl font-semibold">
                      얼굴을 가이드라인에 맞춰주세요
                    </span>
                  </div>
                </div>
              )}

              {/* 녹화 상태 표시 */}
              {recordingState === "recording" && (
                <div className="absolute top-0 left-0 right-0 p-3">
                  <div className="h-2 w-full bg-white/20 rounded-full overflow-hidden">
                    <div className="h-full bg-red-500 animate-pulse" />
                  </div>
                  <div className="mt-2 flex justify-between text-white/90 text-sm">
                    <span>녹화 중…</span>
                    <span>
                      {elapsed.toString().padStart(2, "0")}s
                    </span>
                  </div>
                </div>
              )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecordingPreview;
