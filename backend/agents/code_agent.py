import json
import os

from openai import OpenAI

from agents.models import AgentResult, AgentStep
from tools.edit_tools import propose_change_set
from tools.file_tools import (
  get_project_structure,
  read_file,
  search_code,
)
from tools.git_tools import (
  get_git_branch,
  get_git_diff,
  get_git_staged_diff,
  get_git_status,
)
from tools.test_tools import run_tests
from workflows.workflow_store import (
  WorkflowStatus,
  create_workflow,
  get_workflow,
  store_proposal,
  update_workflow,
)


MAX_AGENT_STEPS = 10
DEFAULT_MAX_OUTPUT_TOKENS = 1000


SYSTEM_PROMPT = """
You are a senior Angular developer investigating and proposing
changes for an Angular project.

The user's requirement is the source of truth.

You have access to tools that allow you to inspect the project,
inspect its Git state, run tests, and propose code modifications.

When investigating a requirement:

1. Understand the requested behavior before proposing code.

2. Inspect the project structure when necessary.

3. Use search_code to locate relevant implementation code,
   tests, components, services, styles, templates, imports,
   API usage, RxJS operators, or other related code.

4. Prefer searching before reading many unrelated files.

5. Read the relevant implementation files.

6. Look for tests related to the behavior being changed.

7. Read relevant tests when they exist.

8. Determine whether the requirement:
   - fixes incorrect behavior,
   - introduces new behavior,
   - or intentionally changes existing behavior.

9. Determine whether existing tests remain valid under the
   requested behavior.

10. Inspect Git state when it is relevant to understanding
    existing developer changes.

11. Use get_git_status to determine whether the working tree
    contains uncommitted changes.

12. Use get_git_diff when you need to understand unstaged
    developer changes.

13. Use get_git_staged_diff when staged changes may be relevant.

14. Use get_git_branch when branch context is useful.

15. Treat existing uncommitted developer changes as intentional
    unless there is strong evidence otherwise.

16. Never propose reverting or overwriting unrelated developer
    changes.

17. When investigating a bug or existing failure, use run_tests
    when running the test suite would provide useful evidence.

18. Use test results as evidence. Never claim that tests pass
    or fail unless you actually ran them.

19. Base your diagnosis and proposal on the actual project code.

20. Explain the likely cause or required behavior change.

21. Propose the complete logical change required to satisfy the
    user's requirement.

When you identify a concrete code change, use propose_change_set.

A change set may contain one or more files. Include all files
that logically need to change together.

This can include:

- production code
- templates
- styles
- tests

Existing tests are evidence of previously expected behavior,
but they are not more authoritative than an explicit new user
requirement.

If the user explicitly requests behavior that conflicts with an
existing test, the test may need to be updated to represent the
new behavior.

Before modifying a test:

1. Read the test.
2. Read the production code related to it.
3. Verify that the expectation actually conflicts with the new
   requirement.
4. Preserve the intent and strength of the test while updating
   the outdated expectation.

Never:

- change a test merely because it fails,
- remove a useful assertion just to make tests pass,
- skip or disable a failing test,
- weaken an assertion unnecessarily,
- disable lint rules to make verification pass,
- revert explicitly requested behavior just because an old test
  expects the previous behavior,
- overwrite unrelated uncommitted developer work.

If an existing test exposes an actual implementation bug rather
than an outdated expectation, fix the implementation instead.

Always read every file before proposing changes to it.

Do not claim that a proposed change has been applied.
propose_change_set only generates a proposal.

Do not assume what the project contains.
Inspect it using the available tools.
"""


TOOLS = {
  "get_project_structure": get_project_structure,
  "read_file": read_file,
  "search_code": search_code,
  "run_tests": run_tests,
  "get_git_branch": get_git_branch,
  "get_git_status": get_git_status,
  "get_git_diff": get_git_diff,
  "get_git_staged_diff": get_git_staged_diff,
  "propose_change_set": propose_change_set,
}


def tool_schema(
  name: str,
  description: str,
  parameters: dict | None = None,
) -> dict:
  return {
    "type": "function",
    "function": {
      "name": name,
      "description": description,
      "parameters": parameters
      or {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
      },
    },
  }


