import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { SportsDbService } from './sports-db.service';

describe('SportsDbService', () => {
  let service: SportsDbService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(SportsDbService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('loads and normalizes leagues', () => {
    const result: unknown[] = [];

    service.leagues$.subscribe((leagues) => result.push(leagues));

    const request = http.expectOne('https://www.thesportsdb.com/api/v1/json/3/all_leagues.php');
    request.flush({
      leagues: [
        {
          idLeague: '4328',
          strLeague: ' English Premier League ',
          strSport: ' Soccer ',
        },
        {
          idLeague: '',
          strLeague: 'Broken League',
          strSport: 'Soccer',
        },
      ],
    });

    expect(result).toEqual([
      [
        {
          idLeague: '4328',
          strLeague: 'English Premier League',
          strSport: 'Soccer',
          strLeagueAlternate: null,
        },
      ],
    ]);
  });

  it('loads sports from all_sports endpoint', () => {
    const result: unknown[] = [];

    service.sports$.subscribe((sports) => result.push(sports));

    const request = http.expectOne('https://www.thesportsdb.com/api/v1/json/3/all_sports.php');
    request.flush({
      sports: [
        { idSport: '2', strSport: 'Basketball' },
        { idSport: '1', strSport: 'Soccer' },
      ],
    });

    expect(result).toEqual([
      [
        { idSport: '2', strSport: 'Basketball' },
        { idSport: '1', strSport: 'Soccer' },
      ],
    ]);
  });

  it('caches badge requests by league id', () => {
    const result: unknown[] = [];

    service.getSeasonBadge('4328').subscribe((badge) => result.push(badge));
    service.getSeasonBadge('4328').subscribe((badge) => result.push(badge));

    const request = http.expectOne(
      'https://www.thesportsdb.com/api/v1/json/3/search_all_seasons.php?badge=1&id=4328',
    );
    request.flush({
      seasons: [
        { idLeague: '4328', strSeason: '2024-2025', strBadge: null },
        { idLeague: '4328', strSeason: '2023-2024', strBadge: 'https://example.com/badge.png' },
      ],
    });

    expect(result).toEqual([
      { idLeague: '4328', strSeason: '2023-2024', strBadge: 'https://example.com/badge.png' },
      { idLeague: '4328', strSeason: '2023-2024', strBadge: 'https://example.com/badge.png' },
    ]);
  });
});
