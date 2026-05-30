import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AssessmentService } from '../service/assessment.service';
import { ExamResponse, QuestionType } from '../models/assessment.model';

interface QuestionForm {
  id: string;
  orderIndex: number;
  type: QuestionType;
  questionText: string;
  correctAnswer: string;
  explanation: string;
  points: number;
  reason: string;
}

@Component({
  selector: 'app-question-editor',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './question-editor.html',
})
export class QuestionEditorComponent implements OnInit {
  examId = '';
  exam: ExamResponse | null = null;
  questionForms: QuestionForm[] = [];
  loading = true;
  error = '';
  savingSet = new Set<string>();
  deletingSet = new Set<string>();
  professorId: string | null = null;

  constructor(
    private route: ActivatedRoute,
    private assessmentService: AssessmentService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.examId = this.route.snapshot.paramMap.get('examId') ?? '';
    this.professorId = this.extractUserIdFromToken();
    this.loadExam();
  }

  saveQuestion(questionId: string): void {
    if (!this.professorId) return;
    const form = this.questionForms.find(f => f.id === questionId);
    if (!form) return;

    this.savingSet.add(questionId);
    this.assessmentService.updateQuestion(
      questionId,
      {
        questionText: form.questionText,
        correctAnswer: form.correctAnswer,
        explanation: form.explanation,
        points: form.points,
        reason: form.reason,
      },
      this.professorId,
    ).subscribe({
      next: () => this.savingSet.delete(questionId),
      error: () => this.savingSet.delete(questionId),
    });
  }

  deleteQuestion(questionId: string): void {
    this.deletingSet.add(questionId);
    this.assessmentService.deleteQuestion(questionId, this.examId).subscribe({
      next: (updatedExam) => {
        this.deletingSet.delete(questionId);
        this.questionForms = this.questionForms.filter(f => f.id !== questionId);
        this.exam = updatedExam;
      },
      error: () => this.deletingSet.delete(questionId),
    });
  }

  isSaving(questionId: string): boolean {
    return this.savingSet.has(questionId);
  }

  isDeleting(questionId: string): boolean {
    return this.deletingSet.has(questionId);
  }

  private loadExam(): void {
    this.assessmentService.getExam(this.examId).subscribe({
      next: (exam) => {
        this.exam = exam;
        this.questionForms = (exam.questions ?? []).map(q => ({
          id: q.id,
          orderIndex: q.orderIndex,
          type: q.type,
          questionText: q.questionText,
          correctAnswer: q.correctAnswer ?? '',
          explanation: q.explanation ?? '',
          points: q.points,
          reason: '',
        }));
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Failed to load exam.';
        this.loading = false;
        this.cdr.detectChanges();
      },
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
