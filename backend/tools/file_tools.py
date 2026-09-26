from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MAX_SEARCH_RESULTS = 50
MAX_SEARCH_QUERY_LENGTH = 200
MAX_READ_FILE_BYTES = 200_000
MAX_SEARCH_FILE_BYTES = 200_000
MAX_TEXT_RESULT_CHARS = 200_000


IGNORED_DIRECTORIES = {
  "node_modules",
  ".git",
  ".angular",
  "dist",
  ".venv",
  "backend",
}


def _validate_relative_path(path: str) -> Path:
  if not path or Path(path).is_absolute():
    raise ValueError("Path must be relative to the project")

  file_path = (PROJECT_ROOT / path).resolve()

  if not file_path.is_relative_to(PROJECT_ROOT):
    raise ValueError("Cannot access files outside the project")

  return file_path


def get_project_structure() -> list[str]:
  """Return a list of files in the Angular project.

  Use this tool when you need to discover which files exist
  or locate files relevant to a user's question.
  """

  print("🔧 TOOL: get_project_structure")

  files = []

  for path in PROJECT_ROOT.rglob("*"):
    if any(part in IGNORED_DIRECTORIES for part in path.parts):
      continue

    if path.is_file():
      files.append(str(path.relative_to(PROJECT_ROOT)))

  return files


def read_file(path: str) -> str:
  """Read a file from the Angular project.

  Args:
      path: Path relative to the Angular project root,
            for example 'src/app/app.component.ts'.
  """

  print(f"🔧 TOOL: read_file({path})")

  file_path = _validate_relative_path(path)

  if not file_path.exists():
    raise FileNotFoundError(path)

  if not file_path.is_file():
    raise ValueError(f"Not a file: {path}")

  if file_path.stat().st_size > MAX_READ_FILE_BYTES:
    raise ValueError(
      f"File is too large to read: {path}"
    )

  content = file_path.read_text(encoding="utf-8")

  if len(content) > MAX_TEXT_RESULT_CHARS:
    return content[:MAX_TEXT_RESULT_CHARS]

  return content


def search_code(query: str) -> list[dict]:
  """Search for text inside project source files.

  Args:
      query: Text to search for, for example
             'HttpClient', 'subscribe(', or 'ProductService'.
  """

  print(f"🔧 TOOL: search_code({query})")

  if not query or len(query) > MAX_SEARCH_QUERY_LENGTH:
    raise ValueError(
      "Search query must be between 1 and "
      f"{MAX_SEARCH_QUERY_LENGTH} characters."
    )

  allowed_extensions = {
    ".ts",
    ".html",
    ".scss",
    ".css",
    ".json",
  }

  matches = []

  for path in PROJECT_ROOT.rglob("*"):
    if any(part in IGNORED_DIRECTORIES for part in path.parts):
      continue

    if not path.is_file():
      continue

    if path.suffix not in allowed_extensions:
      continue

    if path.stat().st_size > MAX_SEARCH_FILE_BYTES:
      continue

    try:
      content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
      continue

    for line_number, line in enumerate(
      content.splitlines(),
      start=1,
    ):
      if query.lower() in line.lower():
        matches.append(
          {
            "path": str(
              path.relative_to(PROJECT_ROOT)
            ),
            "line": line_number,
            "content": line.strip(),
          }
        )

        if len(matches) >= MAX_SEARCH_RESULTS:
          return matches

  return matches
