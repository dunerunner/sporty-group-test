import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VerificationResultsComponent } from './verification-results';

describe('VerificationResultsComponent', () => {
  let fixture: ComponentFixture<VerificationResultsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VerificationResultsComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(VerificationResultsComponent);
    fixture.componentRef.setInput('verification', {
      success: false,
      failedCheck: 'lint',
      checks: {
        tests: { success: true, exitCode: 0, stdout: 'ok', stderr: '' },
        lint: { success: false, exitCode: 1, stdout: '', stderr: 'lint failed' },
      },
    });
  });

  it('shows repair control only after verification failure', () => {
    fixture.componentRef.setInput('status', 'verification_failed');
    fixture.componentRef.setInput('canRepair', true);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement | null;

    expect(button?.textContent).toContain('Ask agent to repair');
    expect(button?.disabled).toBe(false);
  });

  it('does not show repair control for completed verification', () => {
    fixture.componentRef.setInput('status', 'completed');
    fixture.componentRef.setInput('canRepair', false);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement | null;

    expect(button).toBeNull();
  });
});
