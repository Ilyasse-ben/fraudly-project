import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  ExamResponse,
  ExamAttemptResponse,
  StartAttemptRequest,
  SubmitAttemptRequest,
  BackendAiGenerationRequest,
  ExamConfigRequest,
  OpenAnswerItem,
  UpdateQuestionRequest,
} from '../models/assessment.model';

@Injectable({ providedIn: 'root' })
export class AssessmentService {
  private readonly baseUrl = `${environment.apiUrl}/exams`;

  constructor(private http: HttpClient) {}

  // Generates a new exam via AI service
  generateExam(request: BackendAiGenerationRequest): Observable<ExamResponse> {
    return this.http.post<ExamResponse>(`${this.baseUrl}/generate`, request);
  }

  createExam(request: ExamConfigRequest): Observable<ExamResponse> {
    return this.http.post<ExamResponse>(`${this.baseUrl}/generate`, request);
  }

  getExamsByProfessor(professorId: string): Observable<ExamResponse[]> {
    return this.http.get<ExamResponse[]>(`${this.baseUrl}/professor/${professorId}`);
  }

  getExam(examId: string): Observable<ExamResponse> {
    return this.http.get<ExamResponse>(`${this.baseUrl}/${examId}`);
  }

  startAttempt(request: StartAttemptRequest): Observable<ExamAttemptResponse> {
    return this.http.post<ExamAttemptResponse>(`${this.baseUrl}/attempts/start`, request);
  }

  submitAttempt(request: SubmitAttemptRequest): Observable<ExamAttemptResponse> {
    return this.http.post<ExamAttemptResponse>(`${this.baseUrl}/attempts/submit`, request);
  }

  getExamsByCourse(courseId: string): Observable<ExamResponse[]> {
    return this.http.get<ExamResponse[]>(`${this.baseUrl}/course/${courseId}`);
  }

  validateExam(examId: string): Observable<ExamResponse> {
    return this.http.put<ExamResponse>(`${this.baseUrl}/${examId}/validate`, {});
  }

  publishExam(examId: string): Observable<ExamResponse> {
    return this.http.put<ExamResponse>(`${this.baseUrl}/${examId}/publish`, {});
  }

  getAttemptsByExam(examId: string): Observable<ExamAttemptResponse[]> {
    return this.http.get<ExamAttemptResponse[]>(`${this.baseUrl}/attempts/exam/${examId}`);
  }

  triggerCorrection(examId: string): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/${examId}/correction`, {});
  }

  getOpenAnswers(examId: string): Observable<OpenAnswerItem[]> {
    return this.http.get<OpenAnswerItem[]>(`${this.baseUrl}/${examId}/open-answers`);
  }

  updateAnswerScore(answerId: string, pointsAwarded: number, professorId: string): Observable<void> {
    const params = new HttpParams()
      .set('pointsAwarded', pointsAwarded.toString())
      .set('professorId', professorId);
    return this.http.patch<void>(`${this.baseUrl}/answers/${answerId}/score`, null, { params });
  }

  getAttempt(attemptId: string): Observable<ExamAttemptResponse> {
    return this.http.get<ExamAttemptResponse>(`${this.baseUrl}/attempts/${attemptId}`);
  }

  getAttemptsByStudent(studentId: string): Observable<ExamAttemptResponse[]> {
    return this.http.get<ExamAttemptResponse[]>(`${this.baseUrl}/attempts/student/${studentId}`);
  }

  updateQuestion(questionId: string, request: UpdateQuestionRequest, professorId: string): Observable<ExamResponse> {
    const params = new HttpParams().set('professorId', professorId);
    return this.http.put<ExamResponse>(`${this.baseUrl}/questions/${questionId}`, request, { params });
  }

  deleteQuestion(questionId: string, examId: string): Observable<ExamResponse> {
    const params = new HttpParams().set('examId', examId);
    return this.http.delete<ExamResponse>(`${this.baseUrl}/questions/${questionId}`, { params });
  }
}
