import React, { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AudioWaveform, Activity, Radio, Heart, ListChecks, ArrowRight } from "lucide-react";
import DetailedEvaluationItemCard, { type DetailedEvaluationItem } from "./DetailedEvaluationItemCard";
import { Button } from "@/components/ui/button";
import type { PraatMetrics } from "@/api/training-session/praat";

interface DetailedEvaluationItemsProps {
  praatData?: PraatMetrics | null;
  praatLoading?: boolean;
}

/**
 * VSA (Vowel Space Area) 계산 함수
 * VSA = |(F1i(F2a-F2u) + F1a(F2u-F2i) + F1u(F2i-F2a))| / 2
 * 
 * TODO: 백엔드에서 3개 모음(/i/, /a/, /u/) 각각의 F1, F2를 제공하면 사용
 * 
 * @param f1i 첫 번째 모음(/i/)의 F1 값
 * @param f2i 첫 번째 모음(/i/)의 F2 값
 * @param f1a 두 번째 모음(/a/)의 F1 값
 * @param f2a 두 번째 모음(/a/)의 F2 값
 * @param f1u 세 번째 모음(/u/)의 F1 값
 * @param f2u 세 번째 모음(/u/)의 F2 값
 * @returns VSA 값 (계산 불가 시 null)
 */
export function calculateVSA(
  f1i: number | null | undefined,
  f2i: number | null | undefined,
  f1a: number | null | undefined,
  f2a: number | null | undefined,
  f1u: number | null | undefined,
  f2u: number | null | undefined
): number | null {
  // 모든 값이 유효한지 확인
  if (
    f1i == null || f2i == null ||
    f1a == null || f2a == null ||
    f1u == null || f2u == null ||
    !Number.isFinite(f1i) || !Number.isFinite(f2i) ||
    !Number.isFinite(f1a) || !Number.isFinite(f2a) ||
    !Number.isFinite(f1u) || !Number.isFinite(f2u)
  ) {
    return null;
  }

  // VSA 공식: |(F1i(F2a-F2u) + F1a(F2u-F2i) + F1u(F2i-F2a))| / 2
  const vsa = Math.abs(
    (f1i * (f2a - f2u)) +
    (f1a * (f2u - f2i)) +
    (f1u * (f2i - f2a))
  ) / 2;

  return vsa;
}

const DetailedEvaluationItems: React.FC<DetailedEvaluationItemsProps> = ({
  praatData,
  praatLoading = false,
}) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // URL 파라미터에서 세션 정보 가져오기
  const sessionIdParam = searchParams.get("sessionId");
  const typeParam = searchParams.get("type");
  const itemIndexParam = searchParams.get("itemIndex");
  const dateParam = searchParams.get("date"); // result-detail에서 온 경우 날짜 파라미터

  // VSA 계산 (현재 API에는 단일 f1, f2만 있으므로 임시로 null 반환)
  // TODO: 백엔드에서 3개 모음(/i/, /a/, /u/) 각각의 F1, F2를 제공하면 수정 필요
  const vsa = useMemo(() => {
    if (!praatData) return null;
    
    // 현재는 단일 f1, f2만 있으므로 VSA 계산 불가
    // 백엔드에서 3개 모음의 데이터를 제공하면 아래처럼 사용:
    // return calculateVSA(
    //   praatData.f1i, praatData.f2i,
    //   praatData.f1a, praatData.f2a,
    //   praatData.f1u, praatData.f2u
    // );
    
    // 임시: f1, f2가 있으면 기본값으로 계산 (실제로는 3개 모음 데이터 필요)
    if (praatData.f1 != null && praatData.f2 != null) {
      // 실제로는 3개 모음 데이터가 필요하지만, 일단 f1, f2를 사용
      // TODO: 백엔드에서 3개 모음 데이터 제공 시 수정
      return null;
    }
    
    return null;
  }, [praatData]);

  // Praat 값에서 점수 계산
  const evaluationData = useMemo<DetailedEvaluationItem[]>(() => {
    const items: DetailedEvaluationItem[] = [];

    // 모음 왜곡도 (VSA 사용)
    const vsaScore = vsa != null ? Math.round(vsa) : undefined;
    items.push({
      id: "vowel_distortion",
      title: "모음 왜곡도",
      score: vsaScore ?? (praatLoading ? 0 : 50), // 로딩 중이 아니면 기본값 50
      icon: AudioWaveform,
      colorVariant: "green",
    });

    // 소리의 안정도 (CPP 사용)
    const cppScore = praatData?.cpp != null ? Math.round(praatData.cpp) : undefined;
    items.push({
      id: "cpp",
      title: "소리의 안정도",
      score: cppScore ?? (praatLoading ? 0 : 90),
      icon: Activity,
      colorVariant: "blue",
    });

    // 음성 맑음도 (HNR 사용)
    const hnrScore = praatData?.hnr != null ? Math.round(praatData.hnr) : undefined;
    items.push({
      id: "hnr",
      title: "음성 맑음도",
      score: hnrScore ?? (praatLoading ? 0 : 40),
      icon: Radio,
      colorVariant: "amber",
    });

    // 음성 건강지수 (CSID 사용)
    const csidScore = praatData?.csid != null ? Math.round(praatData.csid) : undefined;
    items.push({
      id: "csid",
      title: "음성 건강지수",
      score: csidScore ?? (praatLoading ? 0 : 34),
      icon: Heart,
      colorVariant: "amber",
    });

    return items;
  }, [praatData, vsa, praatLoading]);

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
      alert("세션 정보를 찾을 수 없습니다.");
    }
  };

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

      {/* 카드 그리드 및 버튼 */}
      <div className="self-stretch flex justify-center items-start gap-6 flex-wrap">
        {evaluationData.map((item) => (
          <DetailedEvaluationItemCard key={item.id} item={item} />
        ))}
        
        {/* 자세히 보기 버튼 */}
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


