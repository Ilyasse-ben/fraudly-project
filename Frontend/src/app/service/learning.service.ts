import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  Cours,
  Chapter,
  Enrollment,
  CreateCoursRequest,
  CreateChapterRequest,
} from '../models/learning.model';

@Injectable({ providedIn: 'root' })
export class LearningService {
  // Base URLs mapped exactly to your Spring Boot RequestMappings
  private readonly baseUrl = `${environment.apiUrl}/learning`;
  private readonly resourcesUrl = `${environment.apiUrl}/resources`; // Note: This controller doesn't use the /learning prefix

  constructor(private http: HttpClient) {}

  // ==========================================
  // COURS MANAGEMENT (/api/learning/courses)
  // ==========================================

  createCourse(request: CreateCoursRequest): Observable<Cours> {
    return this.http.post<Cours>(`${this.baseUrl}/courses`, request);
  }

  getAllCourses(): Observable<Cours[]> {
    return this.http.get<Cours[]>(`${this.baseUrl}/courses`);
  }

  getCourseById(courseId: string): Observable<Cours> {
    return this.http.get<Cours>(`${this.baseUrl}/courses/${courseId}`);
  }

  updateCourse(courseId: string, request: CreateCoursRequest): Observable<Cours> {
    return this.http.put<Cours>(`${this.baseUrl}/courses/${courseId}`, request);
  }

  deleteCourse(courseId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/courses/${courseId}`);
  }

  // NOTE: These were in your original frontend but are missing from the Java code you provided.
  // Kept here with standard REST paths in case you have them in a different file.
  getCoursesByProfessor(profId: string): Observable<Cours[]> {
    return this.http.get<Cours[]>(`${this.baseUrl}/courses/prof/${profId}`);
  }

  getEnrolledCourses(studentId: string): Observable<Cours[]> {
    return this.http.get<Cours[]>(`${this.baseUrl}/courses/student/${studentId}`);
  }

  // ==========================================
  // CHAPITRE MANAGEMENT (/api/learning/chapitres)
  // ==========================================

  // FIXED: Backend requires courseId in the path
  createChapter(courseId: string, request: CreateChapterRequest): Observable<Chapter> {
    return this.http.post<Chapter>(`${this.baseUrl}/chapitres/${courseId}`, request);
  }

  getChapterById(chapterId: string): Observable<Chapter> {
    return this.http.get<Chapter>(`${this.baseUrl}/chapitres/${chapterId}`);
  }

  updateChapter(chapterId: string, request: CreateChapterRequest): Observable<Chapter> {
    return this.http.put<Chapter>(`${this.baseUrl}/chapitres/${chapterId}`, request);
  }

  deleteChapter(chapterId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/chapitres/${chapterId}`);
  }

  // NOTE: Missing from Java code provided, kept just in case.
  getChaptersByCourse(courseId: string): Observable<Chapter[]> {
    return this.http.get<Chapter[]>(`${this.baseUrl}/chapitres/course/${courseId}`);
  }

  // ==========================================
  // ENROLLMENT MANAGEMENT (/api/learning/enrolements)
  // ==========================================

  // FIXED: Backend takes coursCode in URL and gets user from JWT. No body needed.
  enroll(coursCode: string): Observable<Enrollment> {
    return this.http.post<Enrollment>(`${this.baseUrl}/enrolements/${coursCode}`, {});
  }

  // FIXED: Added missing delete endpoint from backend
  unenroll(enrolementId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/enrolements/${enrolementId}`);
  }

  // ==========================================
  // RESOURCES MANAGEMENT (/api/resources)
  // ==========================================

  // FIXED: Changed to match MultipartFile and @RequestParam needs of backend
  uploadResource(chapterId: string, file: File, type: string, lien: string): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);
    formData.append('lien', lien);

    // Notice this uses this.resourcesUrl instead of baseUrl
    return this.http.post<any>(`${this.resourcesUrl}/${chapterId}`, formData);
  }

  // ==========================================
  // AI TUTOR (/api/learning/tutor)
  // ==========================================

  askTutor(question: string, studentId: string, courseId: string): Observable<{ answer: string }> {
    const body = { question, studentId, courseId };
    return this.http.post<{ answer: string }>(`${this.baseUrl}/tutor/ask`, body);
  }
}
