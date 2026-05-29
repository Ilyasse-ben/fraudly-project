import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Allcours } from './allcours';

describe('Allcours', () => {
  let component: Allcours;
  let fixture: ComponentFixture<Allcours>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Allcours],
    }).compileComponents();

    fixture = TestBed.createComponent(Allcours);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
