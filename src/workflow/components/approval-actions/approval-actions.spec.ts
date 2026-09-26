import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApprovalActionsComponent } from './approval-actions';

describe('ApprovalActionsComponent', () => {
  let fixture: ComponentFixture<ApprovalActionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ApprovalActionsComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ApprovalActionsComponent);
  });

  it('shows enabled approval controls while approval is available', () => {
    fixture.componentRef.setInput('disabled', false);
    fixture.detectChanges();

    const buttons = fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>;

    expect(buttons.length).toBe(2);
    expect(buttons[0]?.disabled).toBe(false);
    expect(buttons[1]?.disabled).toBe(false);
  });

  it('disables approval controls while an operation is running', () => {
    fixture.componentRef.setInput('disabled', true);
    fixture.componentRef.setInput('loadingMessage', 'Applying changes and running verification...');
    fixture.detectChanges();

    const buttons = fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>;

    expect(fixture.nativeElement.textContent).toContain(
      'Applying changes and running verification...',
    );
    expect(buttons[0]?.disabled).toBe(true);
    expect(buttons[1]?.disabled).toBe(true);
  });
});
