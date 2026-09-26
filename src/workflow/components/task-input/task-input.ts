import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-task-input',
  imports: [FormsModule],
  templateUrl: './task-input.html',
  styleUrl: './task-input.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskInputComponent {
  readonly problem = input('');
  readonly canAnalyze = input(false);
  readonly loading = input(false);
  readonly loadingMessage = input<string | null>(null);

  readonly problemChange = output<string>();
  readonly analyze = output<void>();
}
