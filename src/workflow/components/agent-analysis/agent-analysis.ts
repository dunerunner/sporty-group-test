import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'app-agent-analysis',
  templateUrl: './agent-analysis.html',
  styleUrl: './agent-analysis.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AgentAnalysisComponent {
  readonly answer = input.required<string>();
}
