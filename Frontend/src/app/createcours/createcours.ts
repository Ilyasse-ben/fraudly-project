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
      coursCode:   ['', Validators.required],
    });
  }

  ngOnInit(): void {}

  onSubmit(): void {
    if (this.courseForm.invalid) return;

    const profId = this.extractUserIdFromToken();
    if (!profId) {
      this.error = 'Could not identify user. Please log in again.';
      return;
    }

    this.loading = true;
    this.error = null;

    this.learningService.createCourse({
      ...this.courseForm.value,
      profId,
    }).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/Allcours']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.message ?? err?.message ?? 'Failed to create course. Please try again.';
        this.cdr.detectChanges();
      },
    });
  }

  cancel(): void {
    this.router.navigate(['/Allcours']);
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
