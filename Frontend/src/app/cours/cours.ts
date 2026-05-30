import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { LearningService } from '../service/learning.service';
import { AuthService } from '../core/services/auth.service';

@Component({
  selector: 'app-cours',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './cours.html',
  styleUrl: './cours.css',
})
export class Cours implements OnInit {
  course: any = null;
  loading = true;
  error = '';
  courseId: string | null = null;
  isTeacher = false;

  constructor(
    private route: ActivatedRoute,
    private learningService: LearningService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.isTeacher = this.authService.isProfessor();

    // Fix: Subscribe to paramMap so we always get the ID even if the route changes
    this.route.paramMap.subscribe(params => {
      this.courseId = params.get('courseId');
      console.log('DEBUG: Course ID retrieved from URL:', this.courseId);

      if (this.courseId) {
        this.loadCourse(this.courseId);
      } else {
        this.error = 'No Course ID found in URL.';
        this.loading = false;
      }
    });
  }

  loadCourse(id: string): void {
    this.loading = true;
    this.error = '';

    this.learningService.getCourseById(id).subscribe({
      next: (data) => {
        console.log('DEBUG: API Response for course:', data);
        this.course = data;
        if (this.course?.chapitres) {
          this.course.chapitres.sort((a: any, b: any) => a.index - b.index);
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('DEBUG: API Error:', err);
        this.error = 'Failed to load course details. Backend returned: ' + (err.status || 'Unknown Error');
        this.loading = false;
      }
    });
  }

  enrollInCourse(): void {
    if (!this.course?.coursCode) return;
    this.loading = true;

    this.learningService.enroll(this.course.coursCode).subscribe({
      next: () => {
        this.loadCourse(this.courseId!);
      },
      error: (err) => {
        console.error('Enrollment Error:', err);
        this.error = 'Failed to enroll in the course.';
        this.loading = false;
      }
    });
  }
}
