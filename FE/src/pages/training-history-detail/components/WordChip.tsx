
interface WordChipProps {
  word: string;
  className?: string;
}

export function WordChip({ word, className = '' }: WordChipProps) {
  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium
        bg-gray-100 text-gray-700 border border-gray-200
        hover:bg-gray-200 transition-colors duration-200
        ${className}
      `}
    >
      {word}
    </span>
  );
}
