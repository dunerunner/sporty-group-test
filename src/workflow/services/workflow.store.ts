import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { finalize } from 'rxjs';

import { AgentStep } from '../models/agent-step.model';
import { Proposal } from '../models/proposal.model';
import { WorkflowError, WorkflowState } from '../models/workflow.model';
import { AgentApiService } from './agent-api.service';

const initialState: WorkflowState = {
  workflowId: null,
  proposalId: null,
  problem: '',
  status: null,
  answer: null,
  steps: [],
  proposal: null,
  verification: null,
  loading: false,
  loadingMessage: null,
  error: null,
};

interface ProposalStepResult {
  changes: ProposalChangeDto[];
}

interface ProposalChangeDto {
  path: string;
  changed: boolean;
  diff: string;
  proposed_content: string;
  original_hash: string;
}

@Injectable({ providedIn: 'root' })
export class WorkflowStore {
  private readonly api = inject(AgentApiService);
  private readonly stateSignal = signal<WorkflowState>(initialState);

  readonly state = this.stateSignal.asReadonly();
  readonly canAnalyze = computed(() => {
    const state = this.state();
    return Boolean(state.problem.trim()) && !state.loading;
  });
  readonly canApprove = computed(() => {
    const state = this.state();
    return state.status === 'awaiting_approval' && Boolean(state.workflowId && state.proposalId) && !state.loading;
  });
  readonly canRepair = computed(() => {
    const state = this.state();
    return state.status === 'verification_failed' && Boolean(state.workflowId) && !state.loading;
  });

  updateProblem(problem: string): void {
    this.patchState({ problem, error: null });
  }

  analyze(): void {
    const problem = this.state().problem.trim();
    if (!problem || this.state().loading) {
      return;
    }

    this.stateSignal.set({
      ...initialState,
      problem,
      status: 'analyzing',
      loading: true,
      loadingMessage: 'Analyzing repository...',
    });

    this.api
      .analyze(problem)
      .pipe(finalize(() => this.patchState({ loading: false, loadingMessage: null })))
      .subscribe({
        next: (result) => {
          this.patchState({
            workflowId: result.workflowId,
            proposalId: result.proposalId,
            answer: result.answer,
            steps: result.steps,
            proposal: extractProposal(result.steps),
            status: result.proposalId ? 'awaiting_approval' : 'completed',
            error: null,
          });
        },
        error: (error: HttpErrorResponse) => {
          this.patchState({
            status: null,
            error: this.mapError(error),
          });
        },
      });
  }

  approve(): void {
    const { workflowId, proposalId, loading } = this.state();
    if (!workflowId || !proposalId || loading) {
      return;
    }

    this.patchState({
      status: 'applying',
      loading: true,
      loadingMessage: 'Applying changes and running verification...',
      error: null,
    });

    this.api
      .applyChange(workflowId, proposalId)
      .pipe(finalize(() => this.patchState({ loading: false, loadingMessage: null })))
      .subscribe({
        next: (response) => {
          this.patchState({
            workflowId: response.workflowId,
            proposalId: response.proposalId,
            status: response.status,
            verification: response.verification,
            error: null,
          });
        },
        error: (error: HttpErrorResponse) => {
          const mapped = this.mapError(error);
          const status = error.status === 409 ? 'proposal_stale' : 'apply_failed';
          this.patchState({ status, error: mapped });
        },
      });
  }

  reject(): void {
    const { workflowId, proposalId, loading } = this.state();
    if (!workflowId || !proposalId || loading) {
      return;
    }

    this.patchState({
      loading: true,
      loadingMessage: 'Rejecting proposal...',
      error: null,
    });

    this.api
      .rejectChange(workflowId, proposalId)
      .pipe(finalize(() => this.patchState({ loading: false, loadingMessage: null })))
      .subscribe({
        next: (response) => {
          this.patchState({
            workflowId: response.workflowId,
            proposalId: response.proposalId,
            status: 'rejected',
            verification: null,
            error: null,
          });
        },
        error: (error: HttpErrorResponse) => {
          this.patchState({ error: this.mapError(error) });
        },
      });
  }

