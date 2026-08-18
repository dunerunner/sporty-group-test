import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { LeagueCard } from './league-card';
import { SportsDbService } from '../../services/sports-db.service';

describe('LeagueCard', () => {
  let fixture: ComponentFixture<LeagueCard>;
  let sportsDb: Pick<SportsDbService, 'getSeasonBadge'>;

  beforeEach(async () => {
    sportsDb = {
      getSeasonBadge: vi.fn(() =>
        of({
          idLeague: '4328',
          strSeason: '2024-2025',
          strBadge: 'https://example.com/badge.png',
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [LeagueCard],
      providers: [{ provide: SportsDbService, useValue: sportsDb }],
    }).compileComponents();

    fixture = TestBed.createComponent(LeagueCard);
    fixture.componentRef.setInput('leagueId', '4328');
    fixture.componentRef.setInput('leagueName', 'English Premier League');
    fixture.componentRef.setInput('sport', 'Soccer');
    fixture.componentRef.setInput('alternateName', 'Premier League');
    fixture.detectChanges();
  });

  it('renders league details from inputs', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent).toContain('English Premier League');
    expect(compiled.textContent).toContain('Soccer');
    expect(compiled.textContent).toContain('Premier League');
  });

  it('loads and renders the season badge', async () => {
    await fixture.whenStable();
    fixture.detectChanges();

    const image = fixture.nativeElement.querySelector('img') as HTMLImageElement | null;

    expect(sportsDb.getSeasonBadge).toHaveBeenCalledWith('4328');
    expect(image?.src).toBe('https://example.com/badge.png');
    expect(image?.alt).toBe('English Premier League season badge');
    expect(fixture.nativeElement.textContent).toContain('2024-2025');
  });
});
