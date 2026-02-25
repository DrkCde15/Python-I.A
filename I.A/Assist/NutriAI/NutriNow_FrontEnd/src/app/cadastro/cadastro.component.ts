import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-cadastro',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HttpClientModule,
    RouterModule
  ],
  templateUrl: './cadastro.component.html',
  styleUrls: ['./cadastro.component.css']
})
export class CadastroComponent {
  showPassword = false;

  usuario = {
    nome: '',
    sobrenome: '',
    data_nascimento: '',
    genero: '',
    email: '',
    senha: ''
  };

  mensagem = '';
  erro = '';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {}

  togglePassword() {
    this.showPassword = !this.showPassword;
    console.log("Toggle clicado:", this.showPassword);
  }

  // criarConta(): void {
  //   this.mensagem = '';
  //   this.erro = '';

  //   this.http.post('http://localhost:8000/cadastro', this.usuario).subscribe({
  //     next: (res: any) => {
  //       this.mensagem = res.message || 'Conta criada com sucesso!';
  //       this.usuario = { nome: '', sobrenome: '', data_nascimento: '', genero: '', email: '', senha: '' };
  //     },
  //     error: (err) => {
  //       this.erro = err.error?.error || 'Erro ao criar conta';
  //     }
  //   });
  // }

  criarConta(form: any): void {
  this.mensagem = '';
  this.erro = '';

  // se o formulário for inválido, marca todos os campos como "touched" para mostrar os erros
  if (form.invalid) {
    Object.values(form.controls).forEach((control: any) => {
      control.markAsTouched();
    });
    this.erro = 'Preencha todos os campos obrigatórios.';
    return;
  }

  // requisição HTTP normalmente
  this.http.post('http://localhost:8000/cadastro', this.usuario).subscribe({
    next: (res: any) => {
      this.mensagem = res.message || 'Conta criada com sucesso!';
      this.usuario = { nome: '', sobrenome: '', data_nascimento: '', genero: '', email: '', senha: '' };
      form.resetForm();
    },
    error: (err) => {
      this.erro = err.error?.error || 'Erro ao criar conta';
    }
  });
}

  voltar(): void {
    this.router.navigate(['/home']);
  }
}
