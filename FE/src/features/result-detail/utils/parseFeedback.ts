/**
 * GPT 피드백을 파싱하여 구조화된 데이터로 변환하는 유틸리티
 */

export interface ParsedFeedback {
  overallSummary: string;
  evaluations: Array<{
    id: number;
    title: string;
    content: string;
  }>;
  improvements: string[];
}

/**
 * GPT 피드백 텍스트를 파싱하여 구조화된 데이터로 변환
 * 
 * @param feedbackText GPT로부터 받은 피드백 텍스트
 * @returns 파싱된 피드백 데이터
 */
export function parseFeedback(feedbackText: string): ParsedFeedback {
  // 기본값 설정
  const defaultResult: ParsedFeedback = {
    overallSummary: '피드백 정보를 분석 중입니다.',
    evaluations: [],
    improvements: []
  };

  if (!feedbackText || feedbackText.trim().length === 0) {
    return defaultResult;
  }

  try {
    // 한 줄 요약 추출 (인사말 부분에서 핵심 메시지 추출)
    let overallSummary = '';
    const greetingMatch = feedbackText.match(/오늘도.*?🌟/s);
    if (greetingMatch) {
      // 이모지와 감사 인사 제거하고 핵심 메시지만 추출
      overallSummary = greetingMatch[0]
        .replace(/🌟/g, '')
        .replace(/오늘도 연습해주셔서 정말 고마워요\./g, '')
        .trim();
    } else {
      // 인사말이 없으면 첫 문단을 요약으로 사용
      const firstParagraph = feedbackText.split('\n\n')[0] || feedbackText.split('\n')[0];
      overallSummary = firstParagraph.replace(/🌟/g, '').trim();
    }

    // 잘하고 계신 부분 파싱
    const evaluations: Array<{ id: number; title: string; content: string }> = [];
    const goodPartsMatch = feedbackText.match(/잘하고 계신 부분\s*([\s\S]*?)(?=💭|🌱|$)/);
    
    if (goodPartsMatch) {
      const goodPartsText = goodPartsMatch[1];
      // 줄 단위로 분리
      const lines = goodPartsText.split('\n').filter(line => line.trim().length > 0);
      
      lines.forEach((line) => {
        const trimmedLine = line.trim();
        // 숫자)로 시작하는 줄 찾기 (예: "1) '빨간색' 발음에 대한...")
        const numberedMatch = trimmedLine.match(/^(\d+)\)\s*(.+)/);
        if (numberedMatch) {
          const itemNumber = parseInt(numberedMatch[1], 10);
          const content = numberedMatch[2].trim();
          
          // '단어' 또는 "단어" 패턴에서 단어 추출
          const wordMatch = content.match(/['"]([^'"]+)['"]/);
          const word = wordMatch ? wordMatch[1] : '';
          
          // 단어가 있으면 제목으로 사용, 없으면 "항목 N" 형식
          const title = word ? `${word} 발음` : `항목 ${itemNumber}`;
          
          // 설명은 전체 내용 사용 (단어 부분 포함)
          evaluations.push({
            id: itemNumber,
            title: title,
            content: content
          });
        }
      });
    }

    // 조금만 더 신경 쓰면 좋을 부분 파싱
    const improvements: string[] = [];
    const improvementMatch = feedbackText.match(/💭\s*조금만 더 신경 쓰면 좋을 부분\s*([\s\S]*?)(?=🌱|조금씩|$)/);
    if (improvementMatch) {
      const improvementText = improvementMatch[1].trim();
      // "하지만 괜찮아요!" 같은 구분 문구 제거
      const cleanedText = improvementText.replace(/하지만 괜찮아요[!.]?\s*/g, '').trim();
      
      if (cleanedText.length > 0) {
        improvements.push(cleanedText);
      }
    }

    // 집에서 함께 해볼 연습 파싱
    const practiceMatch = feedbackText.match(/🌱\s*집에서 함께 해볼 연습\s*([\s\S]*?)(?=조금씩|$)/);
    if (practiceMatch) {
      const practiceText = practiceMatch[1];
      // 줄 단위로 분리하고 - 로 시작하는 항목들 추출
      const lines = practiceText.split('\n').filter(line => line.trim().length > 0);
      
      lines.forEach((line) => {
        const trimmedLine = line.trim();
        // - 로 시작하는 줄 찾기
        if (trimmedLine.startsWith('-')) {
          const item = trimmedLine.replace(/^-\s*/, '').trim();
          if (item.length > 0) {
            improvements.push(item);
          }
        }
      });
    }

    // 평가 항목이 없으면 기본 항목 생성
    if (evaluations.length === 0) {
      evaluations.push({
        id: 1,
        title: '전체 평가',
        content: '피드백 정보를 분석 중입니다.'
      });
    }

    // 개선 포인트가 없으면 기본 메시지
    if (improvements.length === 0) {
      improvements.push('계속 연습하시면 더 좋아질 거예요.');
    }

    return {
      overallSummary: overallSummary || '피드백 정보를 분석 중입니다.',
      evaluations,
      improvements
    };
  } catch (error) {
    console.error('피드백 파싱 오류:', error);
    return defaultResult;
  }
}

