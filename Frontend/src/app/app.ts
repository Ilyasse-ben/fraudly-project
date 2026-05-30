import { Component, OnInit, signal } from '@angular/core';
import { Router, RouterLink, RouterModule, RouterOutlet } from '@angular/router';
import { AuthService } from './core/services/auth.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  protected readonly title = signal('Frontend');

  userName = '';
  userInitials = '';
  userRole = '';

  constructor(public router: Router, public authService: AuthService) {}

  ngOnInit(): void {
    this.loadUserFromToken();
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  private loadUserFromToken(): void {
    const token = this.authService.getToken();
    if (!token) return;
    try {
      const payload = JSON.parse(atob(token.split('.')[1])) as Record<string, unknown>;
      const role = (payload['role'] as string) ?? '';
      const email = (payload['email'] as string) ?? '';

      this.userRole = role.replace('ROLE_', '');

      const fullName = (payload['fullName'] as string) ?? '';
      if (fullName) {
        this.userName = fullName;
        this.userInitials = fullName
          .split(' ')
          .map((w: string) => w[0] ?? '')
          .join('')
          .toUpperCase()
          .slice(0, 2);
      } else if (email) {
        this.userName = email;
        this.userInitials = email.slice(0, 2).toUpperCase();
      } else {
        this.userName = this.userRole;
        this.userInitials = this.userRole.slice(0, 2).toUpperCase();
      }
    } catch {
      // Token unreadable — leave properties empty
    }
  }
}
