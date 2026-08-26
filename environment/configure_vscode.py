"""Configure a Tea analysis workspace for VS Code without replacing user settings."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


def vscode_is_available() -> bool:
  if os.environ.get("TERM_PROGRAM") == "vscode" or os.environ.get("VSCODE_IPC_HOOK_CLI"):
    return True
  if shutil.which("code") or shutil.which("code-insiders") or shutil.which("codium"):
    return True

  home = Path.home()
  candidates = [
    Path("/Applications/Visual Studio Code.app"),
    home / "Applications/Visual Studio Code.app",
    home / ".vscode-server",
    home / ".vscode-server-insiders",
  ]
  return any(candidate.exists() for candidate in candidates)


def read_json_object(path: Path) -> dict[str, Any]:
  if not path.exists():
    return {}
  try:
    contents = json.loads(path.read_text(encoding="utf-8"))
  except json.JSONDecodeError as error:
    raise ValueError(f"{path} contains JSON comments or invalid JSON; Tea left it unchanged ({error})") from error
  if not isinstance(contents, dict):
    raise TypeError(f"{path} must contain a JSON object; Tea left it unchanged")
  return contents


def write_json_if_changed(path: Path, contents: dict[str, Any]) -> bool:
  rendered = json.dumps(contents, indent=2, ensure_ascii=False) + "\n"
  if path.exists() and path.read_text(encoding="utf-8") == rendered:
    return False

  path.parent.mkdir(parents=True, exist_ok=True)
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
  temporary_path = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(rendered)
    temporary_path.replace(path)
  finally:
    temporary_path.unlink(missing_ok=True)
  return True


def append_unique(values: Any, additions: list[str]) -> list[str]:
  result = list(values) if isinstance(values, list) else []
  for addition in additions:
    if addition not in result:
      result.append(addition)
  return result


def materialize_template(value: Any, replacements: dict[str, str]) -> Any:
  if isinstance(value, dict):
    return {key: materialize_template(item, replacements) for key, item in value.items()}
  if isinstance(value, list):
    return [materialize_template(item, replacements) for item in value]
  if isinstance(value, str):
    for placeholder, replacement in replacements.items():
      value = value.replace(placeholder, replacement)
  return value


def merge_settings(settings: dict[str, Any], generated: dict[str, Any]) -> None:
  for key, value in generated.items():
    if key == "[python]" and isinstance(value, dict):
      python_settings = settings.get(key, {})
      if not isinstance(python_settings, dict):
        raise TypeError("[python] must be a JSON object")
      python_settings.update(value)
      settings[key] = python_settings
    else:
      settings[key] = value


def configure_workspace(workspace: Path, framework: Path, environment: Path) -> bool:
  python = environment / "bin/python"
  ruff = environment / "bin/ruff"
  clang_format = environment / "bin/clang-format"
  ruff_configuration = framework / "ruff.toml"
  template_directory = framework / "templates/.vscode"
  settings_template_path = template_directory / "settings.json"
  extensions_template_path = template_directory / "extensions.json"
  for required_path in (
    python,
    ruff,
    clang_format,
    ruff_configuration,
    settings_template_path,
    extensions_template_path,
  ):
    if not required_path.exists():
      raise ValueError(f"required Tea tool is missing: {required_path}")

  replacements = {
    "@TEA_ENV_PREFIX@": str(environment),
    "@TEA_ENV_PARENT@": str(environment.parent),
    "@TEA_FRAMEWORK_DIR@": str(framework),
  }

  settings_path = workspace / ".vscode/settings.json"
  settings = read_json_object(settings_path)
  settings.pop("clang-format.executable", None)
  generated_settings = materialize_template(read_json_object(settings_template_path), replacements)
  merge_settings(settings, generated_settings)

  settings_changed = write_json_if_changed(settings_path, settings)

  extensions_path = workspace / ".vscode/extensions.json"
  extensions = read_json_object(extensions_path)
  recommendations = extensions.get("recommendations")
  if isinstance(recommendations, list):
    extensions["recommendations"] = [
      recommendation for recommendation in recommendations if recommendation != "xaver.clang-format"
    ]
  generated_extensions = materialize_template(read_json_object(extensions_template_path), replacements)
  extensions["recommendations"] = append_unique(
    extensions.get("recommendations"),
    generated_extensions.get("recommendations", []),
  )
  extensions_changed = write_json_if_changed(extensions_path, extensions)
  return settings_changed or extensions_changed


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--workspace", required=True, type=Path)
  parser.add_argument("--framework", required=True, type=Path)
  parser.add_argument("--environment", required=True, type=Path)
  parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)
  arguments = parser.parse_args()

  if not arguments.force and not vscode_is_available():
    print("tea: VS Code not detected; skipping workspace editor configuration")
    return 0

  try:
    changed = configure_workspace(
      arguments.workspace.resolve(),
      arguments.framework.resolve(),
      arguments.environment.resolve(),
    )
  except (TypeError, ValueError) as error:
    print(f"tea: warning: {error}", file=sys.stderr)
    return 0

  if changed:
    print(f"tea: configured VS Code workspace at {arguments.workspace / '.vscode'}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
