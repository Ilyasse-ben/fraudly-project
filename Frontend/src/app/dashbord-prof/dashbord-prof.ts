import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin } from 'rxjs';
import { AnalyticsService } from '../core/services/analytics.service';
import { TopicStats, StudentGrade } from '../core/models/analytics.model';

@Component({
  selector: 'app-dashbord-prof',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashbord-prof.html',
  styleUrl: './dashbord-prof.css'
})
export class DashbordProf implements OnInit {

  private readonly COURSE1_ID = '66666666-6666-6666-6666-666666666666';

  stats = {
    totalStudents: 0,
    activeCourses: 0,
    classAverage: 0,
    examsCompleted: 0
  };

  loading = true;
  error = '';
  courseStats: TopicStats[] = [];
  topStudents: any[] = [];
  studentsGrades: StudentGrade[] = [];
  pendingCount = 0;

  constructor(
    private analyticsService: AnalyticsService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const courseId = this.COURSE1_ID;

    forkJoin({
      topics: this.analyticsService.getCourseTopicStats(courseId),
      grades: this.analyticsService.getStudentsGrades(courseId),
    }).subscribe({
      next: ({ topics, grades }) => {
        this.courseStats = topics;
        this.studentsGrades = grades;
        this.updateStats(grades, topics);
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.error = 'Failed to load dashboard data.';
        this.cdr.detectChanges();
      },
    });
  }

  updateStats(grades: StudentGrade[], topics: TopicStats[]): void {
    const total = grades.length;
    const avg = total > 0
      ? grades.reduce((acc, curr) => acc + curr.average, 0) / total
      : 0;

    this.stats = {
      totalStudents: total,
      activeCourses: topics.length,
      classAverage: parseFloat(avg.toFixed(1)),
      examsCompleted: grades.length,
    };
  }

  // Used by the HTML progress bar width
  calculatePercentage(questions: number): number {
    const MAX_QUESTIONS = 50;
    return Math.min((questions / MAX_QUESTIONS) * 100, 100);
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