  repair(): void {
    const { workflowId, loading } = this.state();
    if (!workflowId || loading) {
      return;
    }

    this.patchState({
      loading: true,
      loadingMessage: 'Investigating verification failure...',
      error: null,
    });

    this.api
      .repair(workflowId)
      .pipe(finalize(() => this.patchState({ loading: false, loadingMessage: null })))
      .subscribe({
        next: (result) => {
          this.patchState({
            workflowId: result.workflowId,
            proposalId: result.proposalId,
            answer: result.answer,
            steps: result.steps,
            proposal: extractProposal(result.steps),
            verification: null,
            status: result.proposalId ? 'awaiting_approval' : 'repair_limit_reached',
            error: null,
          });
        },
        error: (error: HttpErrorResponse) => {
          const mapped = this.mapError(error);
          this.patchState({
            status: error.status === 409 ? 'repair_limit_reached' : this.state().status,
            error: mapped,
          });
        },
      });
  }

  reset(): void {
    this.stateSignal.set(initialState);
  }

  private patchState(patch: Partial<WorkflowState>): void {
    this.stateSignal.update((state) => ({ ...state, ...patch }));
  }

  private mapError(error: HttpErrorResponse): WorkflowError {
    const detail = this.extractDetail(error);

    if (error.status === 0) {
      return {
        title: 'Backend unavailable',
        message: 'The frontend could not reach the backend service.',
        detail,
        statusCode: null,
      };
    }

    const messages: Record<number, { title: string; message: string }> = {
      400: {
        title: 'Invalid workflow operation',
        message: 'The backend rejected this workflow operation.',
      },
      404: {
        title: 'Workflow or proposal not found',
        message: 'The referenced workflow or proposal no longer exists.',
      },
      409: {
        title: 'Workflow conflict',
        message: 'The backend reported a conflict for the current workflow state.',
      },
      500: {
        title: 'Backend failure',
        message: 'The backend failed while processing this request.',
      },
    };
    const mapped = messages[error.status] ?? {
      title: 'Request failed',
      message: 'The backend returned an unexpected error.',
    };

    return {
      ...mapped,
      detail,
      statusCode: error.status,
    };
  }

  private extractDetail(error: HttpErrorResponse): string | null {
    const payload = error.error as { detail?: unknown } | string | null;
    if (typeof payload === 'string') {
      return payload;
    }
    if (payload && typeof payload.detail === 'string') {
      return payload.detail;
    }
    if (payload && payload.detail !== undefined) {
      return JSON.stringify(payload.detail);
    }

    return error.message || null;
  }
}

export function extractProposal(steps: AgentStep[]): Proposal | null {
  const proposalStep = steps.find((step) => step.tool === 'propose_change_set' && step.success);
  if (!proposalStep || !isProposalStepResult(proposalStep.result)) {
    return null;
  }

  return {
    changes: proposalStep.result.changes.map((change) => ({
      path: change.path,
      changed: change.changed,
      diff: change.diff,
      proposedContent: change.proposed_content,
      originalHash: change.original_hash,
    })),
  };
}

function isProposalStepResult(result: unknown): result is ProposalStepResult {
  if (!result || typeof result !== 'object' || !('changes' in result)) {
    return false;
  }

  const changes = (result as { changes: unknown }).changes;
  return Array.isArray(changes) && changes.every(isProposalChangeDto);
}

function isProposalChangeDto(change: unknown): change is ProposalChangeDto {
  if (!change || typeof change !== 'object') {
    return false;
  }

  const candidate = change as Record<string, unknown>;
  return (
    typeof candidate['path'] === 'string' &&
    typeof candidate['changed'] === 'boolean' &&
    typeof candidate['diff'] === 'string' &&
    typeof candidate['proposed_content'] === 'string' &&
    typeof candidate['original_hash'] === 'string'
  );
}
