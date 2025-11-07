import React from 'react';

interface StatusBadgeProps {
  label: string;
  active: boolean;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ label, active }) => {
  return (
    <div 
      className={`px-4 py-2 rounded-lg text-base font-semibold transition-colors ${
        active 
          ? 'bg-red-500/10 text-red-600 border-2 border-red-200' 
          : 'bg-slate-100 text-slate-600 border-2 border-slate-200'
      }`}
    >
      <div className="flex items-center gap-2">
        {active && (
          <span className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        )}
        {label}
      </div>
    </div>
  );
};

export default StatusBadge;

