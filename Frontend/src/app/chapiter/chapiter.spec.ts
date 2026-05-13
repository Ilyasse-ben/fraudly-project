import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Chapiter } from './chapiter';

describe('Chapiter', () => {
  let component: Chapiter;
  let fixture: ComponentFixture<Chapiter>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Chapiter],
    }).compileComponents();

    fixture = TestBed.createComponent(Chapiter);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
