import { ChevronLeft, ChevronRight, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

// 연 선택 범위(필요 시 조정)
const YEARS = Array.from({ length: 7 }, (_, i) => 2023 + i); // 2023~2029

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
                className="rounded-xl h-12 px-4 text-2xl font-semibold flex items-center gap-2"
              >
                {year}년
                <ChevronDown className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="center" className="w-48">
              <DropdownMenuLabel className="text-center">연도 선택</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {YEARS.map((y) => (
                <DropdownMenuItem 
                  key={y} 
                  onClick={() => onYearChange(y)} 
                  className="cursor-pointer text-center justify-center hover:bg-gray-100"
                >
                  {y}년
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* 월 표기 */}
          <div className="text-2xl md:text-3xl font-semibold text-gray-900">
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

