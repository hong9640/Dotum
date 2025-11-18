import React from 'react';
import { ArrowDown, ArrowUp } from 'lucide-react';

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
    normalThreshold: 0.005,
    maxValue: 0.02,
    description: '작을수록 발성이 더 안정적입니다. (정상 ≤ 0.005)'
  },
  'Shimmer': {
    lowerIsBetter: true,
    normalThreshold: 0.025,
    maxValue: 0.1,
    description: '작을수록 소리 크기가 더 고르고 깨끗합니다. (정상 ≤ 0.025)'
  },
  'NHR': {
    lowerIsBetter: true,
    normalThreshold: 0.02,
    maxValue: 0.1,
    description: '작을수록 잡음이 적고 맑게 들립니다. (정상 ≤ 0.02)'
  },
  'HNR': {
    lowerIsBetter: false,
    normalThreshold: 15,
    maxValue: 30,
    description: '클수록 음성이 더 맑게 들립니다. (정상 ≥ 15)'
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
    description: '최대 주파수 값입니다.'
  },
  'min_f0': {
    lowerIsBetter: false,
    maxValue: 300,
    description: '최소 주파수 값입니다.'
  },
  'LH_ratio_mean_db': {
    lowerIsBetter: false,
    maxValue: 20,
    description: '저주파 대비 고주파 비율(평균)입니다.'
  },
  'LH_ratio_sd_db': {
    lowerIsBetter: true,
    maxValue: 10,
    description: '저주파 대비 고주파 비율(표준편차)입니다.'
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

  // Progress bar 계산
  const progressPercentage = value !== null && config.maxValue
    ? Math.min((value / config.maxValue) * 100, 100)
    : 0;

  return (
    <div className="w-full min-w-[280px] p-5 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start gap-3">
      {/* 제목 */}
      <div className="w-full inline-flex justify-start items-start">
        <div className="justify-center text-gray-900 text-lg font-semibold leading-6">
          {title}
        </div>
      </div>
      
      {/* 값 표시 */}
      <div className="w-full inline-flex justify-start items-baseline gap-1">
        <div className="justify-center text-gray-900 text-3xl font-bold leading-10">
          {value !== null ? value.toFixed(3) : '0.000'}
        </div>
        <div className="justify-center text-gray-500 text-base font-normal leading-6">
          {unit}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full flex flex-col gap-2">
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div 
            className="h-full bg-green-600 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        
        {/* 낮음/높음 표시 */}
        <div className="w-full flex justify-between items-center text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <ArrowDown className="w-3 h-3 text-red-500" />
            <span>낮음</span>
          </div>
          <div className="flex items-center gap-1">
            <span>높음</span>
            <ArrowUp className="w-3 h-3 text-red-500" />
          </div>
        </div>
      </div>

      {/* 설명 */}
      {config.description && (
        <div className="w-full text-sm text-gray-600 leading-relaxed">
          {config.description}
        </div>
      )}
    </div>
  );
};

export default MetricCard;

