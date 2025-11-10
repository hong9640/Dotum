import React from 'react';
import { Square } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface RecordToggleProps {
  isRecording: boolean;
  onToggle: () => void;
  disabled?: boolean;
}

const RecordToggle: React.FC<RecordToggleProps> = ({ isRecording, onToggle, disabled = false }) => {
  return (
    <>
      {!isRecording ? (
        <Button 
          size="lg" 
          className="px-5 sm:px-8 py-4 sm:py-6 text-lg sm:text-xl bg-red-500 hover:bg-red-600 flex items-center gap-3" 
          onClick={onToggle}
          disabled={disabled}
        >
          <div className="relative">
            <div className="sm:size-6 size-5 border-2 border-white rounded-full"></div>
            <div className="sm:size-3 size-2 bg-white rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"></div>
          </div>
          녹음 시작
        </Button>
      ) : (
        <Button 
          size="lg" 
          className="px-5 sm:px-8 py-4 sm:py-6 text-lg sm:text-xl bg-slate-800 hover:bg-slate-900 flex items-center gap-3" 
          onClick={onToggle}
          disabled={disabled}
        >
          <Square className="sm:size-6 size-5 text-white" strokeWidth={2} />
          녹음 종료
        </Button>
      )}
    </>
  );
};

export default RecordToggle;

