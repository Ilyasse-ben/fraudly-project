import {
  Component,
  HostListener,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AssessmentService } from '../service/assessment.service';
import { ProctoringService } from '../service/proctoring.service';
import { AuthService } from '../core/services/auth.service';
import {
  ExamAttemptResponse,
  ExamQuestionResponse,
  ExamResponse,
  SubmitAnswerRequest,
  SubmitAttemptRequest,
} from '../models/assessment.model';
import { FraudEventType } from '../models/proctoring.model';

interface AnswerState {
  textAnswer: string | null;
  selectedChoiceId: string | null;
  selectedChoiceIds: string[];
}

@Component({
  selector: 'app-examen',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './examen.html',
  styleUrl: './examen.css',
})
export class Examen implements OnInit, OnDestroy {
  exam: ExamResponse | null = null;
  attempt: ExamAttemptResponse | null = null;
  loading = true;
  error: string | null = null;
  submitted = false;
  submitting = false;
  isProfessorPreview = false;

  currentIndex = 0;
  secondsRemaining = 0;

  private sessionId: string | null = null;
  private timerInterval: ReturnType<typeof setInterval> | null = null;
  private answers = new Map<string, AnswerState>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private assessmentService: AssessmentService,
    private proctoringService: ProctoringService,
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    const examId = this.route.snapshot.paramMap.get('id');
    const userId = this.extractUserIdFromToken();
    this.isProfessorPreview = this.authService.isProfessor();

    if (!examId || !userId) {
      this.error = 'Missing exam or user information.';
      this.loading = false;
      return;
    }

    if (this.isProfessorPreview) {
      // Professor: load exam read-only, no attempt, no proctoring
      this.assessmentService.getExam(examId).subscribe({
        next: (exam) => {
          this.exam = exam;
          this.initAnswerMap(exam);
          this.loading = false;
        },
        error: () => {
          this.error = 'Failed to load the exam. Please try again.';
          this.loading = false;
        },
      });
      return;
    }

