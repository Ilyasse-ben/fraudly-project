import { Component, OnInit } from '@angular/core';
import { DatePipe, CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AssessmentService } from '../service/assessment.service';
import { ExamResponse, Difficulty } from '../models/assessment.model';

@Component({
  selector: 'app-list-exemane',
  standalone: true,
  imports: [RouterLink, DatePipe, CommonModule],
  templateUrl: './list-exemane.html',
  styleUrl: './list-exemane.css',
})
export class ListExemane implements OnInit {
  exams: ExamResponse[] = [];
  loading = true;
  error = '';

  constructor(private assessmentService: AssessmentService) {}

  ngOnInit(): void {
    const professorId = this.extractUserIdFromToken();
    if (!professorId) {
      this.loading = false;
      this.error = 'Could not identify user. Please log in again.';
      return;
    }

    this.assessmentService.getExamsByProfessor(professorId).subscribe({
      next: (exams) => {
        this.exams = exams;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.error = 'Failed to load exams. Please try again.';
      },
    });
  }

  get pendingCount(): number {
    return this.exams.filter((e) => e.status === 'PUBLISHED').length;
  }

  badgeClass(difficulty: Difficulty): string {
    const map: Record<Difficulty, string> = {
      EASY: 'bg-green-50 text-green-600',
      MEDIUM: 'bg-blue-50 text-blue-600',
      HARD: 'bg-purple-50 text-purple-600',
      VERY_HARD: 'bg-orange-50 text-orange-600',
    };
    return map[difficulty] ?? 'bg-slate-50 text-slate-600';
  }

  private extractUserIdFromToken(): string | null {
    const token = localStorage.getItem('fraudly_access_token');
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload['userId'] ?? payload['sub'] ?? null;
    } catch {
      return null;
    }
  }
}
