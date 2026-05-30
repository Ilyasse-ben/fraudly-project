import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { LearningService } from '../service/learning.service';
import { AuthService } from '../core/services/auth.service';
import { Chapter } from '../models/learning.model';

@Component({
  selector: 'app-chapiter',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chapiter.html',
  styleUrl: './chapiter.css',
})
export class Chapiter implements OnInit {
  chapters: Chapter[] = [];
  loading = true;
  error = '';
  courseId = '';
  isTeacher = false;

  showAddForm = false;
  newChapterTitle = '';
  newChapterIndex = 1;
  saving = false;
  saveError = '';

  constructor(
    private learningService: LearningService,
    private route: ActivatedRoute,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.courseId = this.route.snapshot.paramMap.get('courseId') ?? '';
    this.isTeacher = this.authService.isProfessor();

    // Workaround: Since there's no endpoint to get chapters by course,
    // we get the course and extract the chapters.
    this.learningService.getCourseById(this.courseId).subscribe({
      next: (course: any) => {
        this.chapters = (course.chapitres || []).sort((a: any, b: any) => a.index - b.index);
        this.newChapterIndex = this.chapters.length + 1;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Failed to load chapters for this course.';
        this.loading = false;
        this.cdr.detectChanges();
      },
    });
  }

  saveChapter(): void {
    if (!this.newChapterTitle.trim()) return;
    this.saving = true;
    this.saveError = '';

    // Fixed: calling createChapter with courseId passed separately to match POST /api/learning/chapitres/{courseId}
    this.learningService.createChapter(this.courseId, {
      title: this.newChapterTitle.trim(),
      index: this.newChapterIndex,
      courseId: this.courseId
    }).subscribe({
      next: (chapter) => {
        this.chapters = [...this.chapters, chapter].sort((a, b) => a.index - b.index);
        this.newChapterTitle = '';
        this.newChapterIndex = this.chapters.length + 1;
        this.showAddForm = false;
        this.saving = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.saveError = err?.error?.message || 'Failed to create chapter. Please try again.';
        this.saving = false;
        this.cdr.detectChanges();
      },
    });
  }
}
