import type { CalendarCellData } from "../utils/calendarCell";

interface CalendarCellProps {
  cellData: CalendarCellData;
  inMonth: boolean;
  onDateClick?: (date: string) => void;
}

function CalendarCell({ cellData, inMonth, onDateClick }: CalendarCellProps) {
  const handleDateClick = () => {
    if (onDateClick && inMonth) {
      onDateClick(cellData.iso);
    }
  };

  return (
    <div
      className={cellData.containerClass}
      onClick={handleDateClick}
    >
      <div className="w-full flex items-center justify-center sm:justify-start relative">
        <span
          className={`font-semibold text-lg sm:text-base md:text-lg ${inMonth ? cellData.numClass : "text-gray-300"
            }`}>
          {cellData.day}
        </span>
        {cellData.setCnt > 0 && (
          <span className={`sm:hidden absolute top-0.5 right-0 h-1.5 w-1.5 rounded-full ${cellData.badgeColor}`} />
        )}
      </div>

      <div className="w-full flex-1 flex items-center justify-center">
        <div
          className={`hidden sm:flex justify-center w-full px-2 py-1.5 rounded-2xl text-center items-center h-8 md:h-9 ${
            cellData.setCnt > 0 ? cellData.badgeClass : "invisible"
          }`}
        >
          <span className="flex lg:hidden text-[16px] font-semibold">
            {cellData.setCnt}회
          </span>
          <span className="hidden lg:flex text-[16px] font-semibold">
            {cellData.setCnt}회 연습
          </span>
        </div>
      </div>
    </div>
  );
}

export default CalendarCell;

