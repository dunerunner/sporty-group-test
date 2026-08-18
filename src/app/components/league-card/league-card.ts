import { AsyncPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, Input, OnChanges, inject } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Observable, catchError, map, of, startWith } from 'rxjs';

import { SeasonBadge } from '../../models/sports-db.models';
import { SportsDbService } from '../../services/sports-db.service';

type BadgeViewModel =
  | { state: 'loading'; badge: null }
  | { state: 'loaded'; badge: SeasonBadge | null }
  | { state: 'error'; badge: null };

@Component({
  selector: 'app-league-card',
  imports: [AsyncPipe, MatCardModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './league-card.html',
  styleUrl: './league-card.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LeagueCard implements OnChanges {
  private readonly sportsDb = inject(SportsDbService);

  @Input({ required: true }) leagueId = '';
  @Input({ required: true }) leagueName = '';
  @Input({ required: true }) sport = '';
  @Input() alternateName: string | null = null;

  protected badgeView$: Observable<BadgeViewModel> = of({ state: 'loading', badge: null });

  ngOnChanges(): void {
    this.badgeView$ = this.sportsDb.getSeasonBadge(this.leagueId).pipe(
      map((badge): BadgeViewModel => ({ state: 'loaded', badge })),
      startWith({ state: 'loading', badge: null } satisfies BadgeViewModel),
      catchError(() => of({ state: 'error', badge: null } satisfies BadgeViewModel)),
    );
  }
}
