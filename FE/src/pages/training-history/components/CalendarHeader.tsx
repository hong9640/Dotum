import { ChevronLeft, ChevronRight, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

interface CalendarHeaderProps {
  year: number;
  monthLabel: string;
  onPrev: () => void;
  onNext: () => void;
  onYearChange: (year: number) => void;
}

function CalendarHeader({ 
  year, 
  monthLabel, 
  onPrev, 
  onNext, 
  onYearChange 
}: CalendarHeaderProps) {
  // 현재 연도 기준으로 이전 2년, 현재, 다음 2년 (총 5개)
  const YEARS = Array.from({ length: 5 }, (_, i) => year - 2 + i);

  return (
    <div className="flex items-center justify-center">
      <div className="flex items-center gap-2">
        {/* 이전 달 화살표 */}
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={onPrev} 
          aria-label="이전 달"
          className="h-10 w-10 text-gray-600 hover:text-gray-900"
        >
          <ChevronLeft className="h-5 w-5" />
        </Button>

        {/* 연도와 월을 하나로 묶기 */}
        <div className="flex items-center gap-2">
          {/* 연도 선택 */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="outline" 
                className="rounded-xl h-12 px-4 text-xl font-semibold flex items-center gap-2"
              >
                {year}년
                <ChevronDown className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="center" className="w-40">
              <DropdownMenuLabel className="text-center text-base font-semibold">연도 선택</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {YEARS.map((y) => (
                <DropdownMenuItem 
                  key={y} 
                  onClick={() => onYearChange(y)} 
                  className={`cursor-pointer text-center justify-center text-xl font-semibold py-2.5 rounded-lg transition-colors ${
                    y === year 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'hover:bg-gray-100'
                  }`}
                >
                  {y}년
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* 월 표기 */}
          <div className="text-xl md:text-2xl font-semibold text-gray-900">
            {monthLabel}
          </div>
        </div>

        {/* 다음 달 화살표 */}
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={onNext} 
          aria-label="다음 달"
          className="h-10 w-10 text-gray-600 hover:text-gray-900"
        >
          <ChevronRight className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
}

export default CalendarHeader;

