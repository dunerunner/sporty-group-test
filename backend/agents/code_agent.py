import os

from google import genai
from google.genai import types

from agents.models import AgentResult, AgentStep
from tools.edit_tools import propose_change_set
from tools.file_tools import (
  get_project_structure,
  read_file,
  search_code,
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


SYSTEM_PROMPT = """
You are a senior Angular developer investigating and proposing
changes for an Angular project.

The user's requirement is the source of truth.

You have access to tools that allow you to inspect and test
the project and propose code modifications.

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

10. When investigating a bug or existing failure, use run_tests
    when running the test suite would provide useful evidence.

11. Use test results as evidence. Never claim that tests pass
    or fail unless you actually ran them.

12. Base your diagnosis and proposal on the actual project code.

13. Explain the likely cause or required behavior change.

14. Propose the complete logical change required to satisfy the
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
  expects the previous behavior.

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
  "propose_change_set": propose_change_set,
}


TOOL_DECLARATIONS = [
  types.FunctionDeclaration(
    name="get_project_structure",
    description=(
      "Return a list of files in the Angular project. "
      "Use this when you need to discover which files exist."
    ),
  ),
  types.FunctionDeclaration(
    name="read_file",
    description=(
      "Read the contents of a file from the Angular project."
    ),
    parameters=types.Schema(
      type=types.Type.OBJECT,
      properties={
        "path": types.Schema(
          type=types.Type.STRING,
          description=(
            "Path relative to the project root, for example "
            "'src/app/app.component.ts'."
          ),
        ),
      },
      required=["path"],
    ),
  ),
  types.FunctionDeclaration(
    name="search_code",
    description=(
      "Search for text inside Angular project source files. "
      "Use this to locate implementation code and related "
      "tests before proposing changes."
    ),
    parameters=types.Schema(
      type=types.Type.OBJECT,
      properties={
        "query": types.Schema(
          type=types.Type.STRING,
          description=(
            "Text to search for, for example "
            "'HttpClient', 'subscribe(', 'blue', "
            "'ProductService', or a component name."
          ),
        ),
      },
      required=["query"],
    ),
  ),
  types.FunctionDeclaration(
    name="run_tests",
    description=(
      "Run the Angular project's test suite and return "
      "whether it passed together with the command output."
    ),
  ),
  types.FunctionDeclaration(
    name="propose_change_set",
    description=(
      "Propose modifications to one or more existing project "
      "files as a single logical change set. Include related "
      "test changes when an explicit requirement intentionally "
      "changes behavior covered by those tests. The tool "
      "generates diffs but does not modify files."
    ),
    parameters=types.Schema(
      type=types.Type.OBJECT,
      properties={
        "changes": types.Schema(
          type=types.Type.ARRAY,
          description=(
            "Files that should be changed together."
          ),
          items=types.Schema(
            type=types.Type.OBJECT,
            properties={
              "path": types.Schema(
                type=types.Type.STRING,
                description=(
                  "Path relative to the project root."
                ),
              ),
              "content": types.Schema(
                type=types.Type.STRING,
                description=(
                  "Complete proposed new contents "
                  "of the file."
                ),
              ),
            },
            required=[
              "path",
              "content",
            ],
          ),
        ),
      },
      required=["changes"],
    ),
  ),
]


client = genai.Client(
  api_key=os.getenv("GEMINI_API_KEY")
)


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

  chat = client.chats.create(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
      system_instruction=SYSTEM_PROMPT,
      tools=[
        types.Tool(
          function_declarations=TOOL_DECLARATIONS
        )
      ],
      automatic_function_calling=types.AutomaticFunctionCallingConfig(
        disable=True
      ),
    ),
  )

  response = chat.send_message(prompt)

  for step in range(MAX_AGENT_STEPS):
    print(f"\n🤖 AGENT STEP {step + 1}")

    function_calls = response.function_calls

    if not function_calls:
      print("✅ Agent finished")

      return response.text, steps, proposal_id

    function_responses = []

    for function_call in function_calls:
      name = function_call.name
      arguments = dict(function_call.args)

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

        function_responses.append(
          types.Part.from_function_response(
            name=name,
            response={
              "result": result
            },
          )
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

        function_responses.append(
          types.Part.from_function_response(
            name=name,
            response={
              "error": str(error)
            },
          )
        )

    response = chat.send_message(
      function_responses
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
  test expects the previous behavior.

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
