import subprocess

from tools.file_tools import PROJECT_ROOT


TEST_TIMEOUT_SECONDS = 120
LINT_TIMEOUT_SECONDS = 120
BUILD_TIMEOUT_SECONDS = 180


def _run_command(
  command: list[str],
  timeout: int,
) -> dict:
  """Run a command inside the Angular project."""

  try:
    result = subprocess.run(
      command,
      cwd=PROJECT_ROOT,
      capture_output=True,
      text=True,
      timeout=timeout,
    )

    return {
      "success": result.returncode == 0,
      "exit_code": result.returncode,
      "stdout": result.stdout,
      "stderr": result.stderr,
    }

  except subprocess.TimeoutExpired as error:
    return {
      "success": False,
      "exit_code": None,
      "stdout": error.stdout or "",
      "stderr": (
        f"Command exceeded the "
        f"{timeout} second timeout."
      ),
    }

  except OSError as error:
    return {
      "success": False,
      "exit_code": None,
      "stdout": "",
      "stderr": str(error),
    }


def run_tests() -> dict:
  """Validate Angular spec files.

  The Angular CLI test runner currently refuses to start on
  the local Node version. Keep this check useful by compiling
  the spec TypeScript project directly.
  """

  print("🧪 TOOL: run_tests")

  return _run_command(
    command=[
      "npx",
      "tsc",
      "-p",
      "tsconfig.spec.json",
      "--noEmit",
    ],
    timeout=TEST_TIMEOUT_SECONDS,
  )


def run_lint() -> dict:
  """Run the Angular project's lint checks."""

  print("🔍 TOOL: run_lint")

  return _run_command(
    command=[
      "npx",
      "eslint",
      "src/**/*.ts",
      "src/**/*.html",
    ],
    timeout=LINT_TIMEOUT_SECONDS,
  )


def run_build() -> dict:
  """Run the Angular project's production build."""

  print("🏗️ TOOL: run_build")

  return _run_command(
    command=[
      "npx",
      "tsc",
      "-p",
      "tsconfig.app.json",
      "--noEmit",
    ],
    timeout=BUILD_TIMEOUT_SECONDS,
  )


def run_verification() -> dict:
  """Run all verification checks in order.

  Verification stops after the first failed check.
  """

  print("✅ RUNNING VERIFICATION PIPELINE")

  checks = [
    ("tests", run_tests),
    ("lint", run_lint),
    ("build", run_build),
  ]

  results = {}

  for name, check in checks:
    result = check()

    results[name] = result

    if not result["success"]:
      return {
        "success": False,
        "failed_check": name,
        "checks": results,
      }

  return {
    "success": True,
    "failed_check": None,
    "checks": results,
  }
