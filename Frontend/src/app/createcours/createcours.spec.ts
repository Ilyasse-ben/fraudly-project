import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Createcours } from './createcours';

describe('Createcours', () => {
  let component: Createcours;
  let fixture: ComponentFixture<Createcours>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Createcours],
    }).compileComponents();

    fixture = TestBed.createComponent(Createcours);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
