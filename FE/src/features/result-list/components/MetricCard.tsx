import React from 'react';

interface MetricCardProps {
  title: string;
  value: number | null;
  unit?: string;
}

// 지표별 설정 정보
const metricConfig: Record<string, {
  lowerIsBetter: boolean;
  normalThreshold?: number;
  maxValue?: number;
  description: string;
}> = {
  'Jitter': {
    lowerIsBetter: true,
    normalThreshold: 0.005, // 0.5%
    maxValue: 0.02,
    description: '작을수록 발성이 더 안정적입니다.'
  },
  'Shimmer': {
    lowerIsBetter: true,
    normalThreshold: 0.05, // 0.5 dB 또는 5% 기준
    maxValue: 0.1,
    description: '작을수록 소리 크기가 더 고르고 깨끗합니다.'
  },
  'NHR': {
    lowerIsBetter: true,
    normalThreshold: 0.02, // 매우 엄격한 기준
    maxValue: 0.1, // 0.1 이내 기준
    description: '작을수록 잡음이 적고 음성이 맑습니다.'
  },
  'HNR': {
    lowerIsBetter: false,
    normalThreshold: 14, // 14 dB 이상 정상
    maxValue: 30,
    description: '클수록 음성이 더욱 맑게 들립니다.'
  },
  'CPP': {
    lowerIsBetter: false,
    normalThreshold: 6,
    maxValue: 15,
    description: '클수록 음성이 더 맑게 인지됩니다.'
  },
  'CSID': {
    lowerIsBetter: true,
    normalThreshold: 20,
    maxValue: 50,
    description: '값이 낮을수록 정상에 가깝습니다.'
  },
  'max_f0': {
    lowerIsBetter: false,
    maxValue: 500,
    description: '최대 기저 주파수입니다.'
  },
  'min_f0': {
    lowerIsBetter: false,
    maxValue: 300,
    description: '최소 기저 주파수입니다.'
  },
  'LH_ratio_mean_db': {
    lowerIsBetter: false,
    maxValue: 20,
    description: '저주파 대비 고주파 비율의 평균값입니다.'
  },
  'LH_ratio_sd_db': {
    lowerIsBetter: true,
    maxValue: 10,
    description: '저주파 대비 고주파 비율의 변동성입니다.'
  }
};

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  unit = '%'
}) => {
  const config = metricConfig[title] || {
    lowerIsBetter: false,
    maxValue: 100,
    description: ''
  };

  return (
    <div className="w-full p-3 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start gap-1.5 shadow-sm">
      {/* 제목 */}
      <div className="w-full inline-flex justify-start items-start">
        <div className="justify-center text-gray-900 text-base font-medium leading-6">
          {title}
        </div>
      </div>
      
      {/* 값 표시 */}
      <div className="w-full inline-flex justify-start items-baseline gap-1">
        <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
          {value !== null ? value.toFixed(3) : '0.000'}
        </div>
        <div className="justify-center text-gray-500 text-sm font-normal leading-6">
          {unit}
        </div>
      </div>

      {/* 설명 */}
      {config.description && (
        <div className="w-full">
          <div className="text-gray-900 text-base font-normal leading-6">
            {config.description}
          </div>
        </div>
      )}
    </div>
  );
};

export default MetricCard;

