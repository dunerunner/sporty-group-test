import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AgentResult, ApplyChangeResponse } from '../models/workflow.model';
import { AgentApiService } from './agent-api.service';
import { WorkflowStore, extractProposal } from './workflow.store';

const analyzeResult: AgentResult = {
  workflowId: 'workflow-1',
  proposalId: 'proposal-1',
  answer: 'Change the button color and related expectation.',
  steps: [
    {
      tool: 'search_code',
      arguments: { query: 'submit' },
      success: true,
      result: [],
    },
    {
      tool: 'propose_change_set',
      arguments: {},
      success: true,
      result: {
        changes: [
          {
            path: 'src/app/button/button.component.scss',
            changed: true,
            diff: '- background: blue;\n+ background: green;',
            proposed_content: 'background: green;',
            original_hash: 'abc123',
          },
        ],
      },
    },
  ],
};

const successfulApplyResponse: ApplyChangeResponse = {
  workflowId: 'workflow-1',
  proposalId: 'proposal-1',
  status: 'completed',
  change: { changes: [{ path: 'src/app/button/button.component.scss', changed: true }] },
  verification: {
    success: true,
    failedCheck: null,
    checks: {
      tests: { success: true, exitCode: 0, stdout: 'tests passed', stderr: '' },
      lint: { success: true, exitCode: 0, stdout: 'lint passed', stderr: '' },
      build: { success: true, exitCode: 0, stdout: 'build passed', stderr: '' },
    },
  },
};

describe('WorkflowStore', () => {
  let store: WorkflowStore;
  let api: {
    analyze: ReturnType<typeof vi.fn>;
    applyChange: ReturnType<typeof vi.fn>;
    rejectChange: ReturnType<typeof vi.fn>;
    repair: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    api = {
      analyze: vi.fn(() => of(analyzeResult)),
      applyChange: vi.fn(() => of(successfulApplyResponse)),
      rejectChange: vi.fn(() =>
        of({ workflowId: 'workflow-1', proposalId: 'proposal-1', status: 'rejected' }),
      ),
      repair: vi.fn(() =>
        of({
          ...analyzeResult,
          proposalId: 'proposal-2',
          answer: 'Repair the lint failure.',
        }),
      ),
    };

    TestBed.configureTestingModule({
      providers: [{ provide: AgentApiService, useValue: api }],
    });

    store = TestBed.inject(WorkflowStore);
  });

  it('creates workflow state from an analyze response', () => {
    store.updateProblem('Change the submit button background from blue to green.');
    store.analyze();

    expect(api.analyze).toHaveBeenCalledWith(
      'Change the submit button background from blue to green.',
    );
    expect(store.state().workflowId).toBe('workflow-1');
    expect(store.state().proposalId).toBe('proposal-1');
    expect(store.state().status).toBe('awaiting_approval');
    expect(store.state().answer).toContain('button color');
  });

  it('extracts proposal changes from the propose_change_set step', () => {
    const proposal = extractProposal(analyzeResult.steps);

    expect(proposal?.changes).toEqual([
      {
        path: 'src/app/button/button.component.scss',
        changed: true,
        diff: '- background: blue;\n+ background: green;',
        proposedContent: 'background: green;',
        originalHash: 'abc123',
      },
    ]);
  });

  it('stores verification results after approval', () => {
    store.updateProblem('Change the button.');
    store.analyze();
    store.approve();

    expect(api.applyChange).toHaveBeenCalledWith('workflow-1', 'proposal-1');
    expect(store.state().status).toBe('completed');
    expect(store.state().verification?.checks.tests?.stdout).toBe('tests passed');
  });

  it('updates state after rejection', () => {
    store.updateProblem('Change the button.');
    store.analyze();
    store.reject();

    expect(api.rejectChange).toHaveBeenCalledWith('workflow-1', 'proposal-1');
    expect(store.state().status).toBe('rejected');
  });

  it('replaces the current proposal id after repair', () => {
    api.applyChange.mockReturnValueOnce(
      of({
        ...successfulApplyResponse,
        status: 'verification_failed',
        verification: {
          success: false,
          failedCheck: 'lint',
          checks: {
            tests: { success: true, exitCode: 0, stdout: 'ok', stderr: '' },
            lint: { success: false, exitCode: 1, stdout: '', stderr: 'lint failed' },
          },
        },
      }),
    );

    store.updateProblem('Change the button.');
    store.analyze();
    store.approve();
    store.repair();

    expect(api.repair).toHaveBeenCalledWith('workflow-1');
    expect(store.state().proposalId).toBe('proposal-2');
    expect(store.state().status).toBe('awaiting_approval');
    expect(store.state().answer).toBe('Repair the lint failure.');
  });
});
