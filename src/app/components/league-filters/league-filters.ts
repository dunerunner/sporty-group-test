import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

@Component({
  selector: 'app-league-filters',
  imports: [MatFormFieldModule, MatIconModule, MatInputModule, MatSelectModule],
  templateUrl: './league-filters.html',
  styleUrl: './league-filters.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LeagueFilters {
  readonly sports = input.required<string[]>();
  readonly searchValue = input('');
  readonly sportValue = input('');
  readonly loadingSports = input(false);
  readonly sportsError = input<string | null>(null);

  readonly searchChange = output<string>();
  readonly sportChange = output<string>();
}
