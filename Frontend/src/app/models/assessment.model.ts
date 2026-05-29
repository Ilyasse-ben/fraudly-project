export type Difficulty = 'EASY' | 'MEDIUM' | 'HARD' | 'VERY_HARD';
export type ExamStatus = 'DRAFT' | 'REVIEWED' | 'PUBLISHED' | 'ARCHIVED' | 'GRADING';
export type QuestionType = 'QCM_SINGLE' | 'QCM_MULTIPLE' | 'TRUE_FALSE' | 'OPEN';
export type AttemptStatus = 'STARTED' | 'IN_PROGRESS' | 'SUBMITTED' | 'GRADED';

export interface QuestionChoiceResponse {
  id: string;
  label: string;
  text: string;
  isCorrect: boolean;
}

export interface ExamQuestionResponse {
  id: string;
  orderIndex: number;
  type: QuestionType;
  questionText: string;
  correctAnswer: string;
  explanation: string;
  points: number;
  difficulty: Difficulty;
  generatedByAi: boolean;
  editedByTeacher: boolean;
  choices: QuestionChoiceResponse[];
}

export interface ExamResponse {
  id: string;
  title: string;
  topic: string;
  difficulty: Difficulty;
  status: ExamStatus;
  version: number;
  courseId: string;
  professorId: string;
  durationMinutes: number;
  createdAt: string;
  publishedAt: string | null;
  startDate: string | null;
  endDate: string | null;
  questions?: ExamQuestionResponse[];
}

export interface StartAttemptRequest {
  studentId: string;
  examId: string;
}

export interface SubmitAnswerRequest {
  questionId: string;
  answerText: string | null;
  selectedChoiceId: string | null;
  selectedChoiceIds: string[] | null;
}

export interface SubmitAttemptRequest {
  attemptId: string;
  answers: SubmitAnswerRequest[];
}

export interface ExamAttemptResponse {
  id: string;
  examId: string;
  studentId: string;
  status: AttemptStatus;
  startedAt: string;
  submittedAt: string | null;
  score: number | null;
  maxScore: number | null;
}
