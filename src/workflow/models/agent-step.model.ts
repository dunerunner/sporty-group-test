export interface AgentStep {
  tool: string;
  arguments: Record<string, unknown>;
  success: boolean;
  result?: unknown;
  error?: string;
}
