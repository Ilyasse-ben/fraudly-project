import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { LearningService } from '../service/learning.service';
import { AuthService } from '../core/services/auth.service';
import { Cours } from '../models/learning.model';

@Component({
  selector: 'app-allcours',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './allcours.html',
  styleUrl: './allcours.css',
})
export class Allcours implements OnInit {
  courses: Cours[] = [];
  loading = true;
  error = '';
  isTeacher = false;

  constructor(
    private learningService: LearningService,
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.isTeacher = this.authService.isProfessor();
    const userId = this.extractUserIdFromToken();

    if (!userId) {
      this.loading = false;
      this.error = 'Could not identify user. Please log in again.';
      return;
    }

    const request$ = this.isTeacher
      ? this.learningService.getCoursesByProfessor(userId)
      : this.learningService.getEnrolledCourses(userId);

    request$.subscribe({
      next: (courses) => {
        this.courses = courses;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Failed to load courses. Please try again.';
        this.loading = false;
        this.cdr.detectChanges();
      },
    });
  }

  navigateToChapters(courseId: string): void {
    this.router.navigate(['/chapitre', courseId]);
  }

  private extractUserIdFromToken(): string | null {
    const token = localStorage.getItem('fraudly_access_token');
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1])) as Record<string, unknown>;
      return (payload['userId'] ?? payload['sub'] ?? null) as string | null;
    } catch {
      return null;
    }
  }
}
