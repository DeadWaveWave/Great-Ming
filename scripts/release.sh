#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SKILL_DIR="$ROOT/skills/great-ming"
ARTIFACT_ZIP="$ROOT/dist/great-ming.zip"

die() {
  echo "Error: $*" >&2
  exit 1
}

have() {
  command -v "$1" >/dev/null 2>&1
}

require_cmd() {
  have "$1" || die "Missing required command: $1"
}

usage() {
  cat <<'EOF'
Usage:
  ./scripts/release.sh [command]

Commands:
  build
    Build dist/great-ming.zip from skills/great-ming/ (default).

  bump <version>
    Replace version strings in README.md, README-en.md, LICENSE, then build.

  publish <version> [--yes]
    bump + build + git commit/tag/push + gh release create (uploads dist/great-ming.zip).

Examples:
  ./scripts/release.sh build
  ./scripts/release.sh bump 3.1.5
  ./scripts/release.sh publish 3.1.5
EOF
}

current_version() {
  require_cmd python3
  python3 - "$ROOT" <<'PY'
from __future__ import annotations

import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
text = (root / "README.md").read_text(encoding="utf-8")
match = re.search(r"永乐_(\\d+\\.\\d+\\.\\d+)", text)
if not match:
    raise SystemExit("Error: cannot find current version in README.md (pattern: 永乐_X.Y.Z)")
print(match.group(1))
PY
}

bump_version() {
  local new_version="${1:?missing version}"
  require_cmd python3
  python3 - "$ROOT" "$new_version" <<'PY'
from __future__ import annotations

import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
new_version = sys.argv[2]

targets = [
    ("README.md", re.compile(r"永乐_(\\d+\\.\\d+\\.\\d+)")),
    ("README-en.md", re.compile(r"Yongle_(\\d+\\.\\d+\\.\\d+)")),
    ("LICENSE", re.compile(r"Version (\\d+\\.\\d+\\.\\d+)")),
]

found_versions: dict[str, str] = {}
for filename, pattern in targets:
    path = root / filename
    text = path.read_text(encoding="utf-8")
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"Error: cannot find version in {filename}")
    found_versions[filename] = match.group(1)

unique = sorted(set(found_versions.values()))
if len(unique) != 1:
    details = ", ".join(f"{k}={v}" for k, v in found_versions.items())
    raise SystemExit(f"Error: version mismatch across files: {details}")

old_version = unique[0]
if old_version == new_version:
    print(f"Version unchanged: {old_version}")
    raise SystemExit(0)

for filename, _pattern in targets:
    path = root / filename
    text = path.read_text(encoding="utf-8")
    updated = text.replace(old_version, new_version)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        print(f"Updated {filename}: {old_version} -> {new_version}")
PY
}

build_skill() {
  require_cmd zip
  require_cmd unzip
  [[ -d "$SKILL_DIR" ]] || die "Missing skill dir: $SKILL_DIR"
  [[ -f "$SKILL_DIR/SKILL.md" ]] || die "Missing SKILL.md: $SKILL_DIR/SKILL.md"

  mkdir -p "$ROOT/dist"
  rm -f "$ARTIFACT_ZIP"

  (cd "$ROOT/skills" && zip -r "$ARTIFACT_ZIP" "great-ming" \
    -x '*/.DS_Store' \
    -x '*/__pycache__/*' \
    -x '*/.pytest_cache/*' \
    -x '*.pyc' \
    -x '*.pyo' \
    >/dev/null)

  unzip -l "$ARTIFACT_ZIP" | grep -qE 'great-ming/SKILL\.md$' || die "Built archive is missing great-ming/SKILL.md"

  echo "Built: $ARTIFACT_ZIP"
  if have shasum; then
    echo "SHA256: $(shasum -a 256 "$ARTIFACT_ZIP" | awk '{print $1}')"
  elif have sha256sum; then
    echo "SHA256: $(sha256sum "$ARTIFACT_ZIP" | awk '{print $1}')"
  fi
}

require_clean_git() {
  require_cmd git
  git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not a git repository: $ROOT"
  [[ -z "$(git -C "$ROOT" status --porcelain)" ]] || die "Working tree is not clean; commit/stash first."
}

publish_release() {
  local version="${1:?missing version}"
  shift || true

  local assume_yes="0"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --yes) assume_yes="1" ;;
      -h|--help) usage; exit 0 ;;
      *) die "Unknown option: $1" ;;
    esac
    shift
  done

  require_cmd gh
  require_clean_git

  local old
  old="$(current_version)"
  [[ "$version" != "$old" ]] || die "Version unchanged ($version); choose a new version."

  bump_version "$version"
  build_skill

  local tag="v$version"
  if git -C "$ROOT" rev-parse "$tag" >/dev/null 2>&1; then
    die "Tag already exists: $tag"
  fi
  git -C "$ROOT" remote get-url origin >/dev/null 2>&1 || die "Missing git remote: origin"

  git -C "$ROOT" add README.md README-en.md LICENSE dist/great-ming.zip
  git -C "$ROOT" commit -m "chore(release): $tag"
  git -C "$ROOT" tag -a "$tag" -m "$tag"

  if [[ "$assume_yes" != "1" ]]; then
    read -r -p "Push to origin and create GitHub release $tag? [y/N] " confirm
    [[ "$confirm" == "y" || "$confirm" == "Y" ]] || die "Aborted."
  fi

  git -C "$ROOT" push origin HEAD
  git -C "$ROOT" push origin "$tag"
  gh release create "$tag" "$ARTIFACT_ZIP" --title "$tag" --generate-notes
}

main() {
  local cmd="${1:-build}"
  shift || true

  case "$cmd" in
    build)
      build_skill
      ;;
    bump)
      [[ $# -eq 1 ]] || die "bump requires exactly 1 argument: <version>"
      bump_version "$1"
      build_skill
      ;;
    publish)
      [[ $# -ge 1 ]] || die "publish requires: <version> [--yes]"
      publish_release "$@"
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      usage
      die "Unknown command: $cmd"
      ;;
  esac
}

main "$@"
