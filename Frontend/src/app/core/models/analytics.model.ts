// Maps to the JSON response from getStudentProfile
export interface StudentProfile {
  studentId: string;
  courseId: string;
  completedChapters: string[];
  scores: { [topic: string]: number };
  weakTopics: string[];
  interactionsCount: number;
  lastInteractionAt: string | null;
}

// Maps to the Map<String, Object> from getCourseTopicStats
export interface TopicStats {
  topic: string;
  totalQuestions: number;
}
export interface StudentGrade {
  studentId: string;
  studentName: string;
  cc1: number;
  cc2: number;
  exam: number;
  average: number;
  status: string;
}

export interface DashboardStats {
  totalStudents: number;
  activeCourses: number;
  classAverage: number;
  examsCompleted: number;
}
