function CalendarLegend() {
  return (
    <div className="mt-6 pt-6 border-t border-gray-200 flex items-center justify-center gap-6">
      <div className="flex items-center gap-2">
        <span className="inline-block h-3 sm:h-4 w-3 sm:w-4 rounded-full bg-emerald-400" />
        <span className="text-lg md:text-xl font-semibold text-gray-600">
          1~4세트
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="inline-block h-3 sm:h-4 w-3 sm:w-4 rounded-full bg-emerald-600" />
        <span className="text-lg md:text-xl font-semibold text-gray-600">
          5세트 이상
        </span>
      </div>
    </div>
  );
}

export default CalendarLegend;
