import { JsonPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { AgentStep } from '../../models/agent-step.model';

const toolLabels: Record<string, string> = {
  get_project_structure: 'Inspect project structure',
  search_code: 'Search code',
  read_file: 'Read file',
  run_tests: 'Run tests',
  get_git_status: 'Inspect Git status',
  get_git_diff: 'Inspect Git changes',
  get_git_staged_diff: 'Inspect staged changes',
  get_git_branch: 'Inspect current branch',
  propose_change_set: 'Create change proposal',
};

@Component({
  selector: 'app-agent-steps',
  imports: [JsonPipe],
  templateUrl: './agent-steps.html',
  styleUrl: './agent-steps.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AgentStepsComponent {
  readonly steps = input.required<AgentStep[]>();

  protected labelFor(step: AgentStep): string {
    return toolLabels[step.tool] ?? step.tool.replaceAll('_', ' ');
  }

  protected summaryFor(step: AgentStep): string | null {
    const args = step.arguments;
    const query = this.stringArg(args, 'query');
    const path = this.stringArg(args, 'path') ?? this.stringArg(args, 'file_path');
    const command = this.stringArg(args, 'command');

    if (query) {
      return `Query: ${query}`;
    }
    if (path) {
      return path;
    }
    if (command) {
      return command;
    }
    if (step.tool === 'run_tests') {
      return step.success ? 'Passed' : 'Failed';
    }
    if (step.tool === 'propose_change_set') {
      const count = this.changeCount(step.result);
      return count === null ? null : `${count} ${count === 1 ? 'file' : 'files'}`;
    }

    return null;
  }

  protected hasTechnicalDetails(step: AgentStep): boolean {
    return Boolean(Object.keys(step.arguments).length || step.result !== undefined || step.error);
  }

  private stringArg(args: Record<string, unknown>, key: string): string | null {
    const value = args[key];
    return typeof value === 'string' && value.trim() ? value : null;
  }

  private changeCount(result: unknown): number | null {
    if (!result || typeof result !== 'object' || !('changes' in result)) {
      return null;
    }
    const changes = (result as { changes: unknown }).changes;
    return Array.isArray(changes) ? changes.length : null;
  }
}
