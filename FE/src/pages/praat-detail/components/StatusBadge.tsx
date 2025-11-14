import React from "react";

type MaybeNum = number | null | undefined;

export type StatusBadgeRule = "gt" | "lt" | "between";

/**
 * 상태 배지 계산 함수 (정상/주의)
 * 정상 범위가 "0"인 경우(기준을 모를 때)는 배지를 표시하지 않음
 */
export function statusBadgeByRule(
  rule: StatusBadgeRule,
  value: number,
  a?: number,
  b?: number,
  normalText?: string
): React.ReactNode {
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
}

/**
 * 값이 없으면 0으로 변환하는 유틸 함수
 */
export const nz = (v: MaybeNum) => v ?? 0;

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

