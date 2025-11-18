import React, { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AudioWaveform, Activity, Radio, Heart, ListChecks, ArrowRight } from "lucide-react";
import DetailedEvaluationItemCard, { type DetailedEvaluationItem, type EvaluationStatus } from "./DetailedEvaluationItemCard";
import { Button } from "@/shared/components/ui/button";
import type { PraatMetrics } from "@/features/training-session/api/praat";
import { useAlertDialog } from "@/shared/hooks/useAlertDialog";

interface DetailedEvaluationItemsProps {
  praatData?: PraatMetrics | null;
}

/**
 * NFCD (Normalized Formant Centralization Distance) 계산 함수
 * NFCD = sqrt((F1_mean - F1_ref)^2 + (F2_mean - F2_ref)^2)
 * 
 * 한국인 남성 기준값:
 * - F1_ref = 600 Hz
 * - F2_ref = 1500 Hz
 * 
 * @param f1Mean 분석 대상 화자의 평균 1포먼트 (Hz)
 * @param f2Mean 분석 대상 화자의 평균 2포먼트 (Hz)
 * @param f1Ref 정상군 남성 평균 F1 (Hz), 기본값 600
 * @param f2Ref 정상군 남성 평균 F2 (Hz), 기본값 1500
 * @returns NFCD 값 (Hz 단위, 계산 불가 시 null)
 */
export function calculateNFCD(
  f1Mean: number | null | undefined,
  f2Mean: number | null | undefined,
  f1Ref: number = 600,
  f2Ref: number = 1500
): number | null {
  // 모든 값이 유효한지 확인
  if (
    f1Mean == null || f2Mean == null ||
    !Number.isFinite(f1Mean) || !Number.isFinite(f2Mean) ||
    !Number.isFinite(f1Ref) || !Number.isFinite(f2Ref)
  ) {
    return null;
  }

  // NFCD 공식: sqrt((F1_mean - F1_ref)^2 + (F2_mean - F2_ref)^2)
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

const DetailedEvaluationItems: React.FC<DetailedEvaluationItemsProps> = ({
  praatData,
}) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { showAlert, AlertDialog: AlertDialogComponent } = useAlertDialog();

  // URL 파라미터에서 세션 정보 가져오기
  const sessionIdParam = searchParams.get("sessionId");
  const typeParam = searchParams.get("type");
  const itemIndexParam = searchParams.get("itemIndex");
  const dateParam = searchParams.get("date"); // result-detail에서 온 경우 날짜 파라미터

  // NFCD 계산 (한국인 남성 기준)
  // F1_ref = 600 Hz, F2_ref = 1500 Hz
  const nfcd = useMemo(() => {
    if (!praatData) return null;
    
    // f1, f2가 있으면 NFCD 계산
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
    });

    // 소리의 안정도 (CPP 사용)
    const cppStatus = evaluateCPP(praatData?.cpp);
    items.push({
      id: "cpp",
      title: "소리의 안정도",
      status: cppStatus,
      icon: Activity,
    });

    // 음성 맑음도 (HNR 사용)
    const hnrStatus = evaluateHNR(praatData?.hnr);
    items.push({
      id: "hnr",
      title: "음성 맑음도",
      status: hnrStatus,
      icon: Radio,
    });

    // 음성 건강지수 (CSID 사용)
    const csidStatus = evaluateCSID(praatData?.csid);
    items.push({
      id: "csid",
      title: "음성 건강지수",
      status: csidStatus,
      icon: Heart,
    });

    return items;
  }, [praatData, nfcd]);

  // 자세히 보기 버튼 클릭 핸들러
  const handleDetailClick = () => {
    if (sessionIdParam && typeParam && itemIndexParam) {
      // praat-detail 페이지로 이동
      let praatDetailUrl = `/praat-detail?sessionId=${sessionIdParam}&type=${typeParam}&itemIndex=${itemIndexParam}`;
      // date 파라미터가 있으면 함께 전달
      if (dateParam) {
        praatDetailUrl += `&date=${dateParam}`;
      }
      navigate(praatDetailUrl);
    } else {
      console.error("세션 정보가 없습니다.");
      showAlert({ description: "세션 정보를 찾을 수 없습니다." });
    }
  };

  return (
    <div className="self-stretch px-6 py-7 rounded-2xl shadow-[0px_1px_2px_-1px_rgba(0,0,0,0.10)] shadow-[0px_1px_3px_0px_rgba(0,0,0,0.10)] border-t border-slate-200 flex flex-col gap-6">
      {/* AlertDialog */}
      <AlertDialogComponent />
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

      {/* 카드 그리드 */}
      <div className="self-stretch flex justify-center items-start gap-6 flex-wrap">
        {evaluationData.map((item) => (
          <DetailedEvaluationItemCard key={item.id} item={item} />
        ))}
      </div>
      
      {/* 자세히 보기 버튼 */}
      <div className="self-stretch flex justify-center items-center mt-6">
        <Button
          className="h-auto min-h-10 px-6 py-4 bg-green-500 hover:bg-green-600 rounded-xl inline-flex justify-center items-center gap-3 text-white text-3xl font-semibold leading-9"
          onClick={handleDetailClick}
        >
          <span className="text-center justify-center">자세히 보기</span>
          <ArrowRight className="w-8 h-8" />
        </Button>
      </div>
    </div>
  );
};

export default DetailedEvaluationItems;


