import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map, of, shareReplay } from 'rxjs';

import {
  LeaguesResponse,
  SeasonBadge,
  SeasonBadgesResponse,
  Sport,
  SportsResponse,
} from '../models/sports-db.models';

@Injectable({ providedIn: 'root' })
export class SportsDbService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'https://www.thesportsdb.com/api/v1/json/3';
  private readonly badgeCache = new Map<string, Observable<SeasonBadge | null>>();

  readonly leagues$ = this.http.get<LeaguesResponse>(`${this.baseUrl}/all_leagues.php`).pipe(
    map((response) =>
      (response.leagues ?? [])
        .filter((league) => Boolean(league.idLeague && league.strLeague && league.strSport))
        .map((league) => ({
          idLeague: String(league.idLeague),
          strLeague: league.strLeague.trim(),
          strSport: league.strSport.trim(),
          strLeagueAlternate: league.strLeagueAlternate?.trim() || null,
        })),
    ),
    shareReplay({ bufferSize: 1, refCount: false }),
  );

  readonly sports$ = this.http.get<SportsResponse>(`${this.baseUrl}/all_sports.php`).pipe(
    map((response) =>
      (response.sports ?? [])
        .filter((sport): sport is Sport => Boolean(sport.strSport))
        .sort((a, b) => a.strSport.localeCompare(b.strSport)),
    ),
    shareReplay({ bufferSize: 1, refCount: false }),
  );

  getSeasonBadge(leagueId: string): Observable<SeasonBadge | null> {
    if (!leagueId) {
      return of(null);
    }

    const cached = this.badgeCache.get(leagueId);
    if (cached) {
      return cached;
    }

    const request$ = this.http
      .get<SeasonBadgesResponse>(`${this.baseUrl}/search_all_seasons.php?badge=1&id=${leagueId}`)
      .pipe(
        map((response) => response.seasons?.find((season) => Boolean(season.strBadge)) ?? null),
        shareReplay({ bufferSize: 1, refCount: false }),
      );

    this.badgeCache.set(leagueId, request$);
    return request$;
  }
}
