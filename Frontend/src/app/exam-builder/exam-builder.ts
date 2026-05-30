import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AssessmentService } from '../service/assessment.service';
import { BackendAiGenerationRequest, Difficulty } from '../models/assessment.model';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-exam-builder',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './exam-builder.html'
})
export class ExamBuilderComponent implements OnInit {
  builderForm: FormGroup;
  loading = false;
  error: string | null = null;
  difficulties: Difficulty[] = ['EASY', 'MEDIUM', 'HARD', 'VERY_HARD'];

  constructor(
    private fb: FormBuilder,
    private assessmentService: AssessmentService,
    private router: Router
  ) {
    this.builderForm = this.fb.group({
      topic: ['', Validators.required],
      difficulty: ['MEDIUM', Validators.required],
      total_questions: [10, [Validators.required, Validators.min(1)]],
      qcm_count: [5, Validators.min(0)],
      true_false_count: [3, Validators.min(0)],
      open_count: [2, Validators.min(0)],
      include_explanations: [true],
      professor_instructions: [''],
      top_k: [3]
    });
  }

  ngOnInit(): void {}

  onSubmit(): void {
    if (this.builderForm.invalid) return;

    const professorId = this.extractUserIdFromToken();

    this.loading = true;
    this.error = null;

    const request: BackendAiGenerationRequest = {
      ...this.builderForm.value,
      course_id: '66666666-6666-6666-6666-666666666666',
      chapter_ids: [],
      professor_id: professorId ?? '',
    };

    this.assessmentService.generateExam(request).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/listexemen']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.message || 'Failed to generate exam';
      }
    });
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
