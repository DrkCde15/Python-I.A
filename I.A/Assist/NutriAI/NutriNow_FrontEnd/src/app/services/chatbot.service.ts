import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ChatResponse {
  response: string;
  status?: string;
  error?: string;
}

export interface ImageAnalysisResponse {
  response: string;
  status?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ChatbotService {
  private apiUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) { }

  // Método para enviar mensagem de texto
  sendMessage(message: string): Observable<ChatResponse> {
    const formData = new FormData();
    formData.append('message', message);

    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, formData);
  }

  // Método para análise de imagem
  analyzeImage(file: File): Observable<ImageAnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<ImageAnalysisResponse>(`${this.apiUrl}/analyze_image`, formData);
  }
}