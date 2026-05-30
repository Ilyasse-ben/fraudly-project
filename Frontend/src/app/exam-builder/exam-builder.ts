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
      course_id: ['', Validators.required],
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

    this.loading = true;
    this.error = null;

    const request: BackendAiGenerationRequest = {
      ...this.builderForm.value,
      chapter_ids: [] // Future: Link to actual chapter selection UI
    };

    this.assessmentService.generateExam(request).subscribe({
      next: (exam) => {
        this.loading = false;
        this.router.navigate(['/listexemen']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.message || 'Failed to generate exam';
      }
    });
  }
}
