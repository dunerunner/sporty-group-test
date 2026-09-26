export type VerificationCheckName = 'tests' | 'lint' | 'build';

export interface CommandResult {
  success: boolean;
  exitCode: number | null;
  stdout: string;
  stderr: string;
}

export interface VerificationResult {
  success: boolean;
  failedCheck: VerificationCheckName | null;
  checks: Partial<Record<VerificationCheckName, CommandResult>>;
}
