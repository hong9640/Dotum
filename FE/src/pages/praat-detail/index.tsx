import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import PatientInfoSection, { type PatientInfo } from "./components/PatientInfoSection";
import PraatMetricsSections from "./components/PraatMetricsSections";
import RecordingTabs from "./components/RecordingTabs";
import PraatSectionCard from "./components/PraatSectionCard";
import { getSessionItemByIndex, getSessionItemErrorMessage } from "@/api/training-session/sessionItemSearch";
import { getTrainingSession } from "@/api/training-session";
import { usePraat } from "@/hooks/usePraat";
import { getPraatErrorMessage } from "@/api/training-session/praat";
import type { PraatValues } from "./types";

/**
 * Praat 상세 페이지
 */
const PraatDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [patientInfo, setPatientInfo] = useState<PatientInfo | null>(null);
  const [itemId, setItemId] = useState<number | undefined>(undefined);
  const [praatValues, setPraatValues] = useState<PraatValues>({});
  const [isVocalExercise, setIsVocalExercise] = useState(false);
  const [recordingCount, setRecordingCount] = useState(0);
  const [currentRecordingIndex, setCurrentRecordingIndex] = useState(0);
  const [compositedVideoUrl, setCompositedVideoUrl] = useState<string | null>(null);

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

        // 세션 상세 정보와 아이템 상세 정보를 병렬로 조회
        const [sessionData, itemDetailData] = await Promise.all([
          getTrainingSession(sessionId),
          getSessionItemByIndex(sessionId, itemIndex),
        ]);

        console.log("Praat 상세 데이터 로드 성공:", { sessionData, itemDetailData });
        console.log("item_id:", itemDetailData.item_id);

        // 발성연습 여부 확인 (type이 'vocal'인 경우)
        const isVocal = (sessionData.type as string) === 'vocal';
        setIsVocalExercise(isVocal);

        // 발성연습일 때 녹음 횟수 계산 (total_items / 5)
        if (isVocal && sessionData.total_items) {
          const count = Math.floor(sessionData.total_items / 5);
          setRecordingCount(count);
          console.log("발성연습 녹음 횟수:", count, "(total_items:", sessionData.total_items, ")");
        }

        // item_id 저장 (Praat API 호출에 필요)
        if (itemDetailData.item_id) {
          setItemId(itemDetailData.item_id);
          console.log("✅ item_id 설정 완료:", itemDetailData.item_id);
        } else {
          console.error("❌ item_id가 없습니다!");
        }

        // composited_video_url 설정 (발성연습일 때 사용)
        if (isVocal && itemDetailData.composited_video_url) {
          setCompositedVideoUrl(itemDetailData.composited_video_url);
        }

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

  // Praat 분석 결과 조회 (폴링 포함)
  const sessionId = sessionIdParam ? Number(sessionIdParam) : undefined;
  const { data: praatData, loading: praatLoading, processing: praatProcessing, error: praatError } = usePraat(
    sessionId,
    itemId,
    {
      pollIntervalMs: 2500,
      maxPollMs: 60000,
      enabled: !!sessionId && !!itemId && !isLoading,
    }
  );

  // Praat 데이터를 PraatValues로 변환
  useEffect(() => {
    console.log("🔄 Praat 데이터 변환 체크:", { praatData, praatError });
    if (praatData) {
      console.log("✅ Praat 데이터 변환 시작:", praatData);
      setPraatValues({
        cpp: praatData.cpp,
        csid: praatData.csid,
        hnr: praatData.hnr,
        nhr: praatData.nhr,
        jitter_local: praatData.jitter_local,
        shimmer_local: praatData.shimmer_local,
        f0: praatData.f0,
        max_f0: praatData.max_f0,
        min_f0: praatData.min_f0,
        lh_ratio_mean_db: praatData.lh_ratio_mean_db,
        lh_ratio_sd_db: praatData.lh_ratio_sd_db,
        intensity: praatData.intensity_mean,
        f1: praatData.f1,
        f2: praatData.f2,
      });
    } else if (praatError) {
      // 에러 발생 시 빈 객체로 설정
      setPraatValues({});
    }
  }, [praatData, praatError]);

  // Praat 에러 처리
  useEffect(() => {
    if (praatError) {
      const errorMessage = getPraatErrorMessage(praatError);
      // 기존 에러가 없고, Praat 에러만 있는 경우에만 설정
      // (세션 아이템 로드 에러보다 Praat 에러는 덜 중요하므로)
      if (!error) {
        setError(errorMessage);
      }
    }
  }, [praatError, error]);

  // 녹음 탭 선택 핸들러
  const handleRecordingSelect = (index: number) => {
    setCurrentRecordingIndex(index);
    // TODO: 선택한 녹음에 해당하는 Praat 데이터를 다시 로드해야 할 수도 있음
    console.log("녹음 선택:", index);
  };

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
  if (isLoading || praatLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">
            {isLoading ? "세션 정보를 불러오는 중..." : praatProcessing ? "Praat 분석 중..." : "Praat 데이터를 불러오는 중..."}
          </p>
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

        {/* 발성연습일 때만 녹음 횟수 탭 표시 */}
        {isVocalExercise && recordingCount > 0 && (
          <RecordingTabs
            totalRecordings={recordingCount}
            currentRecordingIndex={currentRecordingIndex}
            onRecordingSelect={handleRecordingSelect}
          />
        )}

        {/* 발성연습일 때 음형 파장 비디오 표시 */}
        {isVocalExercise && compositedVideoUrl && (
          <PraatSectionCard
            title="음형 파장"
            titleIconClass="w-4 h-4 bg-blue-600"
            className="w-full"
          >
            <div className="w-full">
              <video
                src={compositedVideoUrl}
                controls
                className="w-full rounded-lg"
                style={{ maxHeight: "600px" }}
              >
                브라우저가 비디오 태그를 지원하지 않습니다.
              </video>
            </div>
          </PraatSectionCard>
        )}

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

