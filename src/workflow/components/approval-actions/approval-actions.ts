import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

@Component({
  selector: 'app-approval-actions',
  templateUrl: './approval-actions.html',
  styleUrl: './approval-actions.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ApprovalActionsComponent {
  readonly disabled = input(false);
  readonly loadingMessage = input<string | null>(null);

  readonly approve = output<void>();
  readonly reject = output<void>();
}
