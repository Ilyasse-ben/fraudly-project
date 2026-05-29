import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashbordProf } from './dashbord-prof';

describe('DashbordProf', () => {
  let component: DashbordProf;
  let fixture: ComponentFixture<DashbordProf>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashbordProf],
    }).compileComponents();

    fixture = TestBed.createComponent(DashbordProf);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
