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

  // Inline add-chapter form
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

    this.learningService.getChaptersByCourse(this.courseId).subscribe({
      next: (chapters) => {
        this.chapters = chapters.sort((a, b) => a.index - b.index);
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Failed to load chapters. Please try again.';
        this.loading = false;
        this.cdr.detectChanges();
      },
    });
  }

  saveChapter(): void {
    if (!this.newChapterTitle.trim()) return;
    this.saving = true;
    this.saveError = '';

    this.learningService.createChapter({
      title: this.newChapterTitle.trim(),
      index: this.newChapterIndex,
      courseId: this.courseId,
    }).subscribe({
      next: (chapter) => {
        this.chapters = [...this.chapters, chapter].sort((a, b) => a.index - b.index);
        this.newChapterTitle = '';
        this.newChapterIndex = this.chapters.length + 1;
        this.showAddForm = false;
        this.saving = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.saveError = 'Failed to create chapter. Please try again.';
        this.saving = false;
        this.cdr.detectChanges();
      },
    });
  }
}
