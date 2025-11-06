import React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AudioWaveform, Activity, Radio, Heart, ListChecks, ArrowRight } from "lucide-react";
import DetailedEvaluationItemCard, { type DetailedEvaluationItem } from "./DetailedEvaluationItemCard";
import { Button } from "@/components/ui/button";

const evaluationData: DetailedEvaluationItem[] = [
  { id: "vowel_distortion", title: "모음 왜곡도", score: 50, icon: AudioWaveform, colorVariant: "green" },
  { id: "cpp", title: "소리의 안정도", score: 90, icon: Activity, colorVariant: "blue" },
  { id: "hnr", title: "음성 맑음도", score: 40, icon: Radio, colorVariant: "amber" },
  { id: "csid", title: "음성 건강지수", score: 34, icon: Heart, colorVariant: "amber" },
];

const DetailedEvaluationItems: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // URL 파라미터에서 세션 정보 가져오기
  const sessionIdParam = searchParams.get("sessionId");
  const typeParam = searchParams.get("type");
  const itemIndexParam = searchParams.get("itemIndex");
  const dateParam = searchParams.get("date"); // result-detail에서 온 경우 날짜 파라미터

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