TOOL_DECLARATIONS = [
  tool_schema(
    name="get_project_structure",
    description=(
      "Return a list of files in the Angular project. "
      "Use this when you need to discover which files exist."
    ),
  ),
  tool_schema(
    name="read_file",
    description=(
      "Read the contents of a file from the Angular project."
    ),
    parameters={
      "type": "object",
      "properties": {
        "path": {
          "type": "string",
          "description": (
            "Path relative to the project root, for example "
            "'src/app/app.component.ts'."
          ),
        },
      },
      "required": ["path"],
      "additionalProperties": False,
    },
  ),
  tool_schema(
    name="search_code",
    description=(
      "Search for text inside Angular project source files. "
      "Use this to locate implementation code and related "
      "tests before proposing changes."
    ),
    parameters={
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": (
            "Text to search for, for example "
            "'HttpClient', 'subscribe(', 'blue', "
            "'ProductService', or a component name."
          ),
        },
      },
      "required": ["query"],
      "additionalProperties": False,
    },
  ),
  tool_schema(
    name="run_tests",
    description=(
      "Run the Angular project's test suite and return "
      "whether it passed together with the command output."
    ),
  ),
  tool_schema(
    name="get_git_branch",
    description=(
      "Return the currently checked-out Git branch. "
      "This is a read-only operation."
    ),
  ),
  tool_schema(
    name="get_git_status",
    description=(
      "Return the Git working tree status, including "
      "modified, staged, and untracked files. "
      "This is a read-only operation."
    ),
  ),
  tool_schema(
    name="get_git_diff",
    description=(
      "Return the current unstaged Git diff. Use this when "
      "you need to understand existing uncommitted developer "
      "changes. This is a read-only operation."
    ),
  ),
  tool_schema(
    name="get_git_staged_diff",
    description=(
      "Return the currently staged Git diff. Use this when "
      "you need to understand changes already staged by the "
      "developer. This is a read-only operation."
    ),
  ),
  tool_schema(
    name="propose_change_set",
    description=(
      "Propose modifications to one or more existing project "
      "files as a single logical change set. Include related "
      "test changes when an explicit requirement intentionally "
      "changes behavior covered by those tests. The tool "
      "generates diffs but does not modify files."
    ),
    parameters={
      "type": "object",
      "properties": {
        "changes": {
          "type": "array",
          "description": (
            "Files that should be changed together."
          ),
          "items": {
            "type": "object",
            "properties": {
              "path": {
                "type": "string",
                "description": (
                  "Path relative to the project root."
                ),
              },
              "content": {
                "type": "string",
                "description": (
                  "Complete proposed new contents "
                  "of the file."
                ),
              },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
          },
        },
      },
      "required": ["changes"],
      "additionalProperties": False,
    },
  ),
]


client: OpenAI | None = None


def get_client() -> OpenAI:
  global client

  if client is None:
    client = OpenAI(
      api_key=os.getenv("OPENROUTER_API_KEY"),
      base_url="https://openrouter.ai/api/v1",
    )

  return client


def execute_tool(name: str, arguments: dict):
  print(f"🔧 AGENT REQUESTED TOOL: {name}")
  print(f"   Arguments: {arguments}")

  tool = TOOLS.get(name)

  if tool is None:
    raise ValueError(f"Unknown tool: {name}")

  return tool(**arguments)


def run_agent(
  workflow_id: str,
  prompt: str,
) -> tuple[str, list[AgentStep], str | None]:
  steps: list[AgentStep] = []
  proposal_id = None
  model = os.getenv(
    "OPENROUTER_MODEL",
    os.getenv("OPENAI_MODEL", "openai/gpt-4o"),
  )
  max_output_tokens = int(
    os.getenv(
      "OPENROUTER_MAX_TOKENS",
      str(DEFAULT_MAX_OUTPUT_TOKENS),
    )
  )
  messages = [
    {
      "role": "system",
      "content": SYSTEM_PROMPT,
    },
    {
      "role": "user",
      "content": prompt,
    },
  ]

  for step in range(MAX_AGENT_STEPS):
    print(f"\n🤖 AGENT STEP {step + 1}")

    response = get_client().chat.completions.create(
      model=model,
      messages=messages,
      tools=TOOL_DECLARATIONS,
      tool_choice="auto",
      max_tokens=max_output_tokens,
    )

    message = response.choices[0].message
    tool_calls = message.tool_calls

    if not tool_calls:
      print("✅ Agent finished")

      return message.content or "", steps, proposal_id

    messages.append(
      message.model_dump(
        exclude_none=True
      )
    )

    for tool_call in tool_calls:
      name = tool_call.function.name
      arguments = json.loads(
        tool_call.function.arguments or "{}"
      )

      try:
        result = execute_tool(
          name=name,
          arguments=arguments,
        )

        if name == "propose_change_set":
          proposal_id = store_proposal(
            workflow_id=workflow_id,
            changes=result["changes"],
          )

        steps.append(
          AgentStep(
            tool=name,
            arguments=arguments,
            success=True,
            result=result,
          )
        )

        messages.append(
          {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(
              {
                "result": result
              },
              default=str,
            ),
          }
        )

      except Exception as error:
        steps.append(
          AgentStep(
            tool=name,
            arguments=arguments,
            success=False,
            error=str(error),
          )
        )

        messages.append(
          {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(
              {
                "error": str(error)
              }
            ),
          }
        )

  raise RuntimeError(
    f"Agent exceeded maximum of {MAX_AGENT_STEPS} steps"
  )


