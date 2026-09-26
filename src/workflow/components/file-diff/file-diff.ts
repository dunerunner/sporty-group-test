import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { ProposalChange } from '../../models/proposal.model';

interface DiffLine {
  content: string;
  kind: 'added' | 'removed' | 'context' | 'meta';
}

@Component({
  selector: 'app-file-diff',
  templateUrl: './file-diff.html',
  styleUrl: './file-diff.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FileDiffComponent {
  readonly change = input.required<ProposalChange>();

  protected readonly lines = computed<DiffLine[]>(() =>
    this.change()
      .diff.split('\n')
      .map((line) => ({
        content: line,
        kind: this.lineKind(line),
      })),
  );

  private lineKind(line: string): DiffLine['kind'] {
    if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
      return 'meta';
    }
    if (line.startsWith('+')) {
      return 'added';
    }
    if (line.startsWith('-')) {
      return 'removed';
    }

    return 'context';
  }
}
