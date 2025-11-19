import { Card, CardContent } from '@/shared/components/ui/card';
import { Clock } from 'lucide-react';

export function EmptyState() {
  return (
    <Card className="text-center py-12">
      <CardContent>
        <div className="text-gray-500">
          <Clock className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p className="text-lg">이 날의 연습 기록이 없습니다.</p>
          <p className="text-sm mt-2">새로운 연습을 시작해보세요!</p>
        </div>
      </CardContent>
    </Card>
  );
}
