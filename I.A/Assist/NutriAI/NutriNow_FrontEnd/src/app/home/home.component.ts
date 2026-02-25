import { Component, Renderer2 } from '@angular/core';
import { RouterModule, Router } from '@angular/router';

// @Component({
//   selector: 'app-home',
//   standalone: true,
//   imports: [RouterModule],
//   templateUrl: './home.component.html',
//   styleUrls: ['./home.component.css']
// })
// export class HomeComponent {
  
// }

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent {

  constructor(private renderer: Renderer2) {}

  toggleFaq(event: Event): void {
    const clickedItem = (event.currentTarget as HTMLElement).closest('.faq-item');
    if (!clickedItem) return;

    const allFaqs = document.querySelectorAll('.faq-item');

    allFaqs.forEach(faq => {
      if (faq !== clickedItem) {
        this.renderer.removeClass(faq, 'active');
      }
    });

    if (clickedItem.classList.contains('active')) {
      this.renderer.removeClass(clickedItem, 'active');
    } else {
      this.renderer.addClass(clickedItem, 'active');
    }
  }
}