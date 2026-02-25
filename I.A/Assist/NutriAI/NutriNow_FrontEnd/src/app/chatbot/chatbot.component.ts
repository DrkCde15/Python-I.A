import { Component, OnInit, OnDestroy, ViewChild, ElementRef, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule } from '@angular/common';
import { isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService, User } from '../services/auth.service';
import { ChatService, ChatResponse } from '../services/chat.service';
import { Subscription } from 'rxjs';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

interface Message {
  text: string;
  isUser: boolean;
  timestamp: Date;
}

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css']
})
export class ChatbotComponent implements OnInit, OnDestroy {
  messages: Message[] = [];
  currentMessage = '';
  currentUser: User | null = null;
  loading = false;
  private subscription = new Subscription();
  private sessionId: string | null = null;
  private isBrowser: boolean;

  @ViewChild('messagesContainer') messagesContainer!: ElementRef;

  constructor(
    private authService: AuthService,
    private chatService: ChatService,
    private router: Router,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  ngOnInit() {
    this.subscription.add(
      this.authService.currentUser$.subscribe(user => {
        this.currentUser = user;
        if (!user && this.isBrowser) {
          this.router.navigate(['/login']);
        }
      })
    );

    if (this.isBrowser) {
      this.sessionId = this.chatService.getSessionId();
      if (!this.sessionId) {
        this.sessionId = this.generateSessionId();
        this.chatService.setSessionId(this.sessionId);
      }
      this.loadChatHistory();
    }
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  private generateSessionId(): string {
    const existing = this.isBrowser ? localStorage.getItem('nutrinow_session_id') : null;
    if (existing) return existing;

    const sid = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    if (this.isBrowser) localStorage.setItem('nutrinow_session_id', sid);
    return sid;
  }

  private loadChatHistory() {
    this.chatService.getChatHistory().subscribe({
      next: (response) => {
        if (response.success && response.history?.length > 0) {
          this.messages = response.history.map((msg: any) => ({
            text: msg.content,
            isUser: msg.type === 'human',
            timestamp: new Date(msg.timestamp || new Date())
          }));
          this.scrollToBottom();
        }
      },
      error: (err: any) => console.error('Erro ao carregar histórico:', err)
    });
  }

  sendMessage() {
    if (!this.currentMessage.trim() || this.loading) return;

    const userMessage: Message = {
      text: this.currentMessage,
      isUser: true,
      timestamp: new Date()
    };
    this.messages.push(userMessage);
    const messageText = this.currentMessage;
    this.currentMessage = '';
    this.loading = true;
    this.scrollToBottom();

    this.chatService.sendMessage(messageText).subscribe({
      next: (response: ChatResponse) => {
        this.loading = false;
        if (response.success) {
          if (response.session_id && this.isBrowser) {
            this.chatService.setSessionId(response.session_id);
            this.sessionId = response.session_id;
          }
          const botMessage: Message = {
            text: response.response!,
            isUser: false,
            timestamp: new Date()
          };
          this.messages.push(botMessage);
        } else {
          this.messages.push({
            text: response.error || 'Erro ao enviar mensagem.',
            isUser: false,
            timestamp: new Date()
          });
        }
        this.scrollToBottom();
      },
      error: (err: any) => {
        console.error('Erro ao enviar mensagem:', err);
        this.loading = false;
        this.messages.push({
          text: 'Erro de conexão com o servidor.',
          isUser: false,
          timestamp: new Date()
        });
        this.scrollToBottom();
      }
    });
  }

  onFileSelected(event: any) {
    if (!this.isBrowser) return;

    const file: File = event.target.files[0];
    if (!file) return;

    const userMessage: Message = {
      text: `📸 Imagem enviada: ${file.name}`,
      isUser: true,
      timestamp: new Date()
    };
    this.messages.push(userMessage);
    this.loading = true;
    this.scrollToBottom();

    this.chatService.analyzeImage(file).subscribe({
      next: (response) => {
        this.loading = false;
        if (response.success) {
          const botMessage: Message = {
            text: response.response,
            isUser: false,
            timestamp: new Date()
          };
          this.messages.push(botMessage);
        } else {
          this.messages.push({
            text: response.error || 'Erro ao analisar a imagem.',
            isUser: false,
            timestamp: new Date()
          });
        }
        this.scrollToBottom();
      },
      error: (err: any) => {
        console.error('Erro ao enviar imagem:', err);
        this.loading = false;
        this.messages.push({
          text: 'Erro ao enviar imagem.',
          isUser: false,
          timestamp: new Date()
        });
        this.scrollToBottom();
      }
    });
  }

  private scrollToBottom() {
    setTimeout(() => {
      if (this.messagesContainer?.nativeElement) {
        this.messagesContainer.nativeElement.scrollTop =
          this.messagesContainer.nativeElement.scrollHeight;
      }
    }, 100);
  }

  // **Logout apenas pelo AuthService**
  logout() {
    if (this.isBrowser) localStorage.removeItem('nutrinow_session_id');
    this.authService.logout().subscribe(() => this.router.navigate(['/login']));
  }

  formatMessage(text: string): string {
    const rawHtml = marked.parse(text || '') as string;
    return DOMPurify.sanitize(rawHtml);
  }

}
