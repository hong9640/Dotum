import React from "react";
import PraatSectionCard from "./PraatSectionCard";
import PraatMetricTile from "./PraatMetricTile";
import { statusBadgeByRule, nz } from "./StatusBadge";
import type { PraatValues } from "../types";

export type PraatMetricsSectionsProps = {
  values: PraatValues;
};

/**
 * Praat 지표 섹션들 컴포넌트
 */
const PraatMetricsSections: React.FC<PraatMetricsSectionsProps> = ({
  values,
}) => {
  return (
    <>
      {/* 켑스트럼/복합 */}
      <PraatSectionCard
        title="켑스트럼/복합 중증도 지표"
        titleIconClass="w-4 h-4 bg-amber-500"
        className="w-full"
      >
        <div className="flex flex-nowrap gap-6">
          <PraatMetricTile
            title="CPP (Cepstral Peak Prominence)"
            value={values.cpp}
            unit="dB"
            normalText="0"
            status={statusBadgeByRule("gt", nz(values.cpp), 15)}
            className="flex-1"
          />
          <PraatMetricTile
            title="CSID (Cepstral Spectral Index)"
            value={values.csid}
            normalText="0"
            status={statusBadgeByRule("lt", nz(values.csid), 3.0)}
            className="flex-1"
          />
        </div>
      </PraatSectionCard>

      {/* 조화성/잡음·스펙트럼 */}
      <PraatSectionCard
        title="조화성/잡음·스펙트럼 지표"
        titleIconClass="w-4 h-4 bg-teal-500"
        className="w-full"
      >
        <div className="flex flex-col gap-6">
          {/* 첫 번째 줄: HNR, NHR */}
          <div className="flex flex-nowrap gap-6">
            <PraatMetricTile
              title="HNR (Harmonics-to-Noise Ratio)"
              value={values.hnr}
              unit="dB"
              normalText="0"
              status={statusBadgeByRule("gt", nz(values.hnr), 15)}
              className="flex-1"
            />
            <PraatMetricTile
              title="NHR (Noise-to-Harmonics Ratio)"
              value={values.nhr}
              normalText="0"
              status={statusBadgeByRule("lt", nz(values.nhr), 0.05)}
              className="flex-1"
            />
          </div>
          {/* 두 번째 줄: LH_ratio_mean_db, LH_ratio_sd_db, Intensity */}
          <div className="flex flex-nowrap gap-6">
            <PraatMetricTile
              title="LH_ratio_mean_db"
              value={values.lh_ratio_mean_db}
              unit="dB"
              normalText="0"
              status={statusBadgeByRule(
                "between",
                nz(values.lh_ratio_mean_db),
                -15,
                -8
              )}
              className="flex-1"
            />
            <PraatMetricTile
              title="LH_ratio_sd_db"
              value={values.lh_ratio_sd_db}
              unit="dB"
              normalText="0"
              status={statusBadgeByRule("lt", nz(values.lh_ratio_sd_db), 3.0)}
              className="flex-1"
            />
            <PraatMetricTile
              title="Intensity"
              value={values.intensity}
              unit="dB"
              normalText="0"
              status={statusBadgeByRule(
                "between",
                nz(values.intensity),
                60,
                80
              )}
              className="flex-1"
            />
          </div>
        </div>
      </PraatSectionCard>

      {/* 퍼터베이션 */}
      <PraatSectionCard
        title="주기-대-주기 변동(퍼터베이션) 지표"
        titleIconClass="w-4 h-4 bg-rose-500"
        className="w-full"
      >
        <div className="flex flex-nowrap gap-6">
          <PraatMetricTile
            title="Jitter Local (%)"
            value={values.jitter_local}
            unit="%"
            normalText="0"
            status={statusBadgeByRule("lt", nz(values.jitter_local), 0.02)}
            className="flex-1"
          />
          <PraatMetricTile
            title="Shimmer Local (%)"
            value={values.shimmer_local}
            unit="%"
            normalText="0"
            status={statusBadgeByRule("lt", nz(values.shimmer_local), 0.04)}
            className="flex-1"
          />
        </div>
      </PraatSectionCard>

      {/* 기본 주파수 */}
      <PraatSectionCard
        title="기본 주파수 지표"
        titleIconClass="w-4 h-4 bg-violet-500"
        className="w-full"
      >
        <div className="flex flex-wrap gap-4 sm:gap-6">
          <PraatMetricTile
            title="F0 (기본주파수)"
            value={values.f0}
            unit="Hz"
            normalText="0"
            status={statusBadgeByRule("between", nz(values.f0), 150, 250)}
            className="w-full sm:w-[calc(33.333%-0.67rem)] lg:w-80"
          />
          <PraatMetricTile
            title="Max F0 (최대주파수)"
            value={values.max_f0}
            unit="Hz"
            normalText="0"
            status={statusBadgeByRule(
              "between",
              nz(values.max_f0),
              180,
              300
            )}
            className="w-full sm:w-[calc(33.333%-0.67rem)] lg:w-80"
          />
          <PraatMetricTile
            title="Min F0 (최소주파수)"
            value={values.min_f0}
            unit="Hz"
            normalText="0"
            status={statusBadgeByRule(
              "between",
              nz(values.min_f0),
              120,
              200
            )}
            className="w-full sm:w-[calc(33.333%-0.67rem)] lg:w-80"
          />
        </div>
      </PraatSectionCard>

      {/* 포먼트 */}
      <PraatSectionCard
        title="조음/공명(포먼트) 지표"
        titleIconClass="w-4 h-4 bg-indigo-500"
        className="w-full"
      >
        <div className="flex flex-nowrap gap-6">
          <PraatMetricTile
            title="F1 (첫번째 포먼트)"
            value={values.f1}
            unit="Hz"
            normalText="0"
            status={statusBadgeByRule("between", nz(values.f1), 600, 900)}
            className="flex-1"
          />
          <PraatMetricTile
            title="F2 (두번째 포먼트)"
            value={values.f2}
            unit="Hz"
            normalText="0"
            status={statusBadgeByRule(
              "between",
              nz(values.f2),
              1000,
              1500
            )}
            className="flex-1"
          />
        </div>
      </PraatSectionCard>
    </>
  );
};

export default PraatMetricsSections;