def run(problem: str) -> AgentResult:
  workflow_id = create_workflow(problem)

  answer, steps, proposal_id = run_agent(
    workflow_id=workflow_id,
    prompt=problem,
  )

  status = (
    WorkflowStatus.AWAITING_APPROVAL
    if proposal_id
    else WorkflowStatus.COMPLETED
  )

  update_workflow(
    workflow_id,
    status=status,
    steps=steps,
    answer=answer,
  )

  return AgentResult(
    workflow_id=workflow_id,
    proposal_id=proposal_id,
    answer=answer,
    steps=steps,
  )


def repair(
  workflow_id: str,
  problem: str,
  verification_result: dict,
) -> AgentResult:
  workflow = get_workflow(workflow_id)

  failed_check = verification_result[
    "failed_check"
  ]

  failed_result = verification_result[
    "checks"
  ][failed_check]

  previous_change = workflow.get(
    "change_result"
  )

  repair_prompt = f"""
The previous approved change was applied, but project
verification failed.

Original user requirement:
{problem}

The original user requirement remains the source of truth.

Previous applied change result:
{previous_change}

Failed verification check:
{failed_check}

Exit code:
{failed_result["exit_code"]}

STDOUT:
{failed_result["stdout"]}

STDERR:
{failed_result["stderr"]}

The project currently contains the previously applied changes.

Investigate the failure using the available tools.

Inspect the current Git state when it helps distinguish the
agent's changes from unrelated developer changes.

Do not overwrite or revert unrelated developer work.

Do not assume that a verification failure means the requested
behavior should be reverted.

First determine why verification failed.

If tests failed, classify the failure as one of these cases:

1. IMPLEMENTATION BUG

   The implementation does not correctly satisfy the original
   user requirement.

   Fix the production implementation.

2. OUTDATED TEST

   The implementation correctly satisfies the new requirement,
   but an existing test still represents the previous behavior.

   Update the test so that it accurately verifies the newly
   requested behavior.

3. BOTH

   The implementation and the test both require changes.

4. UNRELATED FAILURE

   The failing test is unrelated to the requested change.

   Do not modify unrelated production code or weaken unrelated
   tests merely to make verification pass. Explain the unrelated
   failure instead.

If lint failed:

- identify the actual lint violation,
- preserve the requested behavior,
- fix the implementation rather than disabling the rule.

If the build failed:

- identify the actual compilation, type-checking, dependency,
  template, or build configuration problem,
- preserve the requested behavior,
- correct the underlying problem.

Before changing any test:

1. Read the relevant test.
2. Read the related production code.
3. Compare both with the original user requirement.
4. Verify that the expectation is genuinely outdated.
5. Preserve meaningful assertions and coverage.

Never:

- modify a test solely because it failed,
- remove useful assertions,
- skip or disable tests,
- weaken tests unnecessarily,
- disable lint rules to hide violations,
- bypass build checks,
- revert explicitly requested behavior solely because an old
  test expects the previous behavior,
- overwrite unrelated developer changes.

Use propose_change_set to propose all related changes together.

Always read every file before proposing changes to it.

Do not claim that the proposed repair has been applied.
"""

  answer, steps, proposal_id = run_agent(
    workflow_id=workflow_id,
    prompt=repair_prompt,
  )

  status = (
    WorkflowStatus.AWAITING_APPROVAL
    if proposal_id
    else WorkflowStatus.VERIFICATION_FAILED
  )

  update_workflow(
    workflow_id,
    status=status,
    repair_steps=steps,
    repair_answer=answer,
  )

  return AgentResult(
    workflow_id=workflow_id,
    proposal_id=proposal_id,
    answer=answer,
    steps=steps,
  )
