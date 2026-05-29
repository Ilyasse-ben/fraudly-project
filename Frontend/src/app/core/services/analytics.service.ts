import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { StudentProfile, TopicStats, StudentGrade } from '../models/analytics.model';

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private baseUrl = `${environment.apiUrl}/analytics`;

  constructor(private http: HttpClient) {}

  getStudentProfile(studentId: string, courseId?: string): Observable<StudentProfile> {
    let params = new HttpParams();
    if (courseId) {
      params = params.set('courseId', courseId);
    }
    return this.http.get<StudentProfile>(`${this.baseUrl}/students/${studentId}/profile`, { params });
  }

  getWeakTopics(studentId: string, courseId: string, minCount: number = 3): Observable<string[]> {
    const params = new HttpParams()
      .set('courseId', courseId)
      .set('minCount', minCount.toString());

    return this.http.get<string[]>(`${this.baseUrl}/students/${studentId}/weak-topics`, { params });
  }

  getCourseTopicStats(courseId: string): Observable<TopicStats[]> {
    return this.http.get<TopicStats[]>(`${this.baseUrl}/courses/${courseId}/topics`);
  }

  // Add to analytics.service.ts
  getStudentsGrades(courseId: string): Observable<StudentGrade[]> {
    // You will need to add this @GetMapping to your LearningAnalyticsController
    return this.http.get<StudentGrade[]>(`${this.baseUrl}/courses/${courseId}/grades`);
  }
}
