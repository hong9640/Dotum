import React from 'react';
import { Music } from 'lucide-react';

interface AudioPlayerProps {
  src: string | null;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ src }) => {
  if (!src) return null;

  return (
    <div className="mt-6 p-4 bg-slate-50 rounded-xl border-2 border-slate-200">
      <div className="flex items-center gap-2 mb-3">
        <Music className="w-5 h-5 text-slate-600" />
        <p className="text-base text-slate-700 font-semibold">녹음된 오디오</p>
      </div>
      <audio 
        controls 
        src={src} 
        className="w-full"
        style={{ height: '48px' }}
      />
    </div>
  );
};

export default AudioPlayer;

