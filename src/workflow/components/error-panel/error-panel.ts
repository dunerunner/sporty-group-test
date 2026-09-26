import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { WorkflowError } from '../../models/workflow.model';

@Component({
  selector: 'app-error-panel',
  templateUrl: './error-panel.html',
  styleUrl: './error-panel.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ErrorPanelComponent {
  readonly error = input.required<WorkflowError>();
}
