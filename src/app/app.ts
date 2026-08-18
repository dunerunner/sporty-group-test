import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MatIconModule } from '@angular/material/icon';
import { catchError, finalize, of } from 'rxjs';

import { LeagueCard } from './components/league-card/league-card';
import { LeagueFilters } from './components/league-filters/league-filters';
import { League } from './models/sports-db.models';
import { SportsDbService } from './services/sports-db.service';

@Component({
  selector: 'app-root',
  imports: [LeagueCard, LeagueFilters, MatIconModule],
  templateUrl: './app.html',
  styleUrl: './app.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  private readonly sportsDb = inject(SportsDbService);

  protected readonly leagues = signal<League[]>([]);
  protected readonly sports = signal<string[]>([]);
  protected readonly searchTerm = signal('');
  protected readonly sportFilter = signal('');
  protected readonly isLoadingLeagues = signal(true);
  protected readonly isLoadingSports = signal(true);
  protected readonly leagueError = signal<string | null>(null);
  protected readonly sportsError = signal<string | null>(null);

  protected readonly filteredLeagues = computed(() => {
    const query = this.searchTerm().trim().toLowerCase();
    const sport = this.sportFilter();

    return this.leagues().filter((league) => {
      const matchesSearch = !query || league.strLeague.toLowerCase().includes(query);
      const matchesSport = !sport || league.strSport === sport;

      return matchesSearch && matchesSport;
    });
  });

  constructor() {
    this.sportsDb.leagues$
      .pipe(
        catchError(() => {
          this.leagueError.set('Unable to load sports leagues. Please try again later.');
          return of([]);
        }),
        finalize(() => this.isLoadingLeagues.set(false)),
        takeUntilDestroyed(),
      )
      .subscribe((leagues) => this.leagues.set(leagues));

    this.sportsDb.sports$
      .pipe(
        catchError(() => {
          this.sportsError.set('Unable to load sport types.');
          return of([]);
        }),
        finalize(() => this.isLoadingSports.set(false)),
        takeUntilDestroyed(),
      )
      .subscribe((sports) => this.sports.set(sports.map((sport) => sport.strSport)));
  }

  protected updateSearchTerm(value: string): void {
    this.searchTerm.set(value);
  }

  protected updateSportFilter(value: string): void {
    this.sportFilter.set(value);
  }
}
