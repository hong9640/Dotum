interface WordChipProps {
  word: string; // 실제 단어 또는 문장 텍스트
  isSentence?: boolean; // 문장인지 여부
  className?: string;
}

export function WordChip({ word, isSentence = false, className = '' }: WordChipProps) {
  // 문장인 경우 첫 번째 단어만 추출하고 "..." 추가
  let displayText: string;
  
  if (!word) {
    displayText = '';
  } else {
    // isSentence가 true이거나, word에 공백이 있으면 문장으로 간주
    const hasSpace = word.trim().indexOf(' ') > 0;
    const shouldTruncate = isSentence || hasSpace;
    
    if (shouldTruncate) {
      // 공백으로 분리하여 첫 번째 단어 추출
      const trimmedWord = word.trim();
      const firstSpaceIndex = trimmedWord.indexOf(' ');
      if (firstSpaceIndex > 0) {
        displayText = `${trimmedWord.substring(0, firstSpaceIndex)}...`;
      } else {
        // 공백이 없으면 첫 3글자만 표시
        displayText = `${trimmedWord.substring(0, Math.min(3, trimmedWord.length))}...`;
      }
    } else {
      displayText = word;
    }
  }

  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium
        bg-gray-100 text-gray-700 border border-gray-200
        hover:bg-gray-200 transition-colors duration-200
        ${className}
      `}
    >
      {displayText}
    </span>
  );
}
