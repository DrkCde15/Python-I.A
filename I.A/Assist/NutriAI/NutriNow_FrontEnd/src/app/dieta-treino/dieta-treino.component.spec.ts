import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DietaTreinoComponent } from './dieta-treino.component';

describe('DietaTreinoComponent', () => {
  let component: DietaTreinoComponent;
  let fixture: ComponentFixture<DietaTreinoComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DietaTreinoComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DietaTreinoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
