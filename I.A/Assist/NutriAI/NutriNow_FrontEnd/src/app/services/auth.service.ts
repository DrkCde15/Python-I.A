// src/app/services/auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';

export interface User {
  id: number;
  nome: string;
  email: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8000';
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(private http: HttpClient) {
    const user = localStorage.getItem('usuario');
    if (user) {
      this.currentUserSubject.next(JSON.parse(user));
    }
  }

  login(email: string, senha: string): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/login`,
      { email, senha },
      { withCredentials: true } // ESSENCIAL para salvar cookie da sessão
    ).pipe(
      tap(response => {
        if (response.user) {
          localStorage.setItem('usuario', JSON.stringify(response.user));
          this.currentUserSubject.next(response.user);
        }
      })
    );
  }

  logout(): Observable<any> {
    return this.http.post(`${this.apiUrl}/logout`, {}, { withCredentials: true }).pipe(
      tap(() => {
        this.currentUserSubject.next(null);
        localStorage.removeItem('usuario');
      })
    );
  }

  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }
}
