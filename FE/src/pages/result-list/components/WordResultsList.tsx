import React from 'react';
import { ListChecks } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import WordResultItem from "./WordResultItem";
import type { WordResult } from "../types";

interface WordResultsListProps {
  results: WordResult[];
  onDetailClick: (result: WordResult) => void;
}

const WordResultsList: React.FC<WordResultsListProps> = ({ results, onDetailClick }) => {
  return (
    <div className="w-full max-w-[1220px] pb-6 bg-white rounded-2xl outline outline-[3px] outline-offset-[-3px] outline-green-200 flex flex-col justify-start items-center gap-6 md:gap-12 overflow-hidden">
      <div className="self-stretch p-6 bg-gradient-to-r from-green-50 via-green-300 to-yellow-100 border-b-[0.80px] border-blue-100 inline-flex justify-start items-center gap-4">
        <ListChecks className="w-6 h-6 md:w-7 md:h-7 text-green-600" strokeWidth={3} />
        <div className="flex-1 inline-flex flex-col justify-center items-start gap-2.5">
          <div className="justify-start">
            <span className="text-slate-700 text-2xl md:text-3xl font-semibold leading-tight md:leading-9">
              단어별 결과
            </span>
            <span className="text-slate-500 text-lg md:text-2xl font-semibold leading-snug md:leading-8">
              {" "}(총 {results.length}개)
            </span>
          </div>
        </div>
      </div>
      
      {/* 결과 아이템들 */}
      <div className="self-stretch px-4 md:px-6 flex flex-col justify-start items-center gap-4">
        {results.map((result) => (
          <WordResultItem
            key={result.id}
            result={result}
            onDetailClick={onDetailClick}
          />
        ))}
      </div>
    </div>
  );
};

export default WordResultsList;
