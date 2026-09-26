import { bootstrapApplication } from '@angular/platform-browser';

import { WorkflowAppComponent } from './workflow-app';
import { workflowAppConfig } from './workflow-app.config';

bootstrapApplication(WorkflowAppComponent, workflowAppConfig).catch((err) => console.error(err));
