interface WordChipProps {
  word: string; // "word_123" 또는 "sentence_456" 형식
  className?: string;
}

export function WordChip({ word, className = '' }: WordChipProps) {
  // word_id 또는 sentence_id 추출 (임시로 ID만 표시)
  const extractId = (wordStr: string): string => {
    const parts = wordStr.split('_');
    if (parts.length >= 2) {
      return parts[1]; // ID 부분만 반환
    }
    return wordStr; // 파싱 실패 시 원본 반환
  };

  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium
        bg-gray-100 text-gray-700 border border-gray-200
        hover:bg-gray-200 transition-colors duration-200
        ${className}
      `}
    >
      ID: {extractId(word)}
    </span>
  );
}