    // Student: full flow with attempt + proctoring
    this.assessmentService.getExam(examId).subscribe({
      next: (exam) => {
        this.exam = exam;
        this.initAnswerMap(exam);

        this.assessmentService.startAttempt({ studentId: userId, examId }).subscribe({
          next: (attempt) => {
            this.attempt = attempt;
            this.loading = false;
            this.startTimer(exam.durationMinutes);

            this.proctoringService.startSession(userId, examId, attempt.id).subscribe({
              next: (session) => (this.sessionId = session.id),
              error: (err) => console.error('Proctoring session failed to start', err),
            });
          },
          error: () => {
            this.error = 'Failed to start the exam attempt. Please try again.';
            this.loading = false;
          },
        });
      },
      error: () => {
        this.error = 'Failed to load the exam. Please try again.';
        this.loading = false;
      },
    });
  }

  ngOnDestroy(): void {
    if (this.timerInterval !== null) {
      clearInterval(this.timerInterval);
    }
    if (this.sessionId) {
      this.proctoringService.endSession(this.sessionId).subscribe();
    }
  }

  @HostListener('window:blur')
  onWindowBlur(): void {
    this.reportFraudEvent(FraudEventType.TAB_SWITCH, 0.9);
  }

  @HostListener('document:contextmenu', ['$event'])
  onContextMenu(event: Event): void {
    if (!this.sessionId || this.submitted) return;
    event.preventDefault();
    this.reportFraudEvent(FraudEventType.TAB_SWITCH, 0.6);
  }

  @HostListener('document:copy', ['$event'])
  onCopy(event: Event): void {
    if (!this.sessionId || this.submitted) return;
    event.preventDefault();
    this.reportFraudEvent(FraudEventType.TAB_SWITCH, 0.7);
  }

  @HostListener('document:paste', ['$event'])
  onPaste(event: Event): void {
    if (!this.sessionId || this.submitted) return;
    event.preventDefault();
    this.reportFraudEvent(FraudEventType.TAB_SWITCH, 0.7);
  }

  @HostListener('document:keydown', ['$event'])
  onKeyDown(event: KeyboardEvent): void {
    if (!this.sessionId || this.submitted) return;
    const key = event.key.toLowerCase();
    const blocked =
      key === 'f12' ||
      (event.ctrlKey && event.shiftKey && key === 'i') ||
      (event.ctrlKey && key === 'u') ||
      (event.ctrlKey && key === 'c') ||
      (event.ctrlKey && key === 'v');
    if (!blocked) return;
    event.preventDefault();
    this.reportFraudEvent(FraudEventType.TAB_SWITCH, 0.7);
  }

  get questions(): ExamQuestionResponse[] {
    return this.exam?.questions ?? [];
  }

  get currentQuestion(): ExamQuestionResponse | null {
    return this.questions[this.currentIndex] ?? null;
  }

  get timerDisplay(): string {
    const m = Math.floor(this.secondsRemaining / 60);
    const s = this.secondsRemaining % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  get timerIsWarning(): boolean {
    return this.secondsRemaining < 300;
  }

  get timerIsCritical(): boolean {
    return this.secondsRemaining < 60;
  }

  // QCM_SINGLE / TRUE_FALSE
  getSelectedChoiceId(questionId: string): string | null {
    return this.answers.get(questionId)?.selectedChoiceId ?? null;
  }

  setSelectedChoiceId(questionId: string, choiceId: string): void {
    if (this.isProfessorPreview) return;
    const state = this.answers.get(questionId);
    if (state) state.selectedChoiceId = choiceId;
  }

  // QCM_MULTIPLE
  isChoiceSelected(questionId: string, choiceId: string): boolean {
    return this.answers.get(questionId)?.selectedChoiceIds.includes(choiceId) ?? false;
  }

  toggleChoice(questionId: string, choiceId: string): void {
    if (this.isProfessorPreview) return;
    const state = this.answers.get(questionId);
    if (!state) return;
    const idx = state.selectedChoiceIds.indexOf(choiceId);
    if (idx === -1) {
      state.selectedChoiceIds.push(choiceId);
    } else {
      state.selectedChoiceIds.splice(idx, 1);
    }
  }

  // OPEN
  getTextAnswer(questionId: string): string {
    return this.answers.get(questionId)?.textAnswer ?? '';
  }

  setTextAnswer(questionId: string, value: string): void {
    if (this.isProfessorPreview) return;
    const state = this.answers.get(questionId);
    if (state) state.textAnswer = value.trim() || null;
  }

  navigate(direction: 1 | -1): void {
    const next = this.currentIndex + direction;
    if (next >= 0 && next < this.questions.length) {
      this.currentIndex = next;
    }
  }

  goBack(): void {
    this.router.navigate(['/listexemen']);
  }

  submitExam(): void {
    if (!this.attempt || this.submitting || this.isProfessorPreview) return;
    this.submitting = true;

    const answers: SubmitAnswerRequest[] = this.questions.map((q): SubmitAnswerRequest => {
      const state = this.answers.get(q.id) ?? {
        textAnswer: null,
        selectedChoiceId: null,
        selectedChoiceIds: [],
      };

      if (q.type === 'OPEN') {
        return {
          questionId: q.id,
          answerText: state.textAnswer,
          selectedChoiceId: null,
          selectedChoiceIds: null,
        };
      }

      if (q.type === 'QCM_MULTIPLE') {
        return {
          questionId: q.id,
          answerText: null,
          selectedChoiceId: null,
          selectedChoiceIds: state.selectedChoiceIds.length > 0 ? state.selectedChoiceIds : null,
        };
      }

      // QCM_SINGLE | TRUE_FALSE
      return {
        questionId: q.id,
        answerText: null,
        selectedChoiceId: state.selectedChoiceId,
        selectedChoiceIds: null,
      };
    });

    const request: SubmitAttemptRequest = {
      attemptId: this.attempt.id,
      answers,
    };

    this.assessmentService.submitAttempt(request).subscribe({
      next: () => {
        this.submitted = true;
        this.submitting = false;
        if (this.timerInterval !== null) {
          clearInterval(this.timerInterval);
          this.timerInterval = null;
        }
      },
      error: () => {
        this.error = 'Submission failed. Please try again.';
        this.submitting = false;
      },
    });
  }

  private reportFraudEvent(eventType: FraudEventType, confidenceScore: number): void {
    if (!this.sessionId || this.submitted) return;
    this.proctoringService
      .reportEvent({ sessionId: this.sessionId, eventType, confidenceScore })
      .subscribe();
  }

  private initAnswerMap(exam: ExamResponse): void {
    for (const q of exam.questions ?? []) {
      this.answers.set(q.id, {
        textAnswer: null,
        selectedChoiceId: null,
        selectedChoiceIds: [],
      });
    }
  }

  private startTimer(durationMinutes: number): void {
    this.secondsRemaining = durationMinutes * 60;
    this.timerInterval = setInterval(() => {
      if (this.secondsRemaining > 0) {
        this.secondsRemaining--;
      } else {
        clearInterval(this.timerInterval!);
        this.timerInterval = null;
        this.submitExam();
      }
    }, 1000);
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
