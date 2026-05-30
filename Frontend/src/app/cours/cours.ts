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
  courseId = '';
  isTeacher = false;

  constructor(
    private route: ActivatedRoute,
    private learningService: LearningService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.courseId = this.route.snapshot.paramMap.get('courseId') ?? '';
    this.isTeacher = this.authService.isProfessor();

    this.loadCourse();
  }

  loadCourse(): void {
    this.loading = true;
    this.error = '';

    // Uses the GET /api/learning/courses/{id} endpoint
    this.learningService.getCourseById(this.courseId).subscribe({
      next: (data) => {
        this.course = data;
        // Ensure chapters are sorted by order index if they exist
        if (this.course.chapitres) {
          this.course.chapitres.sort((a: any, b: any) => a.index - b.index);
        }
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load course details. Please try again.';
        this.loading = false;
      }
    });
  }

  enrollInCourse(): void {
    if (!this.course?.coursCode) return;
    this.loading = true;

    // Uses the POST /api/learning/enrolements/{coursCode} endpoint
    this.learningService.enroll(this.course.coursCode).subscribe({
      next: () => {
        this.loadCourse(); // Reload to reflect enrollment status
      },
      error: () => {
        this.error = 'Failed to enroll in the course.';
        this.loading = false;
      }
    });
  }
}
