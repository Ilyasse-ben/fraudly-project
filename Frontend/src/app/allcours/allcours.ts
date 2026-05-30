import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { LearningService } from '../service/learning.service';
import { AuthService } from '../core/services/auth.service';

@Component({
  selector: 'app-allcours',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './allcours.html',
  styleUrl: './allcours.css'
})
export class Allcours implements OnInit {
  courses: any[] = [];
  loading = true;
  error = '';
  isTeacher = false;

  constructor(
    private learningService: LearningService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    // Initialize role
    this.isTeacher = this.authService.isProfessor();
    this.loadCourses();
  }

  loadCourses(): void {
    this.loading = true;
    this.error = '';

    this.learningService.getAllCourses().subscribe({
      next: (data) => {
        // Ensure data is defined, default to empty array
        this.courses = Array.isArray(data) ? data : [];
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('API Error:', err);
        this.error = 'Failed to load courses. Please check your backend connection.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
