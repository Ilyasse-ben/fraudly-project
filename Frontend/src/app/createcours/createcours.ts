import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { LearningService } from '../service/learning.service';
import { AuthService } from '../core/services/auth.service';

@Component({
  selector: 'app-createcours',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './createcours.html',
  styleUrl: './createcours.css',
})
export class Createcours implements OnInit {
  courseForm: FormGroup;
  loading = false;
  error: string | null = null;

  constructor(
    private fb: FormBuilder,
    private learningService: LearningService,
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {
    this.courseForm = this.fb.group({
      title:       ['', Validators.required],
      description: ['', Validators.required],
      category:    ['', Validators.required],
    });
  }

  ngOnInit(): void {}

  onSubmit(): void {
    if (this.courseForm.invalid) return;

    this.loading = true;
    this.error = null;

    // Uses POST /api/learning/courses
    this.learningService.createCourse({
      ...this.courseForm.value
    }).subscribe({
      next: (createdCourse) => {
        this.loading = false;
        // Navigate directly to the newly created course details
        this.router.navigate(['/cours', createdCourse.id]);
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.message ?? 'Failed to create course.';
        this.cdr.detectChanges();
      },
    });
  }

  cancel(): void {
    this.router.navigate(['/Allcours']);
  }
}
