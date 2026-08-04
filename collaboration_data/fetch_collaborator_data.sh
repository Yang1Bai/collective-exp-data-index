#!/usr/bin/env bash
set -euo pipefail

DESTINATION="${1:-collaborator_workspace}"
REPOSITORY="Yang1Bai/collective-exp-data-index"
TAG="collaborator-data-v2026.08.04"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v gh >/dev/null 2>&1 || {
  echo "GitHub CLI (gh) is required." >&2
  exit 1
}

gh auth status >/dev/null
mkdir -p "$DESTINATION"
gh release download "$TAG" --repo "$REPOSITORY" --dir "$DESTINATION" --clobber

(
  cd "$DESTINATION"
  sha256sum --check "$SCRIPT_DIR/RELEASE_ASSET_CHECKSUMS.sha256"
  for archive in *.zip; do
    [ -e "$archive" ] || continue
    rm -rf "${archive%.zip}"
    unzip -q "$archive" -d "${archive%.zip}"
  done
)

echo "Collaborator datasets downloaded, verified, and extracted to $DESTINATION"
