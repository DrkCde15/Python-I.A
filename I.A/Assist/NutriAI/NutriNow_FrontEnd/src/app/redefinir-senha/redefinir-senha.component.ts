import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { ActivatedRoute, RouterModule } from '@angular/router';

@Component({
  selector: 'app-redefinir-senha',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule, RouterModule],
  templateUrl: './redefinir-senha.component.html',
  styleUrls: ['./redefinir-senha.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class RedefinirSenhaComponent implements OnInit {

  token = '';
  novaSenha = '';
  confirmarSenha = '';
  mensagem = '';
  erro = '';

  constructor(private http: HttpClient, private route: ActivatedRoute) { }

  ngOnInit(): void {
    // Captura o token da URL (?token=xxxx)
    this.route.queryParams.subscribe(params => {
      this.token = params['token'] || '';
      // const header = document.querySelector('header');
      // if (header) header.style.display = 'none';
    });
  }

  // ngOnDestroy() {
  //   const header = document.querySelector('header');
  //   if (header) header.style.display = '';
  // }

  redefinirSenha(): void {
    this.mensagem = '';
    this.erro = '';

    if (!this.novaSenha.trim() || !this.confirmarSenha.trim()) {
      this.erro = 'Por favor, preencha todos os campos.';
      return;
    }

    if (this.novaSenha !== this.confirmarSenha) {
      this.erro = 'As senhas não coincidem.';
      return;
    }

    this.http.post('http://localhost:8000/redefinir-senha', {
      token: this.token,
      nova_senha: this.novaSenha
    }).subscribe({
      next: (res: any) => {
        this.mensagem = res.message || 'Senha redefinida com sucesso!';
      },
      error: (err) => {
        this.erro = err.error?.error || 'Erro ao redefinir senha.';
      }
    });
  }
}