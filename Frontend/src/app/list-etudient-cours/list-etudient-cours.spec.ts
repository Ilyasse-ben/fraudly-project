import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ListEtudientCours } from './list-etudient-cours';

describe('ListEtudientCours', () => {
  let component: ListEtudientCours;
  let fixture: ComponentFixture<ListEtudientCours>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ListEtudientCours],
    }).compileComponents();

    fixture = TestBed.createComponent(ListEtudientCours);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
