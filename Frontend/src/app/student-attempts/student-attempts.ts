import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { DatePipe } from '@angular/common';
import { AssessmentService } from '../service/assessment.service';
import { ExamAttemptResponse, AttemptStatus } from '../models/assessment.model';

@Component({
  selector: 'app-student-attempts',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './student-attempts.html',
})
export class StudentAttemptsComponent implements OnInit {
  studentId = '';
  attempts: ExamAttemptResponse[] = [];
  loading = true;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private assessmentService: AssessmentService,
  ) {}

  ngOnInit(): void {
    this.studentId = this.route.snapshot.paramMap.get('studentId') ?? '';
    this.assessmentService.getAttemptsByStudent(this.studentId).subscribe({
      next: (attempts) => {
        this.attempts = attempts;
        this.loading = false;
      },
      error: () => {
        this.error = 'Failed to load attempts.';
        this.loading = false;
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
}
