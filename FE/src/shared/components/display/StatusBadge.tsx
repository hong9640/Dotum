import React from 'react';

/**
 * StatusBadge 통합 컴포넌트
 * voice-training과 praat-detail의 두 가지 사용 패턴을 지원합니다.
 */

/**
 * 간단한 상태 배지 Props (voice-training 스타일)
 */
interface SimpleStatusBadgeProps {
  variant?: 'simple';
  label: string;
  active: boolean;
}

/**
 * 규칙 기반 상태 배지 Props (praat-detail 스타일)
 */
type StatusBadgeRule = "gt" | "lt" | "between";

interface RuleBasedStatusBadgeProps {
  variant: 'rule-based';
  rule: StatusBadgeRule;
  value: number;
  a?: number;
  b?: number;
  normalText?: string;
}

type StatusBadgeProps = SimpleStatusBadgeProps | RuleBasedStatusBadgeProps;

/**
 * 간단한 상태 배지 (voice-training 스타일)
 */
const SimpleStatusBadge: React.FC<SimpleStatusBadgeProps> = ({ label, active }) => {
  return (
    <div 
      className={`px-4 py-2 rounded-lg text-base font-semibold transition-colors ${
        active 
          ? 'bg-red-500/10 text-red-600 border-2 border-red-200' 
          : 'bg-slate-100 text-slate-600 border-2 border-slate-200'
      }`}
    >
      <div className="flex items-center gap-2">
        {active && (
          <span className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        )}
        {label}
      </div>
    </div>
  );
};

/**
 * 규칙 기반 상태 배지 (praat-detail 스타일)
 */
const RuleBasedStatusBadge: React.FC<RuleBasedStatusBadgeProps> = ({ 
  rule, 
  value, 
  a, 
  b, 
  normalText 
}) => {
  // 정상 범위가 "0"이면 배지를 표시하지 않음 (기준을 모를 때)
  if (normalText === "0" || normalText === undefined) {
    return null;
  }

  let ok = false;

  if (rule === "gt" && typeof a === "number") ok = value > a;
  if (rule === "lt" && typeof a === "number") ok = value < a;
  if (
    rule === "between" &&
    typeof a === "number" &&
    typeof b === "number"
  ) {
    ok = value >= a && value <= b;
  }

  const cls = ok
    ? "bg-green-50 text-green-600"
    : "bg-red-50 text-red-600";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${cls}`}
    >
      {ok ? "정상" : "주의"}
    </span>
  );
};

/**
 * StatusBadge 통합 컴포넌트
 * 순수 프레젠테이션 컴포넌트 - props로만 데이터를 받습니다.
 */
const StatusBadge: React.FC<StatusBadgeProps> = (props) => {
  if (props.variant === 'rule-based') {
    return <RuleBasedStatusBadge {...props} />;
  }
  
  // 기본값은 simple variant
  return <SimpleStatusBadge {...props} />;
};

export default StatusBadge;
export type { StatusBadgeProps };
export type { StatusBadgeRule };

/**
 * 규칙 기반 상태 배지 계산 함수 (praat-detail에서 사용)
 * @deprecated 이 함수는 StatusBadge 컴포넌트를 직접 사용하는 것을 권장합니다.
 */
export function statusBadgeByRule(
  rule: StatusBadgeRule,
  value: number,
  a?: number,
  b?: number,
  normalText?: string
): React.ReactNode {
  return (
    <RuleBasedStatusBadge
      variant="rule-based"
      rule={rule}
      value={value}
      a={a}
      b={b}
      normalText={normalText}
    />
  );
}

/**
 * 값이 없으면 0으로 변환하는 유틸 함수
 */
export const nz = (v: number | null | undefined) => v ?? 0;

/**
 * 정상 범위 텍스트 생성 함수
 */
export function getNormalRangeText(
  rule: StatusBadgeRule,
  a?: number,
  b?: number,
  unit?: string
): string {
  const unitStr = unit ? ` ${unit}` : "";
  
  if (rule === "gt" && typeof a === "number") {
    return `> ${a}${unitStr}`;
  }
  if (rule === "lt" && typeof a === "number") {
    return `< ${a}${unitStr}`;
  }
  if (rule === "between" && typeof a === "number" && typeof b === "number") {
    return `${a} ~ ${b}${unitStr}`;
  }
  
  return "0"; // 기본값 (정상 기준을 모를 때)
}

