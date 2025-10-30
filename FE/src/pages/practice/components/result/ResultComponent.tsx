import React from "react";
import ResultVideoDisplay from "./ResultVideoDisplay";
import FeedbackCard from "./FeedbackCard";

interface ResultComponentProps {
  onViewAllResults: () => void;
  userVideoUrl?: string;
}

const ResultComponent: React.FC<ResultComponentProps> = ({
  onViewAllResults,
  userVideoUrl
}) => {
  return (
    <>
      <ResultVideoDisplay userVideoUrl={userVideoUrl} />
      <FeedbackCard onViewAllResults={onViewAllResults} />
    </>
  );
};

export default ResultComponent;
