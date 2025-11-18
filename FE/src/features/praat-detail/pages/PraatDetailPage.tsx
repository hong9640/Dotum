import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/shared/components/ui/button";
import { ChevronLeft } from "lucide-react";
import PatientInfoSection, { type PatientInfo } from "../components/PatientInfoSection";
import PraatMetricsSections from "../components/PraatMetricsSections";
import RecordingTabs from "../components/RecordingTabs";
import PraatSectionCard from "../components/PraatSectionCard";
import { getSessionItemByIndex, getSessionItemErrorMessage } from "@/features/training-session/api/session-item-search";
import { getTrainingSession } from "@/features/training-session/api";
import type { PraatValues } from "@/features/praat-detail/types";
import { usePraat } from "@/features/praat-detail/hooks";
import { getPraatErrorMessage } from "@/features/training-session/api/praat";
// import type { PraatMetrics } from "@/features/training-session/api/praat";

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
  const [sessionType, setSessionType] = useState<string | null>(null);
  const [recordingCount, setRecordingCount] = useState(0);
  const [currentRecordingIndex, setCurrentRecordingIndex] = useState(0);
  const [compositedVideoUrl, setCompositedVideoUrl] = useState<string | null>(null);
  const [praatImageUrl, setPraatImageUrl] = useState<string | null>(null);
  const [baseItemIndex, setBaseItemIndex] = useState<number>(0); // 현재 연습의 첫 번째 itemIndex

  // URL 파라미터에서 세션 정보 가져오기
  const sessionIdParam = searchParams.get("sessionId");
  const typeParam = searchParams.get("type");
  const itemIndexParam = searchParams.get("itemIndex");
  const dateParam = searchParams.get("date"); // result-list에서 온 경우 날짜 파라미터

  // 페이지 진입 시 상단으로 스크롤
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [sessionIdParam, itemIndexParam]);

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

        // 세션 상세 정보와 아이템 상세 정보를 병렬로 조회
        const [sessionData, itemDetailData] = await Promise.all([
          getTrainingSession(sessionId),
          getSessionItemByIndex(sessionId, itemIndex),
        ]);

        // 발성연습 여부 확인 (type이 'vocal'인 경우)
        const sessionTypeLower = (sessionData.type || '').toLowerCase();
        const isVocal = sessionTypeLower === 'vocal';
        setIsVocalExercise(isVocal);
        // 세션 타입 저장 (handleBack에서 사용)
        setSessionType(sessionTypeLower);

        // 발성연습일 때 녹음 횟수 계산 (total_items / 5)
        if (isVocal && sessionData.total_items) {
          const count = Math.floor(sessionData.total_items / 5);
          setRecordingCount(count);
          // 현재 itemIndex가 속한 연습의 첫 번째 itemIndex 계산
          const n = count;
          const trainingIndex = Math.floor(itemIndex / n);
          const baseIndex = trainingIndex * n;
          setBaseItemIndex(baseIndex);
          // 현재 itemIndex에 해당하는 녹음 탭 인덱스 설정 (0부터 시작)
          const currentTabIndex = itemIndex - baseIndex;
          setCurrentRecordingIndex(currentTabIndex);
        } else {
          setBaseItemIndex(itemIndex);
        }

        // item_id 저장
        if (itemDetailData.item_id) {
          setItemId(itemDetailData.item_id);
        } else {
          console.error("item_id가 없습니다");
        }

        // composited_video_url 설정 (발성연습일 때 사용)
        if (isVocal && itemDetailData.composited_video_url) {
          setCompositedVideoUrl(itemDetailData.composited_video_url);
        }

        // Praat 데이터 설정 (아이템 상세 조회 API 응답에 포함된 praat 데이터 사용)
        // if (itemDetailData.praat) {
        //   updatePraatValues(itemDetailData.praat);
        // } else {
        //   setPraatValues({});
        //   setPraatImageUrl(null);
        // }

        // 환자 정보 설정
        let word = itemDetailData.word || itemDetailData.sentence || "";

        // 발성 연습일 때는 연습 명칭으로 표시
        if (isVocal && sessionData.total_items) {
          const vocalTrainingNames = [
            '최대 발성 지속 시간 연습 (MPT)',
            '크레셴도 연습 (점강)',
            '데크레셴도 연습 (점약)',
            '순간 강약 전환 연습',
            '연속 강약 조절 연습'
          ];
          const n = Math.floor(sessionData.total_items / 5);
          const trainingIndex = Math.floor(itemIndex / n);
          if (trainingIndex >= 0 && trainingIndex < vocalTrainingNames.length) {
            word = vocalTrainingNames[trainingIndex];
          }
        }

        const analyzedAt = new Date().toLocaleString("ko-KR", {
          year: "numeric",
          month: "long",
          day: "numeric",
        });

        setPatientInfo({
          analyzedAt,
          word,
          isVocalExercise: isVocal,
        });

        setIsLoading(false);
      } catch (err: unknown) {
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
  const { data: praatData, error: praatError } = usePraat(
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
    if (praatData) {
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

      // image_url 추출 (API 응답에 포함될 수 있음)
      const dataWithImageUrl = praatData as { image_url?: string };
      const imageUrl = dataWithImageUrl.image_url;
      if (imageUrl) {
        setPraatImageUrl(imageUrl);
      } else {
        setPraatImageUrl(null);
      }
    } else if (praatError) {
      // 에러 발생 시 빈 객체로 설정
      setPraatValues({});


      // Praat 데이터를 PraatValues로 변환하는 함수
      // const updatePraatValues = (praatData: PraatMetrics) => {
      //   setPraatValues({
      //     cpp: praatData.cpp,
      //     csid: praatData.csid,
      //     hnr: praatData.hnr,
      //     nhr: praatData.nhr,
      //     jitter_local: praatData.jitter_local,
      //     shimmer_local: praatData.shimmer_local,
      //     f0: praatData.f0,
      //     max_f0: praatData.max_f0,
      //     min_f0: praatData.min_f0,
      //     lh_ratio_mean_db: praatData.lh_ratio_mean_db,
      //     lh_ratio_sd_db: praatData.lh_ratio_sd_db,
      //     intensity: praatData.intensity_mean,
      //     f1: praatData.f1,
      //     f2: praatData.f2,
      //   });

      //   // image_url 추출 (API 응답에 포함될 수 있음)
      //   const dataWithImageUrl = praatData as { image_url?: string };
      //   const imageUrl = dataWithImageUrl.image_url;
      //   if (imageUrl) {
      //     setPraatImageUrl(imageUrl);
      //   } else {
      setPraatImageUrl(null);
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

  // };

  // 녹음 탭 선택 핸들러
  const handleRecordingSelect = async (index: number) => {
    setCurrentRecordingIndex(index);

    // 발성 연습일 때만 해당 녹음의 데이터를 다시 로드
    if (isVocalExercise && sessionIdParam) {
      try {
        const sessionId = Number(sessionIdParam);
        // 선택한 녹음의 itemIndex 계산 (baseItemIndex + index)
        const selectedItemIndex = baseItemIndex + index;

        // 해당 itemIndex의 아이템 데이터 조회
        const itemDetailData = await getSessionItemByIndex(sessionId, selectedItemIndex);

        // item_id 업데이트 (Praat API 호출에 필요)
        if (itemDetailData.item_id) {
          setItemId(itemDetailData.item_id);
        }

        // composited_video_url 업데이트
        if (itemDetailData.composited_video_url) {
          setCompositedVideoUrl(itemDetailData.composited_video_url);
        } else {
          setCompositedVideoUrl(null);
        }

        // Praat 데이터 업데이트 (아이템 상세 조회 API 응답에 포함된 praat 데이터 사용)
        // if (itemDetailData.praat) {
        //   updatePraatValues(itemDetailData.praat);
        // } else {
        //   setPraatValues({});
        //   setPraatImageUrl(null);
        // }
      } catch (err: unknown) {
        console.error("선택한 녹음 데이터 로드 실패:", err);
      }
    }
  };

  // 이전 페이지로 돌아가기
  const handleBack = () => {
    if (sessionIdParam) {
      // typeParam이 있으면 사용, 없으면 sessionType 사용
      const type = typeParam || sessionType;
      if (type) {
        // result-list 페이지로 이동
        let listUrl = `/result-list?sessionId=${sessionIdParam}&type=${type}`;
        if (dateParam) {
          listUrl += `&date=${dateParam}`;
        }
        navigate(listUrl);
      } else {
        // 타입 정보가 없으면 홈으로 이동
        navigate("/");
      }
    } else {
      // 세션 정보가 없으면 홈으로 이동
      navigate("/");
    }
  };

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">세션 정보를 불러오는 중...</p>
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
    <div className="self-stretch pt-7 pb-10 flex flex-col justify-start items-center bg-white min-h-screen">
      {/* 메인 콘텐츠 영역 */}
      <div className="p-4 md:p-8 flex flex-col justify-start items-center gap-8 w-full min-w-[320px] max-w-[1152px] mx-auto">
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

        {/* 발성연습일 때 음형 파장 비디오/이미지 표시 */}
        {isVocalExercise && (
          <PraatSectionCard
            title="음형 파장"
            titleIconClass="w-4 h-4 bg-blue-600"
            className="w-full"
          >
            <div className="w-full">
              {praatImageUrl ? (
                <img
                  src={praatImageUrl}
                  alt="음형 파장 그래프"
                  className="w-full rounded-lg"
                  style={{ maxHeight: "600px", objectFit: "contain" }}
                />
              ) : compositedVideoUrl ? (
                <video
                  src={compositedVideoUrl}
                  controls
                  className="w-full rounded-lg"
                  style={{ maxHeight: "600px" }}
                >
                  브라우저가 비디오 태그를 지원하지 않습니다.
                </video>
              ) : (
                <div className="w-full h-[600px] bg-gray-100 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
                  <div className="text-center">
                    <div className="text-gray-400 text-lg mb-2">📹</div>
                    <div className="text-gray-500 text-base">파형 그래프 영상을 불러오는 중...</div>
                  </div>
                </div>
              )}
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

