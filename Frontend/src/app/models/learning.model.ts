export interface Chapter {
  id: string;
  title: string;
  index: number;
  dateChapitre: string | null;
  courseId: string;
}

export interface Cours {
  id: string;
  title: string;
  description: string;
  category: string;
  coursCode: string;
  profId: string;
  courseDate: string | null;
  chapters?: Chapter[];
}

export interface Enrollment {
  id: string;
  studentId: string;
  courseId: string;
  enrollmentDate: string | null;
}

export interface CreateCoursRequest {
  title: string;
  description: string;
  category: string;
  coursCode: string;
  profId: string;
}

export interface CreateChapterRequest {
  title: string;
  index: number;
  courseId: string;
}

export interface EnrollRequest {
  studentId: string;
  courseId: string;
}
