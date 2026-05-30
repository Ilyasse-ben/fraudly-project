import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { NgClass, DatePipe } from '@angular/common';
import { ProctoringService } from '../service/proctoring.service';
import { ProctoringSessionResponse, FraudEventResponse } from '../models/proctoring.model';

@Component({
  selector: 'app-proctoring-review',
  standalone: true,
  imports: [NgClass, DatePipe],
  templateUrl: './proctoring-review.html',
})
export class ProctoringReview implements OnInit {
  sessions: ProctoringSessionResponse[] = [];
  events: FraudEventResponse[] = [];
  selectedSessionId: string | null = null;
  loadingSessions = true;
  loadingEvents = false;
  sessionsError = '';
  eventsError = '';

  constructor(
    private proctoringService: ProctoringService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.proctoringService.getFlaggedSessions().subscribe({
      next: (sessions) => {
        this.sessions = sessions;
        this.loadingSessions = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loadingSessions = false;
        this.sessionsError = 'Failed to load flagged sessions.';
        this.cdr.detectChanges();
      },
    });
  }

  selectSession(sessionId: string): void {
    this.selectedSessionId = sessionId;
    this.loadingEvents = true;
    this.eventsError = '';
    this.events = [];
    this.proctoringService.getSessionEvents(sessionId).subscribe({
      next: (events) => {
        this.events = events;
        this.loadingEvents = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loadingEvents = false;
        this.eventsError = 'Failed to load events for this session.';
        this.cdr.detectChanges();
      },
    });
  }

  fraudScoreClass(score: number): string {
    if (score >= 70) return 'text-red-600 font-bold';
    if (score >= 40) return 'text-orange-500 font-semibold';
    return 'text-green-600 font-semibold';
  }

  confidencePct(score: number): string {
    return (score * 100).toFixed(0);
  }
}
