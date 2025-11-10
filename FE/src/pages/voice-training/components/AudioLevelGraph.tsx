// src/pages/voice-training/components/AudioLevelGraph.tsx
import {
  useEffect,
  useRef,
  useImperativeHandle,
  forwardRef,
} from "react";

type Props = {
  active: boolean;
  analyser: AnalyserNode | null;
  width?: number;
  height?: number;
  stroke?: string;
  minDb?: number;
  maxDb?: number;
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
    },
    ref
  ) => {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    // RAF & 상태
    const rafRef = useRef<number | null>(null);
    const mountedRef = useRef(false);

    // 버퍼
    const tdBufRef = useRef<Float32Array | null>(null);

    // 내부 참조 (EMA/기준선)
    const emaDbRef = useRef<number | null>(null);
    const emaDeltaRef = useRef<number | null>(null);
    const refRmsRef = useRef<number>(1.0);

    // 캘리브레이션용 최근 프레임 RMS 저장
    const calibWindowRef = useRef<number[]>([]);

    // 그리기 x 위치
    const xRef = useRef(41);

    // 그리기 영역(좌표) 계산
    const LEFT_PAD = 40;                // 눈금/라벨용 왼쪽 여백
    const DRAW_BASE_Y = height * 0.8;   // 바닥선
    const DRAW_RANGE_H = height * 0.6;  // 표시 높이

    // 유틸
    const dbFromRms = (r: number) => 20 * Math.log10(Math.max(r, EPS));
    const emaStep = (prev: number | null, next: number, a: number) =>
      prev === null ? next : prev + a * (next - prev);

    // dB 눈금 그리기 (텍스트만, 그리드 선 없음)
    const drawDbScale = (ctx: CanvasRenderingContext2D) => {
      ctx.save();
      ctx.fillStyle = "#6b7280";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "right";

      const start = Math.ceil(minDb / 10) * 10;
      const end = Math.floor(maxDb / 10) * 10;
      for (let db = end; db >= start; db -= 10) {
        const normalized = clamp((db - minDb) / (maxDb - minDb), 0, 1);
        const y = DRAW_BASE_Y - normalized * DRAW_RANGE_H;
        ctx.fillText(`${db} dB`, LEFT_PAD - 5, y + 3);
      }
      ctx.restore();
    };

    // 외부로 제공하는 메서드
    useImperativeHandle(ref, () => ({
      captureImage: async (): Promise<Blob | null> => {
        const canvas = canvasRef.current;
        if (!canvas) {
          console.error('Canvas ref 없음');
          return null;
        }
        
        return new Promise((resolve) => {
          canvas.toBlob((blob) => {
            if (!blob) {
              console.error('Canvas toBlob 실패');
            }
            resolve(blob);
          }, "image/png");
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

    // Canvas 초기화 (analyser나 크기 변경 시에만)
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
      
      // 상태 초기화
      emaDbRef.current = null;
      emaDeltaRef.current = null;
      xRef.current = 41;
    }, [analyser, width, height, minDb, maxDb]);
    
    // 그리기 루프 (active 변경에만 반응)
    useEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas || !analyser) {
        if (rafRef.current) {
          cancelAnimationFrame(rafRef.current);
          rafRef.current = null;
        }
        return;
      }
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      
      const tdBuf = tdBufRef.current;
      if (!tdBuf) return;

      // 그리기 루프 시작/중지만 제어
      mountedRef.current = true;
      let lastY = DRAW_BASE_Y;

      const draw = () => {
        if (!mountedRef.current || !analyser) {
          if (rafRef.current) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
          }
          return;
        }

        // 시간영역 데이터
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

        // 캘리브레이션용 최근 값 저장
        const cw = calibWindowRef.current;
        cw.push(rms);
        if (cw.length > 120) cw.shift();

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
    }, [active, analyser, stroke]);

    // HMR/언마운트 안전장치
    useEffect(() => {
      return () => {
        mountedRef.current = false;
        if (rafRef.current) {
          cancelAnimationFrame(rafRef.current);
          rafRef.current = null;
        }
      };
    }, []);

    return (
      <div className="border border-slate-200 rounded-lg p-2 bg-white">
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

