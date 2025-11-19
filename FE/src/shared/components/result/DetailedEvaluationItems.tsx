import React, { useMemo } from "react";
import { AudioWaveform, Activity, Radio, Heart, ListChecks, ArrowRight } from "lucide-react";
import DetailedEvaluationItemCard from "./DetailedEvaluationItemCard";
import { Button } from "@/shared/components/ui/button";
import type { DetailedEvaluationItem, EvaluationStatus, ItemFeedback } from "@/shared/types/result";

/**
 * NFCD (Normalized Formant Centralization Distance) 계산 함수
 * NFCD = sqrt((F1_mean - F1_ref)^2 + (F2_mean - F2_ref)^2)
 * 
 * 한국인 남성 기준값:
 * - F1_ref = 600 Hz
 * - F2_ref = 1500 Hz
 */
export function calculateNFCD(
  f1Mean: number | null | undefined,
  f2Mean: number | null | undefined,
  f1Ref: number = 600,
  f2Ref: number = 1500
): number | null {
  if (
    f1Mean == null || f2Mean == null ||
    !Number.isFinite(f1Mean) || !Number.isFinite(f2Mean) ||
    !Number.isFinite(f1Ref) || !Number.isFinite(f2Ref)
  ) {
    return null;
  }

  const nfcd = Math.sqrt(
    Math.pow(f1Mean - f1Ref, 2) + Math.pow(f2Mean - f2Ref, 2)
  );

  return nfcd;
}

/**
 * 상태 평가 함수들
 */
const evaluateNFCD = (value: number | null | undefined): EvaluationStatus => {
  if (value == null || !Number.isFinite(value)) return "주의";
  if (value < 150) return "주의";
  if (value >= 150 && value <= 250) return "좋음";
  return "개선 필요";
};

const evaluateCPP = (value: number | null | undefined): EvaluationStatus => {
  if (value == null || !Number.isFinite(value)) return "주의";
  if (value >= 6) return "좋음";
  if (value >= 4 && value < 6) return "주의";
  return "개선 필요";
};

const evaluateHNR = (value: number | null | undefined): EvaluationStatus => {
  if (value == null || !Number.isFinite(value)) return "주의";
  if (value >= 15) return "좋음";
  if (value >= 10 && value < 15) return "주의";
  return "개선 필요";
};

const evaluateCSID = (value: number | null | undefined): EvaluationStatus => {
  if (value == null || !Number.isFinite(value)) return "주의";
  if (value < 20) return "좋음";
  if (value >= 20 && value <= 30) return "주의";
  return "개선 필요";
};

/**
 * PraatMetrics 타입 정의 (feature에서 정의된 타입을 참조하지 않도록)
 */
interface PraatData {
  f1?: number | null;
  f2?: number | null;
  cpp?: number | null;
  hnr?: number | null;
  csid?: number | null;
}

interface DetailedEvaluationItemsComponentProps {
  praatData?: PraatData | null;
  feedback?: ItemFeedback | null;
  onDetailClick?: () => void; // 자세히 보기 버튼 클릭 핸들러 (optional)
  showDetailButton?: boolean; // 자세히 보기 버튼 표시 여부
}

/**
 * 세부 평가 항목 컴포넌트
 * 순수 프레젠테이션 컴포넌트 - 라우팅 로직은 props로 받습니다.
 */
const DetailedEvaluationItems: React.FC<DetailedEvaluationItemsComponentProps> = ({
  praatData,
  feedback,
  onDetailClick,
  showDetailButton = true,
}) => {
  // NFCD 계산 (한국인 남성 기준)
  const nfcd = useMemo(() => {
    if (!praatData) return null;
    
    if (praatData.f1 != null && praatData.f2 != null) {
      return calculateNFCD(praatData.f1, praatData.f2, 600, 1500);
    }
    
    return null;
  }, [praatData]);

  // Praat 값에서 상태 평가
  const evaluationData = useMemo<DetailedEvaluationItem[]>(() => {
    const items: DetailedEvaluationItem[] = [];

    // 모음 왜곡도 (NFCD 사용)
    const nfcdStatus = evaluateNFCD(nfcd);
    items.push({
      id: "vowel_distortion",
      title: "모음 왜곡도",
      status: nfcdStatus,
      icon: AudioWaveform,
      content: feedback?.vowel_distortion,
    });

    // 소리의 안정도 (CPP 사용)
    const cppStatus = evaluateCPP(praatData?.cpp);
    items.push({
      id: "sound_stability",
      title: "소리의 안정도",
      status: cppStatus,
      icon: Activity,
      content: feedback?.sound_stability,
    });

    // 음성 일탈도 (HNR 사용)
    const hnrStatus = evaluateHNR(praatData?.hnr);
    items.push({
      id: "voice_clarity",
      title: "음성 일탈도",
      status: hnrStatus,
      icon: Radio,
      content: feedback?.voice_clarity,
    });

    // 음성 건강지수 (CSID 사용)
    const csidStatus = evaluateCSID(praatData?.csid);
    items.push({
      id: "voice_health",
      title: "음성 건강지수",
      status: csidStatus,
      icon: Heart,
      content: feedback?.voice_health,
    });

    return items;
  }, [praatData, nfcd, feedback]);

  return (
    <div className="self-stretch px-6 py-7 rounded-2xl shadow-[0px_1px_2px_-1px_rgba(0,0,0,0.10)] shadow-[0px_1px_3px_0px_rgba(0,0,0,0.10)] border-t border-slate-200 flex flex-col gap-6">
      {/* 제목 섹션 */}
      <div className="self-stretch flex justify-start items-start">
        <div className="flex-1 h-6 flex justify-start items-center">
          <div className="pr-3 flex justify-start items-start">
            <div className="self-stretch flex justify-start items-center">
              <ListChecks
                className="w-7 h-7 text-green-500"
                strokeWidth={2.5}
              />
            </div>
          </div>
          <div className="text-slate-800 text-2xl md:text-3xl font-semibold leading-9">
            세부 평가 항목
          </div>
        </div>
      </div>

      {/* 카드 그리드 - 가로 1개씩 4개 배치 */}
      <div className="self-stretch flex flex-col justify-start items-start gap-4">
        {evaluationData.map((item) => (
          <DetailedEvaluationItemCard key={item.id} item={item} />
        ))}
      </div>
      
      {/* 자세히 보기 버튼 */}
      {showDetailButton && onDetailClick && (
        <div className="self-stretch flex justify-center items-center mt-6">
          <Button
            className="h-auto min-h-10 px-6 py-4 bg-green-500 hover:bg-green-600 rounded-xl inline-flex justify-center items-center gap-3 text-white text-3xl font-semibold leading-9"
            onClick={onDetailClick}
          >
            <span className="text-center justify-center">자세히 보기</span>
            <ArrowRight className="w-8 h-8" />
          </Button>
        </div>
      )}
    </div>
  );
};

export default DetailedEvaluationItems;
export type { DetailedEvaluationItemsComponentProps };

