// src/app/services/chat.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ChatResponse {
  success: boolean;
  session_id?: string;
  response?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://localhost:8000';
  private sessionId: string | null = null;

  constructor(private http: HttpClient) {}

  // Armazena sessionId local
  setSessionId(sid: string) {
    this.sessionId = sid;
    localStorage.setItem('nutrinow_session_id', sid);
  }

  getSessionId(): string | null {
    if (!this.sessionId) {
      this.sessionId = localStorage.getItem('nutrinow_session_id');
    }
    return this.sessionId;
  }

  // Envia mensagem para o chatbot
  sendMessage(message: string): Observable<ChatResponse> {
    const headers: any = {};
    const session_id = this.getSessionId();
    if (session_id) headers['X-Session-ID'] = session_id;

    return this.http.post<ChatResponse>(
      `${this.apiUrl}/chat`,
      { message },
      { headers, withCredentials: true } // ESSENCIAL
    );
  }

  // Recupera histórico de mensagens
  getChatHistory(): Observable<any> {
    const session_id = this.getSessionId();
    const params: any = {};
    if (session_id) params['session_id'] = session_id;

    return this.http.get<any>(
      `${this.apiUrl}/chat_history`,
      { params, withCredentials: true } // ESSENCIAL
    );
  }

  // Analisa imagem
  analyzeImage(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<any>(
      `${this.apiUrl}/analyze_image`,
      formData,
      { withCredentials: true } // ESSENCIAL
    );
  }
}
