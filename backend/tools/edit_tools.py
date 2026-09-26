import difflib
import hashlib

from tools.file_tools import PROJECT_ROOT


def _resolve_project_file(path: str):
  file_path = (PROJECT_ROOT / path).resolve()

  if not file_path.is_relative_to(PROJECT_ROOT):
    raise ValueError(
      "Cannot modify files outside the project"
    )

  if not file_path.exists():
    raise FileNotFoundError(path)

  if not file_path.is_file():
    raise ValueError(f"Not a file: {path}")

  return file_path


def _content_hash(content: str) -> str:
  return hashlib.sha256(
    content.encode("utf-8")
  ).hexdigest()


def propose_change_set(
  changes: list[dict],
) -> dict:
  """Propose changes to one or more existing project files.

  This function does not modify any files. It returns diffs
  showing the proposed changes together with hashes of the
  original file contents.
  """

  print(
    f"✏️ TOOL: propose_change_set("
    f"{len(changes)} file(s))"
  )

  proposed_changes = []

  for change in changes:
    path = change["path"]
    content = change["content"]

    file_path = _resolve_project_file(path)

    old_content = file_path.read_text(
      encoding="utf-8"
    )

    diff = difflib.unified_diff(
      old_content.splitlines(),
      content.splitlines(),
      fromfile=f"a/{path}",
      tofile=f"b/{path}",
      lineterm="",
    )

    diff_text = "\n".join(diff)

    print(f"\n📄 PROPOSED DIFF: {path}")
    print(diff_text)

    proposed_changes.append(
      {
        "path": path,
        "changed": old_content != content,
        "diff": diff_text,
        "proposed_content": content,
        "original_hash": _content_hash(
          old_content
        ),
      }
    )

  return {
    "changes": proposed_changes,
  }


def apply_change_set(
  changes: list[dict],
) -> dict:
  """Apply an approved change set.

  All files are validated before any file is written.

  If writing any file fails, previously written files are
  restored to their original contents.
  """

  print(
    f"💾 APPLYING CHANGE SET "
    f"({len(changes)} file(s))"
  )

  prepared_changes = []

  # Phase 1: validate everything before writing anything.
  for change in changes:
    path = change["path"]

    file_path = _resolve_project_file(path)

    current_content = file_path.read_text(
      encoding="utf-8"
    )

    current_hash = _content_hash(
      current_content
    )

    if current_hash != change["original_hash"]:
      raise ValueError(
        f"File changed after proposal "
        f"was created: {path}"
      )

    prepared_changes.append(
      {
        "path": path,
        "file_path": file_path,
        "original_content": current_content,
        "proposed_content": (
          change["proposed_content"]
        ),
      }
    )

  # Phase 2: write the complete change set.
  written_changes = []

  try:
    for change in prepared_changes:
      path = change["path"]
      file_path = change["file_path"]
      original_content = (
        change["original_content"]
      )
      proposed_content = (
        change["proposed_content"]
      )

      if original_content == proposed_content:
        written_changes.append(
          {
            "path": path,
            "changed": False,
          }
        )
        continue

      file_path.write_text(
        proposed_content,
        encoding="utf-8",
      )

      written_changes.append(
        {
          "path": path,
          "changed": True,
        }
      )

  except Exception as error:
    print(
      "❌ Change set failed. "
      "Rolling back modified files."
    )

    rollback_errors = []

    for change in prepared_changes:
      try:
        change["file_path"].write_text(
          change["original_content"],
          encoding="utf-8",
        )
      except Exception as rollback_error:
        rollback_errors.append(
          {
            "path": change["path"],
            "error": str(rollback_error),
          }
        )

    if rollback_errors:
      raise RuntimeError(
        "Change set failed and rollback was "
        f"incomplete. Original error: {error}. "
        f"Rollback errors: {rollback_errors}"
      ) from error

    raise RuntimeError(
      "Change set failed. All modified files "
      f"were rolled back. Error: {error}"
    ) from error

  return {
    "changes": written_changes,
  }
