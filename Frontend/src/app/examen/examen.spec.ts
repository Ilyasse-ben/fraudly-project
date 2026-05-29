import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Examen } from './examen';

describe('Examen', () => {
  let component: Examen;
  let fixture: ComponentFixture<Examen>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Examen],
    }).compileComponents();

    fixture = TestBed.createComponent(Examen);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
