import { Component, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class LoginComponent {

  showPassword = false;

  credenciais = {
    email: '',
    senha: ''
  };

  mensagem = '';
  erro = '';

  constructor(
    private router: Router,
    private authService: AuthService
  ) {}

  togglePassword() {
    this.showPassword = !this.showPassword;
  }

  login(event?: Event): void {
    if (event) event.preventDefault();

    this.mensagem = '';
    this.erro = '';

    // ✅ Agora o AuthService cuida da requisição de login e do cookie
    this.authService.login(this.credenciais.email, this.credenciais.senha).subscribe({
      next: (res) => {
        console.log('Login bem-sucedido:', res);
        this.mensagem = res.message || 'Login realizado com sucesso!';
        setTimeout(() => this.router.navigate(['/home']), 300);
      },
      error: (err) => {
        console.error('Erro no login:', err);
        this.erro = err.error?.error || 'Usuário ou senha incorretos.';
      }
    });
  }
}
