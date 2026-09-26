import subprocess

from tools.file_tools import PROJECT_ROOT


GIT_TIMEOUT_SECONDS = 30
MAX_GIT_OUTPUT_CHARS = 200_000


def _run_git_command(
  arguments: list[str],
) -> str:
  """Run an allowed read-only Git command."""

  try:
    result = subprocess.run(
      ["git", *arguments],
      cwd=PROJECT_ROOT,
      capture_output=True,
      text=True,
      timeout=GIT_TIMEOUT_SECONDS,
    )

  except subprocess.TimeoutExpired as error:
    raise RuntimeError(
      "Git command exceeded the "
      f"{GIT_TIMEOUT_SECONDS} second timeout."
    ) from error

  except OSError as error:
    raise RuntimeError(
      f"Could not execute Git: {error}"
    ) from error

  if result.returncode != 0:
    raise RuntimeError(
      result.stderr.strip()
      or "Git command failed."
    )

  if len(result.stdout) > MAX_GIT_OUTPUT_CHARS:
    return (
      result.stdout[:MAX_GIT_OUTPUT_CHARS]
      + "\n\n[output truncated]"
    )

  return result.stdout


def get_git_branch() -> dict:
  """Return the currently checked-out Git branch."""

  print("🌿 TOOL: get_git_branch")

  branch = _run_git_command(
    ["branch", "--show-current"]
  ).strip()

  return {
    "branch": branch or None,
  }


def get_git_status() -> dict:
  """Return the working tree status."""

  print("🌿 TOOL: get_git_status")

  output = _run_git_command(
    ["status", "--short"]
  )

  files = [
    line
    for line in output.splitlines()
    if line.strip()
  ]

  return {
    "clean": len(files) == 0,
    "files": files,
  }


def get_git_diff() -> dict:
  """Return unstaged changes in the working tree."""

  print("🌿 TOOL: get_git_diff")

  diff = _run_git_command(
    ["diff", "--no-ext-diff"]
  )

  return {
    "diff": diff,
  }


def get_git_staged_diff() -> dict:
  """Return changes currently staged for commit."""

  print("🌿 TOOL: get_git_staged_diff")

  diff = _run_git_command(
    [
      "diff",
      "--cached",
      "--no-ext-diff",
    ]
  )

  return {
    "diff": diff,
  }
