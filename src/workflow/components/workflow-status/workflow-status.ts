import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { WorkflowStatus, workflowStatusLabels } from '../../models/workflow.model';

type StepState = 'done' | 'current' | 'failed' | 'pending';

interface WorkflowStepView {
  label: string;
  state: StepState;
}

@Component({
  selector: 'app-workflow-status',
  templateUrl: './workflow-status.html',
  styleUrl: './workflow-status.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WorkflowStatusComponent {
  readonly status = input<WorkflowStatus | null>(null);

  protected readonly statusLabel = computed(() => {
    const status = this.status();
    return status ? workflowStatusLabels[status] : 'Not started';
  });

  protected readonly steps = computed<WorkflowStepView[]>(() => {
    const status = this.status();
    const activeIndex = this.resolveActiveIndex(status);
    const failedStatuses: WorkflowStatus[] = [
      'verification_failed',
      'proposal_stale',
      'apply_failed',
      'repair_limit_reached',
    ];

    return ['Analyze', 'Proposal', 'Approval', 'Apply', 'Verification', 'Completed'].map(
      (label, index) => {
        if (status === 'rejected' && index >= 3) {
          return { label, state: 'pending' };
        }
        if (failedStatuses.includes(status as WorkflowStatus) && index === activeIndex) {
          return { label, state: 'failed' };
        }
        if (status === 'completed' && index <= activeIndex) {
          return { label, state: 'done' };
        }
        if (index < activeIndex) {
          return { label, state: 'done' };
        }
        if (index === activeIndex && status) {
          return { label, state: 'current' };
        }

        return { label, state: 'pending' };
      },
    );
  });

  private resolveActiveIndex(status: WorkflowStatus | null): number {
    switch (status) {
      case 'analyzing':
        return 0;
      case 'awaiting_approval':
        return 2;
      case 'applying':
      case 'apply_failed':
      case 'proposal_stale':
        return 3;
      case 'verifying':
      case 'verification_failed':
      case 'repair_limit_reached':
        return 4;
      case 'completed':
        return 5;
      case 'rejected':
        return 2;
      default:
        return -1;
    }
  }
}
