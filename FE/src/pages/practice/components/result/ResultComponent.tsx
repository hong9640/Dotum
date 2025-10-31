import React from "react";
import ResultVideoDisplay from "./ResultVideoDisplay";
import FeedbackCard from "./FeedbackCard";

interface ResultComponentProps {
  userVideoUrl?: string;
  onNext?: () => void;
  hasNext?: boolean;
}

const ResultComponent: React.FC<ResultComponentProps> = ({
  userVideoUrl,
  onNext,
  hasNext
}) => {
  return (
    <>
      <ResultVideoDisplay userVideoUrl={userVideoUrl} />
      <FeedbackCard 
        onNext={onNext}
        hasNext={hasNext}
      />
    </>
  );
};

export default ResultComponent;
