import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { Proposal } from '../../models/proposal.model';
import { FileDiffComponent } from '../file-diff/file-diff';

@Component({
  selector: 'app-proposal-viewer',
  imports: [FileDiffComponent],
  templateUrl: './proposal-viewer.html',
  styleUrl: './proposal-viewer.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProposalViewerComponent {
  readonly proposal = input.required<Proposal>();

  protected readonly changedCount = computed(
    () => this.proposal().changes.filter((change) => change.changed).length,
  );
}
