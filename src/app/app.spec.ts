import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { App } from './app';
import { SportsDbService } from './services/sports-db.service';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        {
          provide: SportsDbService,
          useValue: {
            leagues$: of([]),
            sports$: of([]),
            getSeasonBadge: () => of(null),
          },
        },
      ],
    }).compileComponents();
  });

  it('should create the sportsbook app shell', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;

    expect(app).toBeTruthy();
  });
});
