import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `<router-outlet></router-outlet>`
})
// import { Component } from '@angular/core';
// import { FormsModule } from '@angular/forms';

// @Component({
//   selector: 'app-perfil',
//   standalone: true,
//   imports: [FormsModule],
//   templateUrl: './perfil.component.html',
//   styleUrls: ['./perfil.component.css']
// })
// export class PerfilComponent {
//   nome: string = '';
// }




export class AppComponent {}
