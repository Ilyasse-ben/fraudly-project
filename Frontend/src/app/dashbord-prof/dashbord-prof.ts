import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
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

  // Data containers for the HTML
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

  constructor(private analyticsService: AnalyticsService) {}

  // Inside dashbord-prof.ts

  ngOnInit(): void {
    const courseId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

    // 1. Populate Course Statistics
    this.analyticsService.getCourseTopicStats(courseId).subscribe({
      next: (data) => {
        this.courseStats = data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.error = 'Failed to load analytics data.';
      },
    });

    // 2. Populate Grades Table
    this.analyticsService.getStudentsGrades(courseId).subscribe({
      next: (data) => {
        this.studentsGrades = data;
        this.updateStats(data);
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.error = 'Failed to load grades data.';
      },
    });
  }

  updateStats(grades: StudentGrade[]): void {
    const total = grades.length;
    if (total === 0) return;

    const avg = grades.reduce((acc, curr) => acc + curr.average, 0) / total;
    this.stats = {
      totalStudents: total,
      activeCourses: 12, // Or fetch from a Courses service
      classAverage: parseFloat(avg.toFixed(1)),
      examsCompleted: total * 3 // Mock logic or fetch from backend
    };
  }

  loadAnalytics(courseId: string): void {
    // 1. Fetch Topic Statistics
    this.analyticsService.getCourseTopicStats(courseId).subscribe({
      next: (data) => {
        this.courseStats = data;
      },
      error: (err) => console.error('Failed to load topic stats', err)
    });

    // Note: You may need to add methods in your AnalyticsService
    // to fetch topStudents and studentGrades if you haven't yet.
  }

  // Used by the HTML progress bar width
  calculatePercentage(questions: number): number {
    const MAX_QUESTIONS = 50; // Set this to your desired scale
    return Math.min((questions / MAX_QUESTIONS) * 100, 100);
  }
}
