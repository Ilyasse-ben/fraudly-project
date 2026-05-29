import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  ExamResponse,
  ExamAttemptResponse,
  StartAttemptRequest,
  SubmitAttemptRequest,
} from '../models/assessment.model';

@Injectable({ providedIn: 'root' })
export class AssessmentService {
  private readonly baseUrl = `${environment.apiUrl}/exams`;

  constructor(private http: HttpClient) {}

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
}
