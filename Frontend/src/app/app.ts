import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router, NavigationEnd, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from './core/services/auth.service';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive], // <-- FIXED: Added RouterLinkActive
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  userName = 'Guest';
  userInitials = '?';
  userRole = '';

  constructor(public authService: AuthService, public router: Router) {}

  ngOnInit() {
    this.updateUserFromToken();

    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe(() => {
      this.updateUserFromToken();
    });
  }

  updateUserFromToken() {
    const token = localStorage.getItem('fraudly_access_token');
    if (!token) {
      this.userName = 'Guest';
      this.userInitials = '?';
      this.userRole = '';
      return;
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1])) as Record<string, any>;

      let rawRole = (payload['role'] || 'ROLE_USER').replace('ROLE_', '');
      this.userRole = rawRole.charAt(0).toUpperCase() + rawRole.slice(1).toLowerCase();

      let extractedName = payload['fullName'] || payload['name'] || payload['email'] || payload['sub'];

      if (!extractedName || extractedName.includes('-')) {
        this.userName = this.userRole === 'Teacher' ? 'Professor Account' : 'Student Account';
      } else {
        this.userName = extractedName;
      }

      const nameParts = this.userName.split(/[\s.@_]/);
      if (nameParts.length > 1 && nameParts[0].length > 0 && nameParts[1].length > 0) {
        this.userInitials = (nameParts[0][0] + nameParts[1][0]).toUpperCase();
      } else {
        this.userInitials = this.userName.substring(0, 2).toUpperCase();
      }

    } catch (e) {
      console.error('Failed to decode token in Sidebar:', e);
    }
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
