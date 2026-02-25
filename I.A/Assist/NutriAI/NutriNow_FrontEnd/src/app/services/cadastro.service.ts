import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Usuario {
  nome: string;
  sobrenome: string;
  data_nascimento: string;
  genero: string;
  email: string;
  senha: string;
}

@Injectable({
  providedIn: 'root'
})
export class CadastroService {
  private apiUrl = 'http://localhost:5000/criar-conta';

  constructor(private http: HttpClient) { }

  criarConta(usuario: Usuario): Observable<any> {
    return this.http.post(this.apiUrl, usuario);
  }

  // Método para testar a conexão com o backend
  testarConexao(): Observable<any> {
    return this.http.get('http://localhost:5000/');
  }
}
