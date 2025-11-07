// src/pages/voice-training/components/AudioLevelGraph.tsx
import {
  useEffect,
  useRef,
  useState,
  useImperativeHandle,
  forwardRef,
} from "react";

type Props = {
  active: boolean;
  analyser: AnalyserNode | null;
  width?: number;   // CSS px
  height?: number;  // CSS px
  stroke?: string;
  minDb?: number;   // 화면 스케일 하한 (기본 -60 dB)
  maxDb?: number;   // 화면 스케일 상한 (기본 0 dB)
  uiUpdateHz?: number; // 숫자표시 갱신 주파수 (기본 10Hz)
};

export type AudioLevelGraphRef = {
  captureImage: () => Promise<Blob | null>;
  calibrateBaseline: () => void; // 최근 프레임 평균값으로 기준점 캘리브레이션
};

const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
const EPS = 1e-12;

// 기본 파라미터
const DEFAULT_WIDTH = 720;
const DEFAULT_HEIGHT = 200;
const DEFAULT_MIN_DB = -60;
const DEFAULT_MAX_DB = 0;

const AudioLevelGraph = forwardRef<AudioLevelGraphRef, Props>(
  (
    {
      active,
      analyser,
      width = DEFAULT_WIDTH,
      height = DEFAULT_HEIGHT,
      stroke = "#0C2C66",
      minDb = DEFAULT_MIN_DB,
      maxDb = DEFAULT_MAX_DB,
      uiUpdateHz = 10,
    },
    ref
  ) => {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    // RAF & 상태
    const rafRef = useRef<number | null>(null);
    const mountedRef = useRef(false);

    // 버퍼
    const tdBufRef = useRef<Float32Array | null>(null);

    // UI 표시에만 쓰는 상태(쓰로틀)
    const [dbfs, setDbfs] = useState<number>(-Infinity);
    const [deltaDb, setDeltaDb] = useState<number>(-Infinity);

    // 내부 참조 (EMA/기준선)
    const emaDbRef = useRef<number | null>(null);
    const emaDeltaRef = useRef<number | null>(null);
    const refRmsRef = useRef<number>(1.0); // 기준 RMS (캘리브레이션으로 갱신)

    // 캘리브레이션용 최근 프레임 RMS 저장
    const calibWindowRef = useRef<number[]>([]);

    // 그리기 x 위치
    const xRef = useRef(41); // 좌측 여백 40px, 실제 그리기는 41부터

    // 그리기 영역(좌표) 계산
    const LEFT_PAD = 40;                // 눈금/라벨용 왼쪽 여백
    const DRAW_BASE_Y = height * 0.8;   // 바닥선
    const DRAW_RANGE_H = height * 0.6;  // 표시 높이

    // 유틸
    const dbFromRms = (r: number) => 20 * Math.log10(Math.max(r, EPS));
    const emaStep = (prev: number | null, next: number, a: number) =>
      prev === null ? next : prev + a * (next - prev);

    // dB 눈금 그리기 (minDb~maxDb, 10dB 간격)
    const drawDbScale = (ctx: CanvasRenderingContext2D) => {
      ctx.save();
      ctx.fillStyle = "#6b7280";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "right";

      const start = Math.ceil(minDb / 10) * 10;
      const end = Math.floor(maxDb / 10) * 10;
      for (let db = end; db >= start; db -= 10) {
        const normalized = clamp((db - minDb) / (maxDb - minDb), 0, 1); // 0..1
        const y = DRAW_BASE_Y - normalized * DRAW_RANGE_H;
        ctx.fillText(`${db} dB`, LEFT_PAD - 5, y + 3);
        ctx.strokeStyle = "#e5e7eb";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(LEFT_PAD, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }
      ctx.restore();
    };

    // 외부로 제공하는 메서드
    useImperativeHandle(ref, () => ({
      captureImage: async (): Promise<Blob | null> => {
        const canvas = canvasRef.current;
        if (!canvas) return null;
        return new Promise((resolve) => {
          canvas.toBlob((blob) => resolve(blob), "image/png");
        });
      },
      calibrateBaseline: () => {
        const arr = calibWindowRef.current;
        if (arr.length) {
          const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
          refRmsRef.current = Math.max(mean, EPS);
          calibWindowRef.current = [];
        }
      },
    }));

    // 메인 루프
    useEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas || !analyser) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      // HiDPI 대응
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // AnalyserNode 설정(필수는 아님)
      try {
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0;
      } catch {}

      if (!tdBufRef.current || tdBufRef.current.length !== analyser.fftSize) {
        tdBufRef.current = new Float32Array(analyser.fftSize);
      }

      // 초기 캔버스
      ctx.fillStyle = "#fff";
      ctx.fillRect(0, 0, width, height);
      drawDbScale(ctx);

      // 상태/루프 관리 초기화
      mountedRef.current = true;
      emaDbRef.current = null;
      emaDeltaRef.current = null;
      xRef.current = 41;

      let lastY = DRAW_BASE_Y;
      const uiIntervalMs = 1000 / Math.max(1, uiUpdateHz);
      let lastUiUpdate = performance.now();

      const draw = () => {
        if (!mountedRef.current) return;

        // 시간영역 데이터
        const tdBuf = tdBufRef.current!;
        // @ts-ignore (TypedArray 호환)
        analyser.getFloatTimeDomainData(tdBuf);

        // RMS → dBFS
        let sumSq = 0;
        for (let i = 0; i < tdBuf.length; i++) sumSq += tdBuf[i] * tdBuf[i];
        const rms = Math.sqrt(sumSq / tdBuf.length);
        const db = dbFromRms(rms);

        // EMA (공격 빠르게, 릴리즈 적당)
        const dbEma = emaStep(
          emaDbRef.current,
          db,
          db > (emaDbRef.current ?? -1e9) ? 0.6 : 0.25
        )!;
        emaDbRef.current = dbEma;

        // ΔdB(기준선 대비) 및 EMA
        const dDb = 20 * Math.log10(Math.max(rms, EPS) / refRmsRef.current);
        const dDbEma = emaStep(emaDeltaRef.current, dDb, 0.4)!;
        emaDeltaRef.current = dDbEma;

        // 캘리브레이션용 최근 값 저장 (적당한 길이 유지)
        const cw = calibWindowRef.current;
        cw.push(rms);
        if (cw.length > 120) cw.shift(); // 최근 ~2초@60fps

        // 숫자 표시(저주파 업데이트)
        const now = performance.now();
        if (now - lastUiUpdate >= uiIntervalMs) {
          setDbfs(dbEma);
          setDeltaDb(dDbEma);
          lastUiUpdate = now;
        }

        // 정규화 (minDb~maxDb → 0..1)
        const normalized = clamp((dbEma - minDb) / (maxDb - minDb), 0, 1);
        const y = DRAW_BASE_Y - normalized * DRAW_RANGE_H;

        // 스크롤: 현재 x 위치에서 좁은 세로 스트립만 정리(잔상 최소화)
        const x = xRef.current;
        ctx.clearRect(x, 0, 3, height);

        // 라인 그리기
        ctx.strokeStyle = stroke;
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(Math.max(LEFT_PAD, x - 1), lastY);
        ctx.lineTo(x, y);
        ctx.stroke();
        lastY = y;

        // x 진행 및 경계 처리
        xRef.current += 1;
        if (xRef.current > width) {
          xRef.current = LEFT_PAD + 1;
          // 우측 끝 → 그래프 영역만 초기화
          ctx.fillStyle = "#fff";
          ctx.fillRect(LEFT_PAD, 0, width - LEFT_PAD, height);
          drawDbScale(ctx);
          lastY = DRAW_BASE_Y;
        }

        rafRef.current = requestAnimationFrame(draw);
      };

      // 루프 스타트/스톱
      const start = () => {
        if (!mountedRef.current || rafRef.current) return;
        rafRef.current = requestAnimationFrame(draw);
      };
      const stop = () => {
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      };

      if (active) start();
      else stop();

      return () => {
        mountedRef.current = false;
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      };
    }, [active, analyser, width, height, stroke, minDb, maxDb, uiUpdateHz]);

    // HMR/언마운트 안전장치
    useEffect(() => {
      return () => {
        mountedRef.current = false;
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      };
    }, []);

    return (
      <div className="border border-slate-200 rounded-lg p-2 bg-white">
        {/* 상단 상태 표시 */}
        <div className="flex items-center gap-2 mb-1.5 text-xs text-slate-800">
          <strong className="text-blue-900">RMS→dBFS</strong>
          <span className="text-slate-600">
            dBFS: <b>{Number.isFinite(dbfs) ? dbfs.toFixed(1) : "-∞"}</b>
          </span>
          <span className="text-slate-600">
            ΔdB:{" "}
            <b>
              {Number.isFinite(deltaDb)
                ? (deltaDb >= 0 ? `+${deltaDb.toFixed(1)}` : deltaDb.toFixed(1))
                : "-∞"}
            </b>
          </span>
        </div>

        <p className="text-xs text-slate-500 font-semibold mb-1">
          🎚 Audio Level (dBFS, 범위: {minDb} ~ {maxDb} dB)
        </p>

        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          className="w-full h-auto"
        />
      </div>
    );
  }
);

AudioLevelGraph.displayName = "AudioLevelGraph";

export default AudioLevelGraph;

