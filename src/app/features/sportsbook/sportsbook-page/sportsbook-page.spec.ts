import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { SportsbookPageComponent } from './sportsbook-page';
import { SportsDbService } from '../../../services/sports-db.service';

describe('SportsbookPageComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SportsbookPageComponent],
      providers: [
        {
          provide: SportsDbService,
          useValue: {
            leagues$: of([
              {
                idLeague: '4328',
                strLeague: 'English Premier League',
                strSport: 'Soccer',
                strLeagueAlternate: 'Premier League',
              },
              {
                idLeague: '4387',
                strLeague: 'NBA',
                strSport: 'Basketball',
                strLeagueAlternate: null,
              },
            ]),
            sports$: of([
              { idSport: '1', strSport: 'Soccer' },
              { idSport: '2', strSport: 'Basketball' },
            ]),
            getSeasonBadge: () =>
              of({
                idLeague: '4328',
                strSeason: '2024-2025',
                strBadge: 'https://example.com/badge.png',
              }),
          },
        },
      ],
    }).compileComponents();
  });

  it('should render page title', async () => {
    const fixture = TestBed.createComponent(SportsbookPageComponent);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('h1')?.textContent).toContain('League Explorer');
  });

  it('renders leagues returned by the service', async () => {
    const fixture = TestBed.createComponent(SportsbookPageComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent).toContain('English Premier League');
    expect(compiled.textContent).toContain('NBA');
    expect(compiled.textContent).toContain('2');
  });

  it('filters leagues by search text', async () => {
    const fixture = TestBed.createComponent(SportsbookPageComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const input = fixture.nativeElement.querySelector('input[type="search"]') as HTMLInputElement;
    input.value = 'premier';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent).toContain('English Premier League');
    expect(compiled.textContent).not.toContain('NBA');
  });
});
