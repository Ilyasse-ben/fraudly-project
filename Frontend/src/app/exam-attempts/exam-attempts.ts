import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { AssessmentService } from '../service/assessment.service';
import { ExamAttemptResponse, AttemptStatus } from '../models/assessment.model';

@Component({
  selector: 'app-exam-attempts',
  standalone: true,
  imports: [DatePipe, RouterLink],
  templateUrl: './exam-attempts.html',
})
export class ExamAttemptsComponent implements OnInit {
  examId = '';
  attempts: ExamAttemptResponse[] = [];
  loading = true;
  error = '';
  isGrading = false;
  gradingError = '';

  constructor(
    private route: ActivatedRoute,
    private assessmentService: AssessmentService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.examId = this.route.snapshot.paramMap.get('examId') ?? '';
    this.loadAttempts();
  }

  triggerAiGrading(): void {
    this.isGrading = true;
    this.gradingError = '';
    this.assessmentService.triggerCorrection(this.examId).subscribe({
      next: () => {
        this.isGrading = false;
        this.loadAttempts();
      },
      error: () => {
        this.isGrading = false;
        this.gradingError = 'AI grading failed. Please try again.';
      },
    });
  }

  scoreDisplay(attempt: ExamAttemptResponse): string {
    if (attempt.score === null) return '—';
    return `${attempt.score} / ${attempt.maxScore ?? '?'}`;
  }

  statusClass(status: AttemptStatus): string {
    const map: Record<AttemptStatus, string> = {
      STARTED: 'bg-blue-50 text-blue-600',
      IN_PROGRESS: 'bg-yellow-50 text-yellow-600',
      SUBMITTED: 'bg-slate-100 text-slate-600',
      GRADED: 'bg-green-50 text-green-600',
    };
    return map[status] ?? 'bg-slate-100 text-slate-600';
  }

  private loadAttempts(): void {
    this.loading = true;
    this.error = '';
    this.assessmentService.getAttemptsByExam(this.examId).subscribe({
      next: (attempts) => {
        this.attempts = attempts;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.error = 'Failed to load attempts.';
        this.cdr.detectChanges();
      },
    });
  }
}
