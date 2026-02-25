import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from './auth.service';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(): Observable<boolean> {
    // currentUser$ já é um BehaviorSubject que emite null se não estiver logado
    return this.authService.currentUser$.pipe(
      map(user => {
        if (user) {
          // Usuário logado, libera rota
          return true;
        } else {
          // Usuário não logado, redireciona para login
          this.router.navigate(['/login']);
          return false;
        }
      })
    );
  }
}
