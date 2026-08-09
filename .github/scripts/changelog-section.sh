#!/usr/bin/env bash
# Print the Keep a Changelog body for a version heading matching TAG.
# Git tags use a leading v (v1.2.3); changelog headings omit it ([1.2.3]).
# Accepts TAG with or without the v prefix. Headings: "## [1.2.3]" or
# "## [1.2.3] - 2026-07-25".
set -euo pipefail

tag=${1:?usage: changelog-section.sh TAG [CHANGELOG.md]}
file=${2:-CHANGELOG.md}
version=${tag#v}

if [[ ! -f $file ]]; then
  echo "changelog not found: $file" >&2
  exit 1
fi

awk -v version="$version" -v tag="$tag" '
  BEGIN { heading = "## [" version "]" }
  $0 == heading || index($0, heading " ") == 1 {
    found = 1
    next
  }
  found && /^## / { exit }
  found { print }
  END {
    if (!found) {
      printf "no changelog section for %s (looked for %s)\n", tag, heading > "/dev/stderr"
      exit 1
    }
  }
' "$file"
