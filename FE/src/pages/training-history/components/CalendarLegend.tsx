function CalendarLegend() {
  return (
    <div className="mt-6 pt-6 border-t border-gray-200 flex items-center justify-center gap-6">
      <div className="flex items-center gap-2">
        <span className="inline-block h-5 w-5 rounded-full bg-green-400" />
        <span className="text-xl md:text-2xl font-semibold text-gray-600">
          1~2세트
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="inline-block h-5 w-5 rounded-full bg-green-500" />
        <span className="text-xl md:text-2xl font-semibold text-gray-600">
          3세트 이상
        </span>
      </div>
    </div>
  );
}

export default CalendarLegend;
