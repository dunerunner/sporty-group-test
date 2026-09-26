import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { AgentAnalysisComponent } from '../../components/agent-analysis/agent-analysis';
import { AgentStepsComponent } from '../../components/agent-steps/agent-steps';
import { ApprovalActionsComponent } from '../../components/approval-actions/approval-actions';
import { ErrorPanelComponent } from '../../components/error-panel/error-panel';
import { ProposalViewerComponent } from '../../components/proposal-viewer/proposal-viewer';
import { TaskInputComponent } from '../../components/task-input/task-input';
import { VerificationResultsComponent } from '../../components/verification-results/verification-results';
import { WorkflowStatusComponent } from '../../components/workflow-status/workflow-status';
import { workflowStatusLabels } from '../../models/workflow.model';
import { WorkflowStore } from '../../services/workflow.store';

@Component({
  selector: 'app-workflow-page',
  imports: [
    AgentAnalysisComponent,
    AgentStepsComponent,
    ApprovalActionsComponent,
    ErrorPanelComponent,
    ProposalViewerComponent,
    TaskInputComponent,
    VerificationResultsComponent,
    WorkflowStatusComponent,
  ],
  templateUrl: './workflow-page.html',
  styleUrl: './workflow-page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WorkflowPageComponent {
  protected readonly store = inject(WorkflowStore);
  protected readonly statusLabels = workflowStatusLabels;
}
