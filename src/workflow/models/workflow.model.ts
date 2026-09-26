import { AgentStep } from './agent-step.model';
import { Proposal } from './proposal.model';
import { VerificationResult } from './verification.model';

export type WorkflowStatus =
  | 'analyzing'
  | 'awaiting_approval'
  | 'applying'
  | 'verifying'
  | 'verification_failed'
  | 'completed'
  | 'rejected'
  | 'proposal_stale'
  | 'apply_failed'
  | 'repair_limit_reached';

export interface AgentResult {
  workflowId: string;
  proposalId: string | null;
  answer: string;
  steps: AgentStep[];
}

export interface ApplyChangeResponse {
  workflowId: string;
  proposalId: string;
  status: WorkflowStatus;
  change: {
    changes: {
      path: string;
      changed: boolean;
    }[];
  };
  verification: VerificationResult;
}

export interface RejectChangeResponse {
  workflowId: string;
  proposalId: string;
  status: 'rejected';
}

export interface WorkflowState {
  workflowId: string | null;
  proposalId: string | null;
  problem: string;
  status: WorkflowStatus | null;
  answer: string | null;
  steps: AgentStep[];
  proposal: Proposal | null;
  verification: VerificationResult | null;
  loading: boolean;
  loadingMessage: string | null;
  error: WorkflowError | null;
}

export interface WorkflowError {
  title: string;
  message: string;
  detail: string | null;
  statusCode: number | null;
}

export const workflowStatusLabels: Record<WorkflowStatus, string> = {
  analyzing: 'Analyzing task',
  awaiting_approval: 'Awaiting approval',
  applying: 'Applying changes',
  verifying: 'Running verification',
  verification_failed: 'Verification failed',
  completed: 'Completed',
  rejected: 'Changes rejected',
  proposal_stale: 'Proposal is stale',
  apply_failed: 'Failed to apply changes',
  repair_limit_reached: 'Repair limit reached',
};
