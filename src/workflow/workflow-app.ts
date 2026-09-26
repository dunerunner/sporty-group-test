import { ChangeDetectionStrategy, Component } from '@angular/core';

import { WorkflowPageComponent } from './pages/workflow-page/workflow-page';

@Component({
  selector: 'app-root',
  imports: [WorkflowPageComponent],
  template: '<app-workflow-page />',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WorkflowAppComponent {}
