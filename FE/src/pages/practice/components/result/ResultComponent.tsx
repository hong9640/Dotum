import React from "react";
import ResultVideoDisplay from "./ResultVideoDisplay";
import FeedbackCard from "./FeedbackCard";

interface ResultComponentProps {
  onViewAllResults: () => void;
}

const ResultComponent: React.FC<ResultComponentProps> = ({
  onViewAllResults
}) => {
  return (
    <>
      <ResultVideoDisplay />
      <FeedbackCard onViewAllResults={onViewAllResults} />
    </>
  );
};

export default ResultComponent;
