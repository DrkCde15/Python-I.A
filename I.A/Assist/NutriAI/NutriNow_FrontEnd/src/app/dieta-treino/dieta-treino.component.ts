import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';

interface Item {
  id: number;
  title: string;
  description: string;
  time?: string;
}

@Component({
  selector: 'app-dieta-treino',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './dieta-treino.component.html',
  styleUrls: ['./dieta-treino.component.css']
})
export class DietaTreinoComponent implements OnInit {
  private http = inject(HttpClient);
  backendUrl = 'http://localhost:8000/dieta-treino';

  activeTab: 'treinos' | 'dietas' = 'treinos';
  workouts: Item[] = [];
  meals: Item[] = [];
  editingItem: Item | null = null;

  // Modal controls
  mostrarModal = false;
  inputTitle = '';
  inputDescription = '';
  inputTime = '';

  // --- Lifecycle ---
  ngOnInit() {
    this.loadItems();
  }

  // --- Carregar itens do backend ---
  loadItems() {
    ['treinos', 'dietas'].forEach(tab => {
      const tipo = tab === 'treinos' ? 'treino' : 'dieta';
      this.http.get(`${this.backendUrl}?tipo=${tipo}`, { withCredentials: true })
        .subscribe({
          next: (res: any) => {
            if (tipo === 'treino') this.workouts = res.items || [];
            else this.meals = res.items || [];
          },
          error: err => console.error('Erro ao carregar items:', err)
        });
    });
  }

  // --- Métodos de abas ---
  switchTab(tab: 'treinos' | 'dietas') {
    this.activeTab = tab;
    this.editingItem = null;
  }

  // --- Modal ---
  openModal() {
    this.mostrarModal = true;
    this.clearForm();
  }

  closeModal() {
    this.mostrarModal = false;
    this.clearForm();
    this.editingItem = null;
  }

  clearForm() {
    this.inputTitle = '';
    this.inputDescription = '';
    this.inputTime = '';
  }

  get modalTitle() {
    const action = this.editingItem ? 'Editar' : 'Adicionar';
    const type = this.activeTab === 'treinos' ? 'Treino' : 'Refeição';
    return `${action} ${type}`;
  }

  get buttonText() {
    return this.editingItem ? 'Atualizar' : 'Adicionar';
  }

  // --- Adicionar / Editar ---
  handleSubmit() {
    const title = this.inputTitle.trim();
    const description = this.inputDescription.trim();
    const time = this.inputTime.trim();

    if (!title || !description) {
      alert('Por favor, preencha todos os campos obrigatórios');
      return;
    }

    if (this.editingItem) {
      this.updateItem(title, description, time);
    } else {
      this.addItem(title, description, time);
    }

    this.closeModal();
  }

  addItem(title: string, description: string, time: string) {
    const payload = {
      title,
      description,
      time,
      tipo: this.activeTab === 'treinos' ? 'treino' : 'dieta'
    };

    this.http.post(this.backendUrl, payload, { withCredentials: true })
      .subscribe({
        next: (res: any) => {
          const newItem: Item = { id: Date.now(), title, description, time };
          if (this.activeTab === 'treinos') this.workouts.push(newItem);
          else this.meals.push(newItem);
        },
        error: err => alert('Erro ao salvar item no servidor: ' + err.error?.error || err.message)
      });
  }

  updateItem(title: string, description: string, time: string) {
    if (!this.editingItem) return;

    const payload = {
      title,
      description,
      time,
      tipo: this.activeTab === 'treinos' ? 'treino' : 'dieta'
    };

    this.http.put(`${this.backendUrl}/${this.editingItem.id}`, payload, { withCredentials: true })
      .subscribe({
        next: (res: any) => {
          const items = this.activeTab === 'treinos' ? this.workouts : this.meals;
          const index = items.findIndex(item => item.id === this.editingItem!.id);
          if (index !== -1) items[index] = { ...items[index], title, description, time };
        },
        error: err => alert('Erro ao atualizar item no servidor: ' + err.error?.error || err.message)
      });
  }

  editItem(item: Item) {
    this.editingItem = item;
    this.inputTitle = item.title;
    this.inputDescription = item.description;
    this.inputTime = item.time || '';
    this.mostrarModal = true;
  }

  deleteItem(id: number) {
    if (!confirm('Tem certeza que deseja excluir este item?')) return;

    this.http.delete(`${this.backendUrl}/${id}`, { withCredentials: true })
      .subscribe({
        next: (res: any) => {
          if (this.activeTab === 'treinos') {
            this.workouts = this.workouts.filter(w => w.id !== id);
          } else {
            this.meals = this.meals.filter(m => m.id !== id);
          }
        },
        error: err => alert('Erro ao excluir item no servidor: ' + err.error?.error || err.message)
      });
  }

  // --- Auxiliares ---
  get currentItems(): Item[] {
    return this.activeTab === 'treinos' ? this.workouts : this.meals;
  }

  get emptyText() {
    return this.activeTab === 'treinos'
      ? 'Nenhum treino cadastrado ainda'
      : 'Nenhuma refeição cadastrada ainda';
  }

  get addButtonText() {
    return this.activeTab === 'treinos' ? 'Adicionar Treino' : 'Adicionar Refeição';
  }
}