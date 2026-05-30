import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AssessmentService } from '../service/assessment.service';
import { ExamConfigRequest } from '../models/assessment.model';

@Component({
  selector: 'app-exam-builder',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './exam-builder.html'
})
export class ExamBuilderComponent implements OnInit {
  private readonly COURSE1_ID = '66666666-6666-6666-6666-666666666666';

  builderForm: FormGroup;
  loading = false;
  error: string | null = null;

  readonly difficulties = ['EASY', 'MEDIUM', 'HARD', 'VERY_HARD'];
  readonly qcmTypes = ['QCM_SINGLE', 'QCM_MULTIPLE'];

  constructor(
    private fb: FormBuilder,
    private assessmentService: AssessmentService,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.builderForm = this.fb.group({
      title:          ['', Validators.required],
      durationMinutes:[60, [Validators.required, Validators.min(1)]],
      difficulty:     ['MEDIUM', Validators.required],
      nbQcm:          [5,  [Validators.required, Validators.min(0)]],
      qcmType:        ['QCM_SINGLE', Validators.required],
      nbTrueFalse:    [3,  [Validators.required, Validators.min(0)]],
      nbOpen:         [2,  [Validators.required, Validators.min(0)]],
      chapterIds:     [''],
    });
  }

  ngOnInit(): void {}

  onSubmit(): void {
    if (this.builderForm.invalid) return;

    const professorId = this.extractUserIdFromToken();
    const courseId = this.route.snapshot.queryParamMap.get('courseId') ?? this.COURSE1_ID;

    const raw = this.builderForm.value;
    const chapterIds: string[] = raw.chapterIds
      ? (raw.chapterIds as string).split(',').map((s: string) => s.trim()).filter((s: string) => s.length > 0)
      : [];

    const request: ExamConfigRequest = {
      title:          raw.title,
      courseId,
      professorId:    professorId ?? '',
      durationMinutes: raw.durationMinutes,
      difficulty:     raw.difficulty,
      nbQcm:          raw.nbQcm,
      qcmType:        raw.qcmType,
      nbTrueFalse:    raw.nbTrueFalse,
      nbOpen:         raw.nbOpen,
      chapterIds,
    };

    this.loading = true;
    this.error = null;

    this.assessmentService.createExam(request).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/listexemen']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.message ?? err?.message ?? 'Failed to create exam. Please try again.';
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
