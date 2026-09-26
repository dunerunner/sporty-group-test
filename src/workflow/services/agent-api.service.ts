import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { AgentStep } from '../models/agent-step.model';
import { VerificationResult } from '../models/verification.model';
import {
  AgentResult,
  ApplyChangeResponse,
  RejectChangeResponse,
  WorkflowStatus,
} from '../models/workflow.model';

interface AgentResultDto {
  workflow_id: string;
  proposal_id: string | null;
  answer: string;
  steps: AgentStep[];
}

interface CommandResultDto {
  success: boolean;
  exit_code: number | null;
  stdout: string;
  stderr: string;
}

interface VerificationResultDto {
  success: boolean;
  failed_check: 'tests' | 'lint' | 'build' | null;
  checks: {
    tests?: CommandResultDto;
    lint?: CommandResultDto;
    build?: CommandResultDto;
  };
}

interface ApplyChangeResponseDto {
  workflow_id: string;
  proposal_id: string;
  status: WorkflowStatus;
  change: {
    changes: {
      path: string;
      changed: boolean;
    }[];
  };
  verification: VerificationResultDto;
}

interface RejectChangeResponseDto {
  workflow_id: string;
  proposal_id: string;
  status: 'rejected';
}

@Injectable({ providedIn: 'root' })
export class AgentApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000';

  analyze(problem: string): Observable<AgentResult> {
    return this.http
      .post<AgentResultDto>(`${this.baseUrl}/analyze`, { problem })
      .pipe(map((response) => this.mapAgentResult(response)));
  }

  applyChange(workflowId: string, proposalId: string): Observable<ApplyChangeResponse> {
    return this.http
      .post<ApplyChangeResponseDto>(`${this.baseUrl}/apply-change`, {
        workflow_id: workflowId,
        proposal_id: proposalId,
      })
      .pipe(map((response) => this.mapApplyChangeResponse(response)));
  }

  rejectChange(workflowId: string, proposalId: string): Observable<RejectChangeResponse> {
    return this.http
      .post<RejectChangeResponseDto>(`${this.baseUrl}/reject-change`, {
        workflow_id: workflowId,
        proposal_id: proposalId,
      })
      .pipe(
        map((response) => ({
          workflowId: response.workflow_id,
          proposalId: response.proposal_id,
          status: response.status,
        })),
      );
  }

  repair(workflowId: string): Observable<AgentResult> {
    return this.http
      .request<AgentResultDto>('POST', `${this.baseUrl}/repair/${encodeURIComponent(workflowId)}`)
      .pipe(map((response) => this.mapAgentResult(response)));
  }

  private mapAgentResult(response: AgentResultDto): AgentResult {
    return {
      workflowId: response.workflow_id,
      proposalId: response.proposal_id,
      answer: response.answer,
      steps: response.steps,
    };
  }

  private mapApplyChangeResponse(response: ApplyChangeResponseDto): ApplyChangeResponse {
    return {
      workflowId: response.workflow_id,
      proposalId: response.proposal_id,
      status: response.status,
      change: response.change,
      verification: this.mapVerification(response.verification),
    };
  }

  private mapVerification(response: VerificationResultDto): VerificationResult {
    return {
      success: response.success,
      failedCheck: response.failed_check,
      checks: {
        tests: response.checks.tests ? this.mapCommandResult(response.checks.tests) : undefined,
        lint: response.checks.lint ? this.mapCommandResult(response.checks.lint) : undefined,
        build: response.checks.build ? this.mapCommandResult(response.checks.build) : undefined,
      },
    };
  }

  private mapCommandResult(response: CommandResultDto) {
    return {
      success: response.success,
      exitCode: response.exit_code,
      stdout: response.stdout,
      stderr: response.stderr,
    };
  }
}
