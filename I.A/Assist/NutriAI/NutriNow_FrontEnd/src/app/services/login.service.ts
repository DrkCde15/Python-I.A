import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LoginService {
  private apiUrl = 'http://localhost:5000/login'; // backend Flask

  constructor(private http: HttpClient) {}

  login(email: string, senha: string): Observable<any> {
    return this.http.post<any>(
      this.apiUrl,
      { email, senha },
      { withCredentials: true } // ✅ envia o cookie de sessão
    );
  }
}
