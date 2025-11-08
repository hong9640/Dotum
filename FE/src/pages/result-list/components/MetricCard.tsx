import React from 'react';

interface MetricCardProps {
  title: string;
  value: number | null;
  unit?: string;
  normalRange?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  unit = '%',
  normalRange 
}) => {
  return (
    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
      <div className="w-44 pb-2 inline-flex justify-start items-start">
        <div className="flex-1 h-7 relative">
          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">
              {title}
            </div>
          </div>
        </div>
      </div>
      <div className="w-44 h-16 flex flex-col justify-start items-start">
        <div className="self-stretch h-10 inline-flex justify-start items-center">
          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
            {value !== null ? value.toFixed(3) : '0.000'}
          </div>
          <div className="justify-center text-gray-500 text-sm font-normal leading-6">
            {unit}
          </div>
        </div>
        {normalRange && (
          <div className="self-stretch pt-1 inline-flex justify-start items-start">
            <div className="w-full h-6 flex justify-start items-center">
              <div className="justify-center text-gray-500 text-sm font-normal leading-6">
                정상 범위: {normalRange}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricCard;

