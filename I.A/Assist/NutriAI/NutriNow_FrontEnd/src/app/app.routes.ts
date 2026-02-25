// import { Routes } from '@angular/router';
// import { AuthGuard } from './services/auth.guard';
// import { LoginComponent } from './login/login.component';
// import { CadastroComponent } from './cadastro/cadastro.component';
// import { HomeComponent } from './home/home.component';
// import { ChatbotComponent } from './chatbot/chatbot.component';
// import { EsqueciSenhaComponent } from './esqueci-senha/esqueci-senha.component';
// import { RedefinirSenhaComponent } from './redefinir-senha/redefinir-senha.component';

// export const routes: Routes = [
//     {path: 'login', component: LoginComponent},
//     {path: 'cadastro', component: CadastroComponent},
//     {path: 'home', component: HomeComponent},
//     {path: 'chatbot', component: ChatbotComponent, canActivate: [AuthGuard]},
//     {path: 'esqueci-senha', component: EsqueciSenhaComponent},
//     { path: '', redirectTo: 'home', pathMatch: 'full' },
//     {path: 'redefinir-senha', component: RedefinirSenhaComponent}
// ];

import { Routes } from '@angular/router';
import { AuthGuard } from './services/auth.guard';
import { LoginComponent } from './login/login.component';
import { CadastroComponent } from './cadastro/cadastro.component';
import { HomeComponent } from './home/home.component';
import { ChatbotComponent } from './chatbot/chatbot.component';
import { EsqueciSenhaComponent } from './esqueci-senha/esqueci-senha.component';
import { RedefinirSenhaComponent } from './redefinir-senha/redefinir-senha.component';

// ✅ Importação dos componentes standalone
import { DietaTreinoComponent } from './dieta-treino/dieta-treino.component';
import { PerfilComponent } from './perfil/perfil.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'cadastro', component: CadastroComponent },
  { path: 'home', component: HomeComponent },
  { path: 'chatbot', component: ChatbotComponent, canActivate: [AuthGuard] },
  { path: 'esqueci-senha', component: EsqueciSenhaComponent },
  { path: 'redefinir-senha', component: RedefinirSenhaComponent },

  // ✅ Novas rotas
  { path: 'dieta-treino', component: DietaTreinoComponent, canActivate: [AuthGuard] },
  { path: 'perfil', component: PerfilComponent, canActivate: [AuthGuard] },

  // Redirecionamento padrão
  { path: '', redirectTo: 'home', pathMatch: 'full' }
];
