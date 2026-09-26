import { ChangeDetectionStrategy, Component } from '@angular/core';

import { SportsbookPageComponent } from './features/sportsbook/sportsbook-page/sportsbook-page';

@Component({
  selector: 'app-root',
  imports: [SportsbookPageComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {}
