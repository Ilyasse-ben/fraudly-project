import { Routes } from '@angular/router';
import { Cours } from './cours/cours';
import { Examen } from './examen/examen';
import { Allcours } from './allcours/allcours';
import { ListEtudientCours } from './list-etudient-cours/list-etudient-cours';
import { Createcours } from './createcours/createcours';
import { Chapiter } from './chapiter/chapiter';
import { DashbordProf } from './dashbord-prof/dashbord-prof';
import { Assistant } from './assistant/assistant';
import { ListExemane } from './list-exemane/list-exemane';
import { Login } from './login/login';
import { Inscription } from './inscription/inscription';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';
import { ExamBuilderComponent } from './exam-builder/exam-builder';
import { ProctoringReview } from './proctoring-review/proctoring-review';
import { ExamAttemptsComponent } from './exam-attempts/exam-attempts';
import { ManualGradingComponent } from './manual-grading/manual-grading';
import { QuestionEditorComponent } from './question-editor/question-editor';
import { StudentAttemptsComponent } from './student-attempts/student-attempts';

export const routes: Routes = [
  // Public routes
  { path: 'login', component: Login },
  { path: 'inscription', component: Inscription },

  // Accessible to both roles
  { path: 'listexemen', component: ListExemane, canActivate: [authGuard] },
  { path: 'exemen/:id', component: Examen, canActivate: [authGuard] },
  { path: 'assistant', component: Assistant, canActivate: [authGuard] },
  { path: 'Allcours', component: Allcours, canActivate: [authGuard] },

  // Teacher-only routes
  { path: 'dashbord', component: DashbordProf, canActivate: [authGuard, roleGuard], data: { expectedRole: 'ROLE_TEACHER' } },
  { path: 'proctoring-review', component: ProctoringReview, canActivate: [authGuard, roleGuard], data: { expectedRole: 'ROLE_TEACHER' } },
  { path: 'exam-attempts/:examId', component: ExamAttemptsComponent, canActivate: [authGuard, roleGuard], data: { expectedRole: 'ROLE_TEACHER' } },
  { path: 'manual-grading/:examId', component: ManualGradingComponent, canActivate: [authGuard, roleGuard], data: { expectedRole: 'ROLE_TEACHER' } },
  { path: 'question-editor/:examId', component: QuestionEditorComponent, canActivate: [authGuard, roleGuard], data: { expectedRole: 'ROLE_TEACHER' } },
  { path: 'exam-builder', component: ExamBuilderComponent, canActivate: [authGuard, roleGuard], data: { expectedRole: 'ROLE_TEACHER' } },

  // Student-only routes
  { path: 'student-attempts/:studentId', component: StudentAttemptsComponent, canActivate: [authGuard, roleGuard], data: { expectedRole: 'ROLE_STUDENT' } },

  // Learning service routes (auth only)
  { path: 'cours/:courseId', component: Cours, canActivate: [authGuard] },
  { path: 'createCours', component: Createcours, canActivate: [authGuard] },
  { path: 'chapitre/:courseId', component: Chapiter, canActivate: [authGuard] },
  { path: 'listEtudiant', component: ListEtudientCours, canActivate: [authGuard] },

  // Default redirect
  { path: '', redirectTo: 'login', pathMatch: 'full' },
];
