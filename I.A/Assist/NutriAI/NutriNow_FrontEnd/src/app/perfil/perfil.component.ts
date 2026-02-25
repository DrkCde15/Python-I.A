import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-perfil',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './perfil.component.html',
  styleUrls: ['./perfil.component.css']
})
export class PerfilComponent implements OnInit {
  // Dados do perfil
  nome: string = '';
  foto: string = 'U';
  email: string = '';
  dataNascimento: string = '';
  meta: string = '';
  alturaPeso: string = '';

  // Controle do modal
  mostrarModal: boolean = false;

  // Inputs temporários
  nomeInput: string = '';
  emailInput: string = '';
  dataInput: string = '';
  metaInput: string = '';
  alturaInput: string = '';
  pesoInput: string = '';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.carregarPerfil();
  }

  // ----------------- Carregar perfil do backend -----------------
  carregarPerfil(): void {
    this.http.get<any>('http://localhost:8000/perfil', { withCredentials: true })
      .subscribe({
        next: res => {
          if (res.success) {
            this.nome = res.nome;
            this.email = res.email;
            this.dataNascimento = res.dataNascimento || '--/--/----';
            this.meta = res.meta || 'Não definida';
            this.alturaPeso = res.alturaPeso || '-- / --';

            // Gera iniciais da foto
            const nomes = this.nome.split(' ').filter(n => n.length > 0);
            this.foto = nomes.length >= 2 
              ? (nomes[0][0] + nomes[nomes.length-1][0]).toUpperCase()
              : nomes[0][0].toUpperCase();
          }
        },
        error: err => console.error('Erro ao carregar perfil', err)
      });
  }

  // ----------------- Modal -----------------
  abrirModal(): void {
    this.mostrarModal = true;
    this.nomeInput = this.nome;
    this.emailInput = this.email;
    this.dataInput = this.dataNascimento;
    this.metaInput = this.meta;

    const [altura, peso] = this.alturaPeso.split(' / ');
    this.alturaInput = altura?.replace('m', '').trim() || '';
    this.pesoInput = peso?.replace('kg', '').trim() || '';
  }

  fecharModal(): void {
    this.mostrarModal = false;
  }

  // ----------------- Salvar perfil -----------------
  salvarPerfil(): void {
    const alturaPesoStr = this.alturaInput && this.pesoInput 
      ? `${this.alturaInput}m / ${this.pesoInput}kg` 
      : '';

    const payload = {
      nome: this.nomeInput,
      email: this.emailInput,
      dataNascimento: this.dataInput,
      meta: this.metaInput,
      alturaPeso: alturaPesoStr
    };

    this.http.post<any>('http://localhost:8000/perfil', payload, { withCredentials: true })
      .subscribe({
        next: res => {
          if (res.success) {
            this.carregarPerfil();  // Atualiza a interface com os dados do backend
            this.fecharModal();
          }
        },
        error: err => console.error('Erro ao salvar perfil', err)
      });
  }

  // ----------------- Excluir conta -----------------
  excluirConta(): void {
    if (confirm('Tem certeza que deseja excluir a conta?')) {
      this.http.delete<any>('http://localhost:8000/perfil', { withCredentials: true })
        .subscribe({
          next: res => {
            if (res.success) {
              alert('Conta excluída com sucesso!');
              // Limpa dados locais
              this.nome = '';
              this.foto = 'U';
              this.email = '';
              this.dataNascimento = '';
              this.meta = '';
              this.alturaPeso = '';
            }
          },
          error: err => console.error('Erro ao excluir conta', err)
        });
    }
  }
}
