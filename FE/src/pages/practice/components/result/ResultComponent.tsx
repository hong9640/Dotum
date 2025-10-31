import React from "react";
import ResultVideoDisplay from "./ResultVideoDisplay";
import FeedbackCard from "./FeedbackCard";

interface ResultComponentProps {
  onViewAllResults: () => void;
  userVideoUrl?: string;
  onNext?: () => void;
  hasNext?: boolean;
}

const ResultComponent: React.FC<ResultComponentProps> = ({
  onViewAllResults,
  userVideoUrl,
  onNext,
  hasNext
}) => {
  return (
    <>
      <ResultVideoDisplay userVideoUrl={userVideoUrl} />
      <FeedbackCard 
        onViewAllResults={onViewAllResults}
        onNext={onNext}
        hasNext={hasNext}
      />
    </>
  );
};

export default ResultComponent;
