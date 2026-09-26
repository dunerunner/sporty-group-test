import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

import {
  CommandResult,
  VerificationCheckName,
  VerificationResult,
} from '../../models/verification.model';
import { WorkflowStatus } from '../../models/workflow.model';

interface VerificationCheckView {
  key: VerificationCheckName;
  label: string;
  result: CommandResult | null;
}

@Component({
  selector: 'app-verification-results',
  templateUrl: './verification-results.html',
  styleUrl: './verification-results.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VerificationResultsComponent {
  readonly verification = input.required<VerificationResult>();
  readonly status = input.required<WorkflowStatus | null>();
  readonly canRepair = input(false);
  readonly loadingMessage = input<string | null>(null);

  readonly repair = output<void>();

  protected readonly checks: VerificationCheckView[] = [
    { key: 'tests', label: 'Tests', result: null },
    { key: 'lint', label: 'Lint', result: null },
    { key: 'build', label: 'Build', result: null },
  ];

  protected resultFor(key: VerificationCheckName): CommandResult | null {
    return this.verification().checks[key] ?? null;
  }
}
