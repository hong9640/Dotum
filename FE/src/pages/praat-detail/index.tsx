import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import PatientInfoSection, { type PatientInfo } from "./components/PatientInfoSection";
import PraatMetricsSections from "./components/PraatMetricsSections";
import { getSessionItemByIndex, getSessionItemErrorMessage } from "@/api/training-session/sessionItemSearch";
import type { PraatValues } from "./types";
import type { PraatResult } from "@/api/training-session/sessionItemSearch";

/**
 * Praat 상세 페이지
 */
const PraatDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [patientInfo, setPatientInfo] = useState<PatientInfo | null>(null);
  const [praatValues, setPraatValues] = useState<PraatValues>({});

  // URL 파라미터에서 세션 정보 가져오기
  const sessionIdParam = searchParams.get("sessionId");
  const typeParam = searchParams.get("type");
  const itemIndexParam = searchParams.get("itemIndex");
  const dateParam = searchParams.get("date"); // result-detail에서 온 경우 날짜 파라미터

  // 세션 아이템 데이터 로드
  useEffect(() => {
    const loadItemData = async () => {
      if (!sessionIdParam || !itemIndexParam) {
        setError("세션 정보가 없습니다. 결과 페이지에서 다시 시작해주세요.");
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        const sessionId = Number(sessionIdParam);
        const itemIndex = Number(itemIndexParam);

        if (isNaN(sessionId) || isNaN(itemIndex)) {
          setError("세션 ID 또는 아이템 인덱스가 유효하지 않습니다.");
          setIsLoading(false);
          return;
        }

        console.log("Praat 상세 데이터 로드 시작:", { sessionId, itemIndex });

        // 세션 아이템 상세 조회 API 호출
        const itemDetailData = await getSessionItemByIndex(sessionId, itemIndex);

        console.log("Praat 상세 데이터 로드 성공:", itemDetailData);

        // 환자 정보 설정
        const word = itemDetailData.word || itemDetailData.sentence || "";
        const analyzedAt = new Date().toLocaleString("ko-KR", {
          year: "numeric",
          month: "long",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        });

        setPatientInfo({
          analyzedAt,
          word,
        });

        // Praat 데이터 변환
        const praat: PraatResult | null | undefined = itemDetailData.praat;
        if (praat) {
          setPraatValues({
            cpp: praat.cpp,
            csid: praat.csid,
            hnr: praat.hnr,
            nhr: praat.nhr,
            jitter_local: praat.jitter_local,
            shimmer_local: praat.shimmer_local,
            f0: praat.f0,
            max_f0: praat.max_f0,
            min_f0: praat.min_f0,
            // API에서 제공되지 않는 필드들은 undefined로 유지
            // 추후 API에 추가되면 여기서 매핑
            lh_ratio_mean_db: undefined,
            lh_ratio_sd_db: undefined,
            intensity: undefined,
            f1: undefined,
            f2: undefined,
          });
        } else {
          // Praat 데이터가 없으면 빈 객체로 설정 (모든 값이 0으로 표시됨)
          setPraatValues({});
        }

        setIsLoading(false);
      } catch (err: any) {
        console.error("Praat 상세 데이터 로드 실패:", err);
        const errorMessage = getSessionItemErrorMessage(err);
        setError(errorMessage);
        setIsLoading(false);
      }
    };

    loadItemData();
  }, [sessionIdParam, itemIndexParam]);

  // 이전 페이지로 돌아가기
  const handleBack = () => {
    if (sessionIdParam && typeParam) {
      // result-detail 페이지로 돌아가기
      let detailUrl = `/result-detail?sessionId=${sessionIdParam}&type=${typeParam}&itemIndex=${itemIndexParam}`;
      if (dateParam) {
        detailUrl += `&date=${dateParam}`;
      }
      navigate(detailUrl);
    } else {
      navigate("/result-list");
    }
  };

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Praat 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">오류 발생</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={handleBack}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="self-stretch pt-7 pb-10 flex flex-col justify-start items-center bg-slate-50 min-h-screen">
      {/* 메인 콘텐츠 영역 */}
      <div className="p-4 md:p-8 flex flex-col justify-start items-center gap-8 w-full max-w-[1152px] mx-auto">
        {/* 환자 정보 */}
        {patientInfo && <PatientInfoSection info={patientInfo} />}

        {/* Praat 지표 섹션들 */}
        <PraatMetricsSections values={praatValues} />

        {/* 하단 버튼 */}
        <div className="border-t mt-8 pt-8 pb-10 flex items-center justify-center w-full">
          <Button
            variant="default"
            className="h-auto min-h-10 px-6 py-4 rounded-xl text-white text-3xl font-semibold bg-green-500 hover:bg-green-600"
            onClick={handleBack}
          >
            <ChevronLeft className="mr-2 h-8 w-8" />
            이전으로
          </Button>
        </div>
      </div>
    </div>
  );
};

export default PraatDetailPage;

