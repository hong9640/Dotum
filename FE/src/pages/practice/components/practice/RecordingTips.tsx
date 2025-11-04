import React from "react";
import { Info, Check } from "lucide-react";

const RecordingTips: React.FC = () => {
  return (
    <div className="flex justify-center">
      <div className="w-full max-w-[896px]">
        <div className="p-6 rounded-xl border-2 border-green-100 bg-green-50">
          <div className="flex items-center gap-2 mb-4">
            <Info className="size-7 text-green-700" />
            <h3 className="text-green-700 text-xl sm:text-2xl font-semibold">녹화 팁</h3>
          </div>

          <ul className="space-y-3">
            <li className="flex items-start gap-3">
              <Check className="mt-1 size-4 text-green-700" />
              <p className="text-green-700 text-base sm:text-lg font-semibold">조용한 환경에서 녹화해주세요</p>
            </li>
            <li className="flex items-start gap-3">
              <Check className="mt-1 size-4 text-green-700" />
              <p className="text-green-700 text-base sm:text-lg font-semibold">카메라와 적절한 거리를 유지해주세요</p>
            </li>
            <li className="flex items-start gap-3">
              <Check className="mt-1 size-4 text-green-700" />
              <p className="text-green-700 text-base sm:text-lg font-semibold">정면을 바라보고 또박또박 발음해주세요</p>
            </li>
            <li className="flex items-start gap-3">
              <Check className="mt-1 size-4 text-green-700" />
              <p className="text-green-700 text-base sm:text-lg font-semibold">밝은 조명 아래에서 촬영하면 더 좋습니다</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RecordingTips;
