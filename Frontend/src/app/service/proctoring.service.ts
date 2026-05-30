import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  FraudEventRequest,
  FraudEventResponse,
  ProctoringSessionResponse,
  StartSessionRequest,
} from '../models/proctoring.model';

@Injectable({ providedIn: 'root' })
export class ProctoringService {
  private readonly baseUrl = `${environment.apiUrl}/proctoring`;
  private readonly SESSION_KEY = 'fraudly_proctoring_session_id';

  constructor(private http: HttpClient) {}

  startSession(
    studentId: string,
    examId: string,
    attemptId: string
  ): Observable<ProctoringSessionResponse> {
    const request: StartSessionRequest = {
      studentId,
      examId,
      attemptId,
      deviceFingerprint: navigator.userAgent,
    };
    return this.http
      .post<ProctoringSessionResponse>(`${this.baseUrl}/sessions/start`, request)
      .pipe(tap((res) => sessionStorage.setItem(this.SESSION_KEY, res.id)));
  }

  endSession(sessionId: string): Observable<ProctoringSessionResponse> {
    return this.http.put<ProctoringSessionResponse>(
      `${this.baseUrl}/sessions/${sessionId}/end`,
      {}
    );
  }

  reportEvent(request: FraudEventRequest): Observable<unknown> {
    return this.http.post(`${this.baseUrl}/events`, request);
  }

  getFlaggedSessions(): Observable<ProctoringSessionResponse[]> {
    return this.http.get<ProctoringSessionResponse[]>(`${this.baseUrl}/sessions/flagged`);
  }

  getSessionEvents(sessionId: string): Observable<FraudEventResponse[]> {
    return this.http.get<FraudEventResponse[]>(`${this.baseUrl}/events/session/${sessionId}`);
  }
}
