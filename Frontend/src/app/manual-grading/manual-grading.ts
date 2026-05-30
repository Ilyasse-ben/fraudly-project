import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { AssessmentService } from '../service/assessment.service';
import { OpenAnswerItem } from '../models/assessment.model';

@Component({
  selector: 'app-manual-grading',
  standalone: true,
  imports: [],
  templateUrl: './manual-grading.html',
})
export class ManualGradingComponent implements OnInit {
  examId = '';
  professorId: string | null = null;
  answers: OpenAnswerItem[] = [];
  scoreInputs = new Map<string, number>();
  updatingSet = new Set<string>();
  loading = true;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private assessmentService: AssessmentService,
  ) {}

  ngOnInit(): void {
    this.examId = this.route.snapshot.paramMap.get('examId') ?? '';
    this.professorId = this.extractUserIdFromToken();

    this.assessmentService.getOpenAnswers(this.examId).subscribe({
      next: (answers) => {
        this.answers = answers;
        answers.forEach(a => this.scoreInputs.set(a.answerId, a.pointsAwarded ?? 0));
        this.loading = false;
      },
      error: () => {
        this.error = 'Failed to load open answers.';
        this.loading = false;
      },
    });
  }

  onScoreInput(answerId: string, value: string): void {
    this.scoreInputs.set(answerId, parseFloat(value) || 0);
  }

  updateScore(answerId: string, maxPoints: number): void {
    const score = this.scoreInputs.get(answerId) ?? 0;
    if (score < 0 || score > maxPoints || !this.professorId) return;

    this.updatingSet.add(answerId);
    this.assessmentService.updateAnswerScore(answerId, score, this.professorId).subscribe({
      next: () => {
        const answer = this.answers.find(a => a.answerId === answerId);
        if (answer) {
          answer.pointsAwarded = score;
          answer.isGraded = true;
        }
        this.updatingSet.delete(answerId);
      },
      error: () => {
        this.updatingSet.delete(answerId);
      },
    });
  }

  isUpdating(answerId: string): boolean {
    return this.updatingSet.has(answerId);
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
