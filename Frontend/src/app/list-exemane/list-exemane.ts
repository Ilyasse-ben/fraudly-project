import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { DatePipe, CommonModule } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { AssessmentService } from '../service/assessment.service';
import { AuthService } from '../core/services/auth.service';
import { ExamResponse, Difficulty } from '../models/assessment.model';

@Component({
  selector: 'app-list-exemane',
  standalone: true,
  imports: [RouterLink, DatePipe, CommonModule],
  templateUrl: './list-exemane.html',
  styleUrl: './list-exemane.css',
})
export class ListExemane implements OnInit {
  exams: ExamResponse[] = [];
  loading = true;
  error = '';
  isTeacher = false;
  isStudent = false;
  private actionLoadingIds = new Set<string>();

  constructor(
    private assessmentService: AssessmentService,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.isTeacher = this.authService.isProfessor();
    this.isStudent = this.authService.isStudent();

    const courseId = this.route.snapshot.queryParamMap.get('courseId');

    if (courseId) {
      this.assessmentService.getExamsByCourse(courseId).subscribe({
        next: (exams) => {
          this.exams = exams;
          this.loading = false;
          this.cdr.detectChanges();
        },
        error: () => {
          this.loading = false;
          this.error = 'Failed to load exams. Please try again.';
          this.cdr.detectChanges();
        },
      });
      return;
    }

    if (this.isTeacher) {
      const professorId = this.extractUserIdFromToken();
      if (!professorId) {
        this.loading = false;
        this.error = 'Could not identify user. Please log in again.';
        return;
      }
      this.assessmentService.getExamsByProfessor(professorId).subscribe({
        next: (exams) => {
          this.exams = exams;
          this.loading = false;
          this.cdr.detectChanges();
        },
        error: () => {
          this.loading = false;
          this.error = 'Failed to load exams. Please try again.';
          this.cdr.detectChanges();
        },
      });
      return;
    }

    // ROLE_STUDENT: load all published exams by course (default COURSE1_ID)
    const defaultCourseId = '66666666-6666-6666-6666-666666666666';
    this.assessmentService.getExamsByCourse(defaultCourseId).subscribe({
      next: (exams) => {
        this.exams = exams.filter(e => e.status === 'PUBLISHED');
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.error = 'Failed to load exams. Please try again.';
        this.cdr.detectChanges();
      },
    });
  }

  isActionLoading(examId: string): boolean {
    return this.actionLoadingIds.has(examId);
  }

  validateExam(examId: string): void {
    this.actionLoadingIds.add(examId);
    this.assessmentService.validateExam(examId).subscribe({
      next: (updated) => {
        this.exams = this.exams.map(e => e.id === examId ? { ...e, status: updated.status } : e);
        this.actionLoadingIds.delete(examId);
      },
      error: () => {
        this.actionLoadingIds.delete(examId);
      },
    });
  }

  publishExam(examId: string): void {
    this.actionLoadingIds.add(examId);
    this.assessmentService.publishExam(examId).subscribe({
      next: (updated) => {
        this.exams = this.exams.map(e => e.id === examId ? { ...e, status: updated.status } : e);
        this.actionLoadingIds.delete(examId);
      },
      error: () => {
        this.actionLoadingIds.delete(examId);
      },
    });
  }

  get pendingCount(): number {
    return this.exams.filter((e) => e.status === 'PUBLISHED').length;
  }

  statusBadgeClass(status: string): string {
    const map: Record<string, string> = {
      DRAFT:     'bg-yellow-50 text-yellow-700',
      REVIEWED:  'bg-blue-50 text-blue-700',
      PUBLISHED: 'bg-green-50 text-green-700',
      ARCHIVED:  'bg-slate-100 text-slate-500',
      GRADING:   'bg-purple-50 text-purple-700',
    };
    return map[status] ?? 'bg-slate-100 text-slate-600';
  }

  badgeClass(difficulty: Difficulty): string {
    const map: Record<Difficulty, string> = {
      EASY:      'bg-green-50 text-green-600',
      MEDIUM:    'bg-blue-50 text-blue-600',
      HARD:      'bg-purple-50 text-purple-600',
      VERY_HARD: 'bg-orange-50 text-orange-600',
    };
    return map[difficulty] ?? 'bg-slate-50 text-slate-600';
  }

  private extractUserIdFromToken(): string | null {
    const token = localStorage.getItem('fraudly_access_token');
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload['userId'] ?? payload['sub'] ?? null;
    } catch {
      return null;
    }
  }
}
