export interface ProposalChange {
  path: string;
  changed: boolean;
  diff: string;
  proposedContent: string;
  originalHash: string;
}

export interface Proposal {
  changes: ProposalChange[];
}
