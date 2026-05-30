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
    private cdr: ChangeDetectorRef // Inject the Change Detector
  ) {}

  ngOnInit(): void {
    this.isTeacher = this.authService.isProfessor();
    this.loadCourses();
  }

  loadCourses(): void {
    this.loading = true;
    this.error = '';

    this.learningService.getAllCourses().subscribe({
      next: (data) => {
        this.courses = data || [];
        this.loading = false;

        // Force Angular to update the HTML immediately
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('API Error:', err);
        this.error = 'Failed to load courses. Please check if the backend is running.';
        this.loading = false;

        // Force Angular to show the error message
        this.cdr.detectChanges();
      }
    });
  }
}
