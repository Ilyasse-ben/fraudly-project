import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ListExemane } from './list-exemane';

describe('ListExemane', () => {
  let component: ListExemane;
  let fixture: ComponentFixture<ListExemane>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ListExemane],
    }).compileComponents();

    fixture = TestBed.createComponent(ListExemane);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
