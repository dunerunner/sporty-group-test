import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';

import { AgentApiService } from './agent-api.service';

describe('AgentApiService', () => {
  let service: AgentApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(AgentApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('sends only workflow_id and proposal_id when applying changes', () => {
    service.applyChange('workflow-1', 'proposal-1').subscribe();

    const request = http.expectOne('http://localhost:8000/apply-change');

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      workflow_id: 'workflow-1',
      proposal_id: 'proposal-1',
    });

    request.flush({
      workflow_id: 'workflow-1',
      proposal_id: 'proposal-1',
      status: 'completed',
      change: { changes: [{ path: 'src/app/app.scss', changed: true }] },
      verification: {
        success: true,
        failed_check: null,
        checks: {
          tests: { success: true, exit_code: 0, stdout: 'ok', stderr: '' },
        },
      },
    });
  });
});
