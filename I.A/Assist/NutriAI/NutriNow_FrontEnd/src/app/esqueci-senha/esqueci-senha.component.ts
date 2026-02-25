import { Component, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-esqueci-senha',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HttpClientModule,
    RouterModule
  ],
  templateUrl: './esqueci-senha.component.html',
  styleUrls: ['./esqueci-senha.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class EsqueciSenhaComponent {

  email = '';
  mensagem = '';
  erro = '';

  constructor(private http: HttpClient) {}

  esqueciSenha(): void {
    this.mensagem = '';
    this.erro = '';

    if (!this.email.trim()) {
      this.erro = 'Por favor, informe seu email';
      return;
    }

    this.http.post('http://localhost:8000/esqueci-senha', { email: this.email }).subscribe({
      next: (res: any) => {
        this.mensagem = res.message || 'Um link de redefinição foi enviado para seu email!';
      },
      error: (err) => {
        this.erro = err.error?.error || 'Erro ao enviar link de redefinição';
      }
    });
  }
}
