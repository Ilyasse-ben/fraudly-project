import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LearningService } from '../service/learning.service';
import { AuthService } from '../core/services/auth.service';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

@Component({
  selector: 'app-assistant',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './assistant.html',
  styleUrl: './assistant.css',
})
export class Assistant implements OnInit {
  messages: ChatMessage[] = [
    {
      role: 'assistant',
      content: 'Hello! 👋 I am your AI educational assistant. I can help you understand lessons, summarize chapters, generate quizzes and answer your course questions.',
    },
  ];
  inputMessage = '';
  loading = false;
  studentId = '';
  readonly courseId = '66666666-6666-6666-6666-666666666666';

  constructor(
    private learningService: LearningService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.studentId = this.extractUserIdFromToken() ?? '';
  }

  sendMessage(): void {
    const question = this.inputMessage.trim();
    if (!question || this.loading) return;

    this.messages = [...this.messages, { role: 'user', content: question }];
    this.inputMessage = '';
    this.loading = true;
    this.cdr.detectChanges();

    this.learningService.askTutor(question, this.studentId, this.courseId).subscribe({
      next: (res) => {
        this.messages = [...this.messages, { role: 'assistant', content: res.answer }];
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.messages = [...this.messages, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }];
        this.loading = false;
        this.cdr.detectChanges();
      },
    });
  }

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
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
